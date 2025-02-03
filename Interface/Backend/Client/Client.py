import threading
import websocket
import logging
import json
import base64
import os
import time
from sendStatus import get_status, update_status
from SimulateCalibration.Simulate import Calibration
class WebSocketClient:
    def __init__(self):
        self.clientId = input("ID nr: ")
        self.uri = f"ws://127.0.0.1:8000/ws/B{self.clientId}"
        self.response = None
        self.status = ""
        self.previous_status = ""
        self.command_dict = {}
        self.image = ImageHandler('Interface/Backend/Client/images', 6)
        self.send_ready = False
        self.ws = None

    def connect(self):
        while True:
            try:
                self.ws = websocket.WebSocketApp(self.uri,
                                                 on_message=self.on_message,
                                                 on_error=self.on_error,
                                                 on_close=self.on_close)
                self.ws.on_open = self.on_open
                self.ws.run_forever()
            except Exception as e:
                logging.error(f"Connection error: {e}")
                logging.error("Reconnecting in 5 seconds...")
                time.sleep(5)

    def on_message(self, ws, message):
        logging.info(f"Received message: {message}")
        try:
            command_data = json.loads(message)
            command = command_data.get("message", "").strip()
            data = command_data.get("data", "").strip()
            logging.info(f"Executing command: {command} with data: {data}")
            if command in self.command_dict:
                self.command_dict[command](data)
            else:
                logging.warning(f"Unknown command: {command}")
        except json.JSONDecodeError:
            logging.warning("Received non-JSON message, ignoring...")

    def on_error(self, ws, error):
        logging.error(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        logging.info("Connection closed")

    def on_open(self, ws):
        logging.info(f"Connected to WebSocket server, your ID is: B{self.clientId}")
        threading.Thread(target=self.send_status, args=(ws,)).start()
        threading.Thread(target=self.send_image, args=(ws,)).start()

    def send_status(self, ws):
        while True:
            current_status = get_status()
            if current_status != self.previous_status and current_status is not " ":
                ws.send(json.dumps({"type_message": "status", "data": current_status}))
                logging.info(f"Sent status: {current_status}")
                self.previous_status = current_status
            time.sleep(1)

    def send_image(self, ws):
        while True:
            if self.send_ready:
                message_data = {
                    "type_message": "get_image",
                    "data": self.image.encode_images()
                }
                ws.send(json.dumps(message_data))
                logging.info("Sent image list")
                self.send_ready = False
            time.sleep(1)

class ImageHandler:
    def __init__(self, image_path, num_of_cams):
        self.image_path = image_path
        self.num_of_cams = num_of_cams

    def encode_images(self):
        encoded_images = []
        try:
            for index in range(self.num_of_cams):
                image_file = os.path.join(self.image_path, f"cam{index}.jpg")
                try:
                    with open(image_file, "rb") as img:
                        encoded_string = base64.b64encode(img.read()).decode('utf-8')
                        encoded_images.append(encoded_string)
                        logging.info(f"Encoded image: {index}")
                except FileNotFoundError:
                    logging.error(f"File not found: {image_file}")
                except Exception as e:
                    logging.error(f"Error encoding image {image_file}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
        return encoded_images

class Calibration_command:
    def __init__(self, client: WebSocketClient):
        self.client = client
        self.client.command_dict = { 
            "B_end_set_machine_config": self.set_machine_config,
            "B_end_start_calibration": self.start_calibration,
            "B_end_stop_calibration": self.stop_calibration,
            "B_end_pause_calibration": self.pause_calibration,
            "B_end_send_images": self.send_images
        }
        self.calibration_config = ""
        self.machine_config_ip = ""
        self.machine_config_num_machines = ""
        self.machine_config_machine_config = ""

    def set_machine_config(self, data):
        try:
            if not isinstance(data, str):
                raise ValueError("Expected a JSON string but got a different type")

            logging.info(f"Received machine config data: {data}") 

            self.calibration_config = json.loads(data)

            self.machine_config_ip = self.calibration_config.get("main_ip", "")
            self.machine_config_num_machines = self.calibration_config.get("number_of_pcs", 1)
            self.machine_config_machine_config = self.calibration_config.get("machine_config", "")

            if not isinstance(self.machine_config_num_machines, int):
                try:
                    self.machine_config_num_machines = int(self.machine_config_num_machines)
                except ValueError:
                    logging.error(f"Invalid number_of_pcs value: {self.machine_config_num_machines}")
                    self.machine_config_num_machines = 1

            logging.info(f"Machine config is set to: {self.machine_config_machine_config}, "
                         f"machine ip is set to: {self.machine_config_ip}, "
                         f"numbers of pc's set to {self.machine_config_num_machines}")

        except json.JSONDecodeError as e:
            logging.error(f"Received invalid JSON in machine config from {self.client.clientId}: {e}")
        except ValueError as e:
            logging.error(f"ValueError in set_machine_config: {e}")

    def start_calibration(self, data):
        self.client.status = "Start calibration"
        self.set_machine_config(data)
        calibration_thread = threading.Thread(target=first_calibration.main_calibration, args=(self.machine_config_ip, self.machine_config_num_machines, self.machine_config_machine_config), daemon=True)
        calibration_thread.start()

    def stop_calibration(self, data):
        self.client.status = "Stop calibration"

    def pause_calibration(self, data):
        self.client.status = "Pause calibration"

    def send_images(self, data):
        self.client.status = "Sending images"
        self.client.send_ready = True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    wsc = WebSocketClient()
    CalibrationProcess = Calibration_command(wsc)

    first_calibration = Calibration()

    threading.Thread(target=wsc.connect).start()