from ability_hand_controller import AbilityHandController
import numpy as np
import time

"""
This script demonstrates how to use the AbilityHandController class to control the fingers of an Ability Hand
by sending joint positions to the hand. The script extends and retracts each finger in sequence for 25 seconds."""

if __name__ == "__main__":
    hand = AbilityHandController(port="/dev/tty.usbmodem")

    joint_positions = np.zeros(6, dtype=np.float32)  # Example joint positions
    start_time = time.time()

    while time.time() < start_time + 25:
        for i in range(5): 
            for j in range(0,100,2):
                joint_positions[i] = j
                hand.send_joint_positions(joint_positions)
                time.sleep(0.02)

            print(f"finger {i + 1} extended, now retracting")
            for j in range(100,0,-2):
                joint_positions[i] = j
                hand.send_joint_positions(joint_positions)
                time.sleep(0.02)
            print(f"finger {i + 1} retracted, now extending finger {i + 2}")

    hand.close()
    print("Client closed, demo completed.")
    