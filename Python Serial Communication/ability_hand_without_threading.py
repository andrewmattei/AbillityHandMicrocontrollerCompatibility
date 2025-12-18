import serial
import numpy as np
import struct
import time

"""
    This is a demo script that shows you how to use serial communication to package and send finger joint data to a microcontroller.
    *** Note: The information sent to the Teensy for Ability Hand movement is an array of 6 float32 values.
        - The arr indices 0-4 can range in values: [0,100]
        - The arr index 5 can range in values: [-100,0]
"""

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
            - Example: "/dev/tty.usbserial-1420"
            - To find the port, use this command in terminal: "ls /dev/tty.*"
    """
    if port is not None:
        print("starting program on ", port)
        try: 
            ser = serial.Serial(port=port, baudrate=serial_baudrate, timeout=serial_timeout, 
            write_timeout=write_timeout) # Open specified serial port 
            print("Serial port opened successfully")
        except Exception as e:
            print(f"Failed to open serial port: {e}")
            return
        
        arr = np.zeros(6, dtype=np.float32) # array to hold finger joint values
        start_time = time.time() # keep track of time to run demo for 25 seconds

        if ser is not None:
            while time.time() < start_time + 25:
                for i in range(5): # loop through first 5 indices of arr
                    for j in range(0,100,2): # increment angles from 0 to 100 by 2 for current finger
                        arr[i] = j
                        print(arr)
                        try:
                            packed_data = struct.pack("<6f", *arr) # pack array into bytes
                            ser.write(packed_data) # write packed data to serial port
                            time.sleep(0.02)
                        except Exception as e:
                            print("Failed to write to serial port")
                            return

                    for j in range(100,0,-2): # decrement angles from 100 to 0 by 2 for current finger
                        arr[i] = j
                        print(arr)
                        try:
                            packed_data = struct.pack("<6f", *arr) # pack array into bytes
                            ser.write(packed_data) # write packed data to serial port
                            time.sleep(0.02)
                        except Exception as e:
                            print("Failed to write to serial port")
                            return

        print("Demo Complete! Serial port closed successfully")
        ser.close() # Close serial port when done

    else:
        print("Please provide a valid serial port.")

if __name__ == "__main__":
    main("/dev/tty.usbmodem175796501")   # Change this to your serial port


        