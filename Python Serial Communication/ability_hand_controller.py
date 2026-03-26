import struct
import threading
import queue
import time

import numpy as np
import serial
from serial.tools import list_ports


CMD_HEADER = 0xA5
TELEMETRY_HEADER = 0x5A
CMD_PACKET_FORMAT = "<BB6fB"
TELEMETRY_PACKET_FORMAT = "<BB6f6f30fB"
CMD_PACKET_SIZE = struct.calcsize(CMD_PACKET_FORMAT)
TELEMETRY_PACKET_SIZE = struct.calcsize(TELEMETRY_PACKET_FORMAT)

CONTROL_MODE_TO_ID = {
    "position": 0,
    "velocity": 1,
    "torque": 2,
}

ID_TO_CONTROL_MODE = {v: k for k, v in CONTROL_MODE_TO_ID.items()}


def _compute_checksum(payload_bytes):
    return (-sum(payload_bytes)) & 0xFF


def _build_command_packet(mode_id, command_values):
    packet_wo_checksum = struct.pack("<BB6f", CMD_HEADER, mode_id, *command_values)
    checksum = _compute_checksum(packet_wo_checksum)
    return packet_wo_checksum + bytes([checksum])


def _parse_telemetry_packet(raw_packet):
    unpacked = struct.unpack(TELEMETRY_PACKET_FORMAT, raw_packet)
    header = unpacked[0]
    mode_id = unpacked[1]
    checksum = unpacked[-1]

    if header != TELEMETRY_HEADER:
        raise ValueError("Unexpected telemetry header")

    expected_checksum = _compute_checksum(raw_packet[:-1])
    if checksum != expected_checksum:
        raise ValueError("Telemetry checksum mismatch")

    pos = np.array(unpacked[2:8], dtype=np.float32)
    vel = np.array(unpacked[8:14], dtype=np.float32)
    forces = np.array(unpacked[14:44], dtype=np.float32)

    return {
        "mode": ID_TO_CONTROL_MODE.get(mode_id, "unknown"),
        "position": pos,
        "velocity": vel,
        "forces": forces,
        "timestamp": time.time(),
    }

class AbilityHandController:
    """
    Controller for the Ability Hand hardware using serial communication and threading to seamlessly integrate 
    into any Python-based control system for the Ability Hand hardware. The controller uses a separate thread for 
    serial communication, ensuring that the main control loop remains responsive and efficient.
    """

    def __init__(self, side="left", port=None, baud=460800, timeout=1, debug=False):
        """
        Initialize Ability Hand controller.
        
        Args:
            side: Side of the hand to control (usuallly name "left" or "right")
            port: Serial port to connect to the Ability Hand hardware
            baud: Serial baud rate for communication with the Ability Hand hardware
            timeout: Serial timeout for communication with the Ability Hand hardware
            debug: Enable debug output
        """
        self.debug = debug
        if not _is_valid_serial_port(port):
            available = _list_serial_ports()
            raise ValueError(f"Serial port {port!r} not found. Available ports: {available if available else 'none'}")
        
        if self.debug:
            print(f"Initializing {side} hand controller on port {port} at {baud} baud")
            
        self.client = None
        self.port = port
        self.serial_thread = None
        self.send_queue = None
        self._serial_stop_event = threading.Event()
        self._serial_baudrate = baud
        self._serial_timeout = timeout
        self.hand_side = side
        self.data = {
            "mode": None,
            "position": None,
            "velocity": None,
            "forces": None,
            "timestamp": None,
        }
        self._feedback_lock = threading.Lock()

        self.send_queue = queue.Queue(maxsize=2)
        self.serial_thread = threading.Thread(
            target=self._serial_worker,
            daemon=True)
        self.serial_thread.start()
        print(f"Serial worker thread started for {self.hand_side} hand on port {self.port}")


    def write(self, joint_values, control_mode="position"):
        """
        Queue a control command for the hand.

        Args:
            joint_values: Array-like of 6 floats representing desired command values.
            control_mode: One of "position", "velocity", or "torque".
        """
        self.send_joint_command(joint_values, control_mode=control_mode)

    def read(self):
        """
        Return the latest telemetry snapshot from the hand.

        Returns:
            Dictionary with keys: mode, position, velocity, forces, timestamp.
            If telemetry has not been received yet, values are None.
        """
        with self._feedback_lock:
            out = {
                "mode": self.data["mode"],
                "position": None,
                "velocity": None,
                "forces": None,
                "timestamp": self.data["timestamp"],
            }
            if self.data["position"] is not None:
                out["position"] = self.data["position"].copy()
            if self.data["velocity"] is not None:
                out["velocity"] = self.data["velocity"].copy()
            if self.data["forces"] is not None:
                out["forces"] = self.data["forces"].copy()
            return out

    def send_joint_positions(self, joint_positions):
        self.write(joint_positions, control_mode="position")

    def send_joint_command(self, joint_values, control_mode="position"):
        """
        Queue a command and control mode for the hand.

        Args:
            joint_values: Array of 6 floats representing desired command values.
            control_mode: One of "position", "velocity", or "torque".
        """
        mode_key = str(control_mode).strip().lower()
        if mode_key not in CONTROL_MODE_TO_ID:
            raise ValueError("control_mode must be one of: position, velocity, torque")

        if len(joint_values) != 6:
            raise ValueError(f"Joint command must be an array of 6 floats; got {len(joint_values)} elements")

        mapped_values = np.array(joint_values, dtype=np.float32)
        if not np.all(np.isfinite(mapped_values)):
            raise ValueError("Joint command values must be finite floats")

        if mode_key == "position":
            for i in range(5):
                mapped_values[i] = np.clip(mapped_values[i], 0.0, 100.0)
            mapped_values[5] = np.clip(mapped_values[5], -100.0, 0.0)

        item = (CONTROL_MODE_TO_ID[mode_key], mapped_values)
        if self.send_queue is not None:
            try:
                self.send_queue.put_nowait(item)
            except queue.Full:
                try:
                    _ = self.send_queue.get_nowait()
                except queue.Empty:
                    pass
                try:
                    self.send_queue.put_nowait(item)
                except queue.Full:
                    if self.debug:
                        print(f"[{self.hand_side}] send queue full; dropping packet")

    def get_latest_feedback(self):
        return self.read()

    def _read_feedback_packet(self):
        if self.client is None:
            return None

        start = self.client.read(1)
        if len(start) != 1:
            return None

        while start and start[0] != TELEMETRY_HEADER:
            start = self.client.read(1)
            if len(start) != 1:
                return None

        remainder = self.client.read(TELEMETRY_PACKET_SIZE - 1)
        if len(remainder) != TELEMETRY_PACKET_SIZE - 1:
            return None

        packet = bytes([start[0]]) + remainder
        return _parse_telemetry_packet(packet)

    
    def _serial_worker(self):
        """
        This function runs in a separate thread.
        It handles all serial communication to avoid blocking the main loop.
        """

        backoff = 0.1
        max_backoff = 5.0

        while not self._serial_stop_event.is_set():
            data_to_send = None
            try:
                try:
                    data_to_send = self.send_queue.get(block=True, timeout=0.05)
                    while True:
                        try:
                            data_to_send = self.send_queue.get_nowait()
                        except queue.Empty:
                            break
                except queue.Empty:
                    data_to_send = None

                if data_to_send is None:
                    continue

                if self.client is None:
                    if self.debug:
                        print(f"[{self.hand_side}] Attempting serial connection to {self.port}...")
                    try:
                        self.client = serial.Serial(
                            port=self.port,
                            baudrate=self._serial_baudrate,
                            timeout=self._serial_timeout,
                            write_timeout=0.05,
                        )
                        if self.debug:
                            print(f"[{self.hand_side}] Hand hardware CONNECTED on {self.port}")
                        backoff = 0.1
                    except serial.SerialException as e:
                        if self.debug:
                            print(f"[{self.hand_side}] Serial open failed: {e}; retrying in {backoff:.1f}s")
                        time.sleep(backoff)
                        backoff = min(max_backoff, backoff * 2)
                        continue
                try:
                    mode_id, command_values = data_to_send
                    packed_data = _build_command_packet(mode_id, command_values)
                    self.client.write(packed_data)
                    if self.debug:
                        cmd_str = ", ".join([f"{pos:.2f}" for pos in command_values])
                        mode_name = ID_TO_CONTROL_MODE.get(mode_id, f"id:{mode_id}")
                        print(f"[{self.hand_side}] HW_SEND ({mode_name}): [{cmd_str}]")

                    feedback = self._read_feedback_packet()
                    if feedback is not None:
                        with self._feedback_lock:
                            self.data["mode"] = feedback["mode"]
                            self.data["position"] = feedback["position"]
                            self.data["velocity"] = feedback["velocity"]
                            self.data["forces"] = feedback["forces"]
                            self.data["timestamp"] = feedback["timestamp"]

                        if self.debug:
                            pos0 = feedback["position"][0]
                            vel0 = feedback["velocity"][0]
                            force0 = feedback["forces"][0]
                            print(
                                f"[{self.hand_side}] HW_RECV mode={feedback['mode']} "
                                f"pos0={pos0:.2f} vel0={vel0:.2f} force0={force0:.2f}"
                            )
                    backoff = 0.1
                except serial.SerialTimeoutException as e:
                    if self.debug:
                        print(f"[{self.hand_side}] Write timed out (drop packet): {e}")
                    continue
                except serial.SerialException as e:
                    print(f"[{self.hand_side}] Serial exception during write: {e}")
                    try:
                        self.client.close()
                    except Exception:
                        pass
                    self.client = None
                    time.sleep(backoff)
                    backoff = min(max_backoff, backoff * 2)
                    continue

            except Exception as e:
                if self.debug:
                    print(f"[{self.hand_side}] Unhandled error in serial thread: {e}")
                time.sleep(0.05)
        try:
            if self.client:
                self.client.close()
        except Exception:
            pass
        self.client = None
        if self.debug:
            print(f"[{self.hand_side}] Serial thread stopped.")

    def close(self):
        """Close the Ability Hand hardware client connection if it exists."""
        if self.serial_thread is not None:
            self._serial_stop_event.set()
            self.serial_thread.join(timeout=2)
            if self.serial_thread.is_alive():
                print(f"Warning: {self.hand_side} serial thread did not shut down cleanly.")

        # Close the client if open
        if self.client is not None:
            try:
                self.client.close()
            except Exception:
                pass
        self.client = None



# Helper functions for serial port management

def _list_serial_ports():
    """Return a list of available serial port device names."""
    return [p.device for p in list_ports.comports()]


def _is_valid_serial_port(port):
    """Return True if port is present in the system's serial ports."""
    if not port:
        return False
    return port in _list_serial_ports()