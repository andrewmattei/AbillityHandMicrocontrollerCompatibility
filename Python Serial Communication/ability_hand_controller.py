import struct
from serial.tools import list_ports
import serial
import threading
import queue
import time
import numpy as np

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
        self.debug = debug
        self.hand_side = side

        self.send_queue = queue.Queue(maxsize=2)
        self.serial_thread = threading.Thread(
            target=self._serial_worker,
            daemon=True)
        self.serial_thread.start()
        print(f"Serial worker thread started for {self.hand_side} hand on port {self.port}")


    def send_joint_positions(self, joint_positions):
        """
        Update positions and queue them for sending to hardware.

        Args:
            joint_positions: An arraay of 6 floats representing the joint positions to send to the hardware
        """
        if len(joint_positions) != 6:
            raise ValueError(f"Joint positions must be an array of 6 floats; got {len(joint_positions)} elements")
        
        
        if self.send_queue is not None:
            if joint_positions is not None:
                mapped_positions = np.zeros(6, dtype=np.float32)

                for i in range(len(mapped_positions) - 1):
                    mapped_positions[i] = np.clip(mapped_positions[i], 0.0, 100.0) # Clip to valid range

                mapped_positions[-1] = np.clip(mapped_positions[-1], -100.0, 0.0) # Clip to valid range

                try:
                    self.send_queue.put_nowait(mapped_positions)
                except queue.Full:
                    try:
                        _ = self.send_queue.get_nowait()
                    except queue.Empty:
                        pass
                    try:
                        self.send_queue.put_nowait(mapped_positions)
                    except queue.Full:
                        if self.debug:
                            print(f"[{self.hand_side}] send queue full; dropping packet")

    
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
                    packed_data = struct.pack('<6f', *data_to_send)
                    self.client.write(packed_data)
                    if self.debug:
                        pos_str = ", ".join([f"{pos:.1f}" for pos in data_to_send])
                        print(f"[{self.hand_side}] HW_SEND: [{pos_str}]")
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