import serial
from serial.tools import list_ports
import numpy as np
import struct
import time


"""
    This is a demo script that shows you how to use serial communication to package and send finger joint data to a microcontroller.
    *** Note: The information sent to the Teensy for Ability Hand movement is an array of 6 float32 values.
        - The arr indices 0-4 can range in values: [0,100]
        - The arr index 5 can range in values: [-100,0]
"""


def _list_serial_ports():
    """Return a list of available serial port device names."""
    return [p.device for p in list_ports.comports()]

def _is_valid_serial_port(port):
    """Return True if port is present in the system's serial ports."""
    if not port:
        return False
    return port in _list_serial_ports()


serial_timeout = 1
write_timeout = 0.05
serial_baudrate = 460800
ser = None

CMD_HEADER = 0xA5
TELEMETRY_HEADER = 0x5A


def _compute_checksum(payload_bytes):
    return (-sum(payload_bytes)) & 0xFF


def build_command_packet(control_mode, values):
    mode = control_mode.strip().lower()
    mode_map = {"position": 0, "velocity": 1, "torque": 2}
    if mode not in mode_map:
        raise ValueError("control_mode must be one of: position, velocity, torque")
    if len(values) != 6:
        raise ValueError("values must contain 6 floats")

    packet_wo_checksum = struct.pack("<BB6f", CMD_HEADER, mode_map[mode], *values)
    checksum = _compute_checksum(packet_wo_checksum)
    return packet_wo_checksum + bytes([checksum])


def read_telemetry_packet(serial_client):
    header = serial_client.read(1)
    if len(header) != 1:
        return None

    while header and header[0] != TELEMETRY_HEADER:
        header = serial_client.read(1)
        if len(header) != 1:
            return None

    payload_size = struct.calcsize("<B6f6f30fB") - 1
    payload = serial_client.read(payload_size)
    if len(payload) != payload_size:
        return None

    packet = bytes([header[0]]) + payload
    expected_checksum = _compute_checksum(packet[:-1])
    if packet[-1] != expected_checksum:
        print("Bad telemetry checksum")
        return None

    unpacked = struct.unpack("<BB6f6f30fB", packet)
    mode_id = unpacked[1]
    mode_name = {0: "position", 1: "velocity", 2: "torque"}.get(mode_id, "unknown")
    position = np.array(unpacked[2:8], dtype=np.float32)
    velocity = np.array(unpacked[8:14], dtype=np.float32)
    forces = np.array(unpacked[14:44], dtype=np.float32)

    return {
        "mode": mode_name,
        "position": position,
        "velocity": velocity,
        "forces": forces,
    }

def main(port=None, control_mode="position"):
    """
    This function opens a serial port and sends an array of 6 float32 values to the microcontroller.
    The array is sent in a loop for 25 seconds.

    Args:
        port (str): The serial port to open. 
    """

    # if port is not None:
    if True:
        print("starting program on ", port)
        # Safety check: ensure the specified serial port is present on the system
        if not _is_valid_serial_port(port):
            available = _list_serial_ports()
            print(f"Error: Serial port {port!r} not found. Available ports: {available if available else 'none'}")
            return
        try: 
            ser = serial.Serial(port=port, baudrate=serial_baudrate, timeout=serial_timeout, 
            write_timeout=write_timeout) 
            print("Serial port opened successfully")
        except Exception as e:
            print(f"Failed to open serial port: {e}")
            return
        
        arr = np.zeros(6, dtype=np.float32) 
        start_time = time.time() 

        if ser is not None:
            while time.time() < start_time + 25:
                for i in range(5): 
                    for j in range(0,100,2):
                        arr[i] = j
                        print(arr)
                        try:
                            packed_data = build_command_packet(control_mode, arr)
                            ser.write(packed_data)
                            feedback = read_telemetry_packet(ser)
                            if feedback is not None:
                                print(
                                    f"Feedback mode={feedback['mode']} "
                                    f"pos0={feedback['position'][0]:.2f} "
                                    f"vel0={feedback['velocity'][0]:.2f} "
                                    f"force0={feedback['forces'][0]:.2f}"
                                )
                            time.sleep(0.02)
                        except Exception as e:
                            print(f"Failed to send packet: {e}")
                            return

                    for j in range(100,0,-2):
                        arr[i] = j
                        print(arr)
                        try:
                            packed_data = build_command_packet(control_mode, arr)
                            ser.write(packed_data)
                            feedback = read_telemetry_packet(ser)
                            if feedback is not None:
                                print(
                                    f"Feedback mode={feedback['mode']} "
                                    f"pos0={feedback['position'][0]:.2f} "
                                    f"vel0={feedback['velocity'][0]:.2f} "
                                    f"force0={feedback['forces'][0]:.2f}"
                                )
                            time.sleep(0.02)
                        except Exception as e:
                            print(f"Failed to send packet: {e}")
                            return

        print("Demo Complete! Serial port closed successfully")
        ser.close()

    else:
        print("Please provide a valid serial port.")

if __name__ == "__main__":
    main("/dev/tty.usbmodem175796501", control_mode="position")   # Change this to your serial port/control mode



        