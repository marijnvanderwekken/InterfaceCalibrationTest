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
        self.send_image_ready = False
        self.send_config_ready = False
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

    def send_status(self, ws):
        while ws.keep_running:
            current_status = get_status()
            if current_status != self.previous_status and current_status != " ":
                ws.send(json.dumps({"type_message": "status", "data": current_status}))
                logging.info(f"Sent status: {current_status}")
                self.previous_status = current_status
            time.sleep(1)

    def send_config(self, config):
        if self.ws and self.ws.keep_running:
            message_data = {
                "type_message": "config",
                "data": config
            }
            self.ws.send(json.dumps(message_data))
            logging.info("Sent machine config")
        else:
            logging.info("Cannot send machine config, WebSocket is not running")

    def send_image(self):
        if self.ws and self.ws.keep_running:
            message_data = {
            "type_message": "get_image",
            "data": self.image.encode_images()
        }
            self.ws.send(json.dumps(message_data))
            logging.info("Sent machine config")
        else:
            logging.info("Cannot send machine config, WebSocket is not running")



class ImageHandler:
    def __init__(self, image_path, num_of_cams):
        self.image_path = image_path
        self.num_of_cams = num_of_cams

    def encode_images(self):
        encoded_images = []
        try:
            for index in range(self.num_of_cams):
                image_file = os.path.join(os.getcwd(), f"utilities/cam{index}.jpg")
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
            "B_end_start_calibration": self.start_calibration,
            "B_end_stop_calibration": self.stop_calibration,
            "B_end_initialize_machine": self.initialize_machine
        }
        self.machine_config = {}

    def read_hardware_configuration(self):
        try:
            config_path = os.path.abspath(os.path.join(os.getcwd(), 'machine.json'))
            with open(config_path) as json_data:
                self.machine_config = json.load(json_data)
            return self.machine_config
        except Exception as e:
            return f"No config error {e}"

    def start_calibration(self, data):
        first_calibration = Calibration()
        self.client.status = "Start calibration"
        calibration_thread = threading.Thread(target=first_calibration.main_calibration, args=("none","none","none")) #ip -> numb_machines -> machine_config?, daemon=True)
        calibration_thread.start()
        self.client.send_image()

    def stop_calibration(self, data):
        self.client.status = "Stop calibration"

    def initialize_machine(self,data):
        self.client.send_config(self.read_hardware_configuration())
        



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    wsc = WebSocketClient()
    CalibrationProcess = Calibration_command(wsc)
    CalibrationProcess.read_hardware_configuration()
    

    threading.Thread(target=wsc.connect).start()