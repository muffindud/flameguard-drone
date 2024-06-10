import os
import cv2
import time
import threading
from djitellopy import Tello
from djitellopy.tello import TelloException
import numpy as np

from pika import BlockingConnection, ConnectionParameters
from dotenv import dotenv_values
from json import dumps
import http.server

config = dotenv_values()
exchange = "drone"      # exchange name
send_to = "receive"     # routing key
receive_from = "send"   # routing key

connection = BlockingConnection(ConnectionParameters(host=config["RABBITMQ_HOST"]))
channel = connection.channel()
channel.exchange_declare(exchange=exchange, exchange_type='direct')
channel.queue_declare(queue="", exclusive=True)
result = channel.queue_declare(queue="", exclusive=True)
callback_queue = result.method.queue
channel.queue_bind(exchange=exchange, queue=callback_queue, routing_key=receive_from)

# Declare a threading Event to signal readiness of video streaming
stream_ready = threading.Event()
frame = None
drone = Tello()
# drone.connect()
state = "idle"


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

def flight_routine(drone: Tello) -> None:
    print("waiting for event to signal video stream readiness")
    state = "patrol"

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
    take_picture(frame)
    drone.move_back(20)
    print("move down\n")
    drone.move_down(20)
    print("rotate CW\n")
    drone.rotate_clockwise(180)
    print("rotate CCW\n")
    take_picture(frame)
    drone.rotate_counter_clockwise(180)
    print("land")
    drone.land()

    state = "idle"

def stream_video(drone: Tello) -> None:
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

def patrol():
    try:
        # Initialize the drone, connect to it, and turn its video stream on.
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
    except TelloException:
        print("An error occurred in the patrol function")

def status() -> dict:
    try:
        battery = drone.get_battery()
    except Exception as e:
        battery = None
        print("Error getting battery status:", e)

    try:
        height = drone.get_height()
    except Exception as e:
        height = None
        print("Error getting height status:", e)

    status = {
        "battery": drone.get_battery(),
        "height": drone.get_height(),
        "state": state
    }

    return status


def callback(ch, method, properties, body):
    body = body.decode()
    print(f"Received: {body}")

    if body == "patrol" and state == "idle":
        print("Starting patrol")
        # patrol()
        files = sorted(os.listdir("./"), key=lambda x: os.path.getctime(f"./{x}"))

        picture_path = f"http://{config["IP_ADDRESS"]}:8000/{files[-1]}"

        channel.basic_publish(exchange=exchange, routing_key=send_to, body="picture " + picture_path)

    elif body == "patrol" and state == "patrol":
        print("Drone is already patrolling")
    elif body == "status":
        channel.basic_publish(exchange=exchange, routing_key=send_to, body="status " + dumps(status()))


def start_http_server():
    web_dir = os.path.join(os.path.dirname(__file__), 'pictures')
    os.chdir(web_dir)
    Handler = http.server.SimpleHTTPRequestHandler
    httpd = http.server.HTTPServer(('0.0.0.0', 8000), Handler)
    httpd.serve_forever()


if __name__ == "__main__":
    sv = threading.Thread(target=start_http_server)
    sv.daemon = True
    sv.start()

    channel.basic_consume(queue=callback_queue, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()
