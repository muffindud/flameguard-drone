"""
Author: Jacob Pitsenberger
Program: take_pictures.py
Project: Taking Pictures with Tello Drones using Python and OpenCV
Date: 12/28/2023
Purpose: This module demonstrates using openCV with the TelloEDU mini drone to stream video from its camera
         and save the frames as a .png file when the 'p' key is pressed.
"""

import os
import cv2
import time
from time import sleep
from djitellopy import Tello
import numpy as np


def take_picture(frame: np.ndarray) -> None:
    """Get the current frame, then check if the pictures directory exists. If not, create it.
    After this, use imwrite to save the current frame to the images directory with the file name being
    the time the picture was taken.

    Args:
        frame (np.ndarray): The current frame from the drone's camera stream.
    """
    try:
        if not os.path.exists("pictures"):
            os.mkdir("pictures")
        file_name = f"pictures/{time.time()}.png"
        cv2.imwrite(file_name, frame)
        print("Image saved:", file_name)
        time.sleep(0.3)
    except Exception as pic_exception:
        print('An exception occurred in the take_picture function:', pic_exception)


def run_tello_video(drone: Tello) -> None:
    """Continuously displays the video stream from the Tello drone.

    Args:
        drone (Tello): The Tello drone object.
    """
    try:
        while True:
            # Capture a frame from the Tello video stream
            frame = drone.get_frame_read().frame

            # Display the captured frame in a window
            cv2.imshow("Frame", frame)

            # Set up the waitKey for updating the video stream
            key = cv2.waitKey(1) & 0xFF  # Apply a bitwise AND operation with 0xFF to get ASCII value of any key pressed

            # Check for keyboard interactions and perform respective functionalities.
            if key == ord('q'):
                break
            elif key == ord('p'):
                take_picture(frame)
            elif key == ord('d'):
                drone.land()
            elif key == ord('u'):
                # Capture a frame from the Tello video stream
                frame = drone.get_frame_read().frame
                drone.takeoff()
                sleep(2)
                drone.move_forward(100)
                # Wait for the drone to stabilize after moving forward
                sleep(2)
                # Update the frame after the movement
                frame = drone.get_frame_read().frame
                take_picture(frame)
                drone.move_back(100)
                sleep(2)
                drone.land()
            elif key == ord('w'):
                drone.takeoff()

    except Exception as stream_exception:
        print('An exception occurred in the run_tello_video function:', stream_exception)
    finally:
        cv2.destroyAllWindows()


def main():
    """Main function to connect to the Tello drone, start the video stream, and handle user input."""

    # Initialize Drone Object.
    drone = Tello()
    try:
        # Establish connection with the drone.
        drone.connect()
        # Start the drone's camera stream.
        drone.streamon()
        # Call the function to stream video from the drone.
        run_tello_video(drone)

    except Exception as main_exception:
        print("An error in the main function:", main_exception)
    finally:
        # reboot the drone such that the program can be easily ran again.
        drone.reboot()


if __name__ == "__main__":
    main()
