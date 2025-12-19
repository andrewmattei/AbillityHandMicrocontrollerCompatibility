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
serial_baudrate = 46800
ser = None

def main(port=None):
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
                            packed_data = struct.pack("<6f", *arr)
                            ser.write(packed_data)
                            time.sleep(0.02)
                        except Exception as e:
                            print("Failed to write to serial port")
                            return

                    for j in range(100,0,-2):
                        arr[i] = j
                        print(arr)
                        try:
                            packed_data = struct.pack("<6f", *arr)
                            ser.write(packed_data)
                            time.sleep(0.02)
                        except Exception as e:
                            print("Failed to write to serial port")
                            return

        print("Demo Complete! Serial port closed successfully")
        ser.close()

    else:
        print("Please provide a valid serial port.")

if __name__ == "__main__":
    main("/dev/tty.usbmodem175796501")   # Change this to your serial port



        