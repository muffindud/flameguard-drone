import os
import cv2
import time
import threading
from djitellopy import Tello
import numpy as np

# Declare a threading Event to signal readiness of video streaming
stream_ready = threading.Event()

def take_picture(frame: np.ndarray) -> None:
    try:
        if not os.path.exists("pictures"):
            os.mkdir("pictures")
        file_name = f"pictures/{time.time()}.png"
        cv2.imwrite(file_name, frame)
        print("Image saved:", file_name)
        time.sleep(0.3)
    except Exception as pic_exception:
        print('An exception occurred in the take_picture function', pic_exception)

def flight_routine(drone):
    print("waiting for event to signal video stream readiness")

    # Wait for the event signaling video stream readiness
    stream_ready.wait()

    print("event signaled for video stream readiness")

    # Send the takeoff command, movement commands, and lastly, the land command
    print("takeoff\n")
    drone.takeoff()
    print("move forward\n")
    drone.move_forward(20)
    print("move up\n")
    drone.move_up(20)
    print("move back\n")
    drone.move_back(20)
    print("move down\n")
    drone.move_down(20)
    print("rotate CW\n")
    drone.rotate_clockwise(180)
    print("rotate CCW\n")
    drone.rotate_counter_clockwise(180)
    print("land")
    drone.land()

def stream_video(drone):
    while True:
        frame = drone.get_frame_read().frame
        # Check if frame reading was successful
        cv2.imshow('tello stream', frame)

        # Check if streaming readiness hasn't been signaled yet
        if not stream_ready.is_set():
            # Signal that video streaming is ready
            stream_ready.set()
            print("Event Signal Set: Stream is live.")

        # Check for key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('p'):
            take_picture(frame)

    cv2.destroyAllWindows()

def main():
    # Initialize the drone, connect to it, and turn its video stream on.
    drone = Tello()
    drone.connect()
    drone.streamon()
    print("drone connected and stream on. Starting video stream thread.\n")

    # Create and start the streaming thread
    stream_thread = threading.Thread(target=stream_video, args=(drone,))

    # Set thread as a daemon thread to have it run in the background.
    # This allows our program to exit even if this streaming thread is still running after calling drone.reboot()
    # Also, this prevents errors in our video stream function from crashing our entire program if they occur.
    stream_thread.daemon = True

    # Start the thread
    stream_thread.start()

    # Execute the flight routine
    flight_routine(drone)

    print("Flight routine ended. Rebooting drone now...")

    # Reboot the drone at the end
    drone.reboot()

if __name__ == "__main__":
    # Run the main function if this script is executed
    main()
