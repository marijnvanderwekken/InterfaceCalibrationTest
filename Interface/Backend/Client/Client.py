import threading
import websocket
import logging
import json
import base64
import os
import time
from sendStatus import *

from NewCalibrationScript.Calibration_qg import *
from SimulateCalibration.Simulate import Calibration_vs, Calibration_qg


class WebSocketClient:
    def __init__(self):
        self.command = Calibration_command(self)
        self.current_ip = os.popen('hostname -I').read().strip().split()[0]
        self.last_octet = self.current_ip.split('.')[-1]
        self.clientId = self.last_octet

        server_ip = input("Enter the server IP (Press enter for default): ")
        if server_ip == "":
            self.uri = f"ws://192.168.1.109:8000/ws/Back-end{self.clientId}"
        else:
            self.uri = f"ws://{server_ip}:8000/ws/Back-end{self.clientId}"
        self.response = None
        self.status = ""
        self.previous_status = ""
        self.command_dict = {}
        self.send_image_ready = False
        self.send_config_ready = False
        self.ws = None
        self.data = ""
        self.machine_config = {}


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
                update_status_error(f"Connection error: {e}")
                update_status_error("Reconnecting in 5 seconds...")
                time.sleep(5)


    def on_message(self, ws, message):
        logging.info(f"Received message: {message}")
        try:
            command_data = json.loads(message)
            command = command_data.get("message", "").strip()
            self.data = command_data.get("data", "").strip()
            logging.info(f"Executing command: {command} with data: {self.data}")
            if command in self.command_dict:
                self.command_dict[command](self.data)
            else:
                logging.warning(f"Unknown command: {command}")
        except json.JSONDecodeError:
            logging.warning("Received non-JSON message, ignoring...")


    def on_error(self, ws, error):
        update_status_error(f"WebSocket error: {error}")


    def on_close(self, ws, close_status_code, close_msg):
        logging.info(f"Connection closed with status code: {close_status_code}, message: {close_msg}")


    def send_status(self, ws):
        while ws.keep_running:
            current_status = get_status()
            if current_status != self.previous_status and current_status != " ":
                ws.send(json.dumps({"type_message": "command","message":"handle_status", "data": current_status, "client": self.clientId}))
                logging.info(f"Send status: {current_status}")
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


    def send_image(self, cams):
        if self.ws and self.ws.keep_running:
            message_data = {
                "type_message": "command",
                "message": "handle_images",
                "data": self.encode_images(cams),
                "client": self.clientId
            }
            self.ws.send(json.dumps(message_data))
            logging.info("Sent images")
        else:
            logging.info("Cannot send images")


    def encode_images(self, cams):
        encoded_images = []
        update_status_info(f"Start to encode: {len(cams)}")
        try:
            for index in range(len(cams)):
                image_file = os.path.join(os.getcwd(), f"utilities/cam{cams[index]}.jpg")
                try:
                    with open(image_file, "rb") as img:
                        encoded_string = base64.b64encode(img.read()).decode('utf-8')
                        encoded_images.append(encoded_string)
                        update_status_info(f"Encoded image: {cams[index]}")
                except FileNotFoundError:
                    update_status_error(f"File not found: {image_file}")
                except Exception as e:
                    update_status_error(f"Error encoding image {image_file}: {e}")
        except Exception as e:
            update_status_error(f"Unexpected error: {e}")
        return encoded_images


    def on_open(self, ws):
        logging.info(f"Connected to WebSocket server, your IP is: {self.current_ip} your ID is: B{self.clientId}")
        self.send_config(self.read_hardware_configuration())
        threading.Thread(target=self.send_status, args=(ws,)).start()


    def read_hardware_configuration(self):
        try:
            config_path = os.path.abspath(os.path.join(os.getcwd(), 'machine.json'))
            with open(config_path) as json_data:
                self.machine_config = json.load(json_data)
            return self.machine_config
        except Exception as e:
            update_status_error(f"Error reading hardware configuration: {e}")
            return {}


class Calibration_command:
    def __init__(self, client: WebSocketClient):
        self.client = client
        self.client.command_dict = { 
            "start_calibration": self.start_calibration,
            "stop_calibration": self.stop_calibration,
            "initialize_machine": self.initialize_machine
        }
        

    def start_calibration(self, data):
        logging.info("start calibration")
         
            

    def stop_calibration(self, data):
        self.client.status = "Stop calibration"


    def initialize_machine(self, data):
        self.client.send_config(self.client.read_hardware_configuration())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    wsc = WebSocketClient()
    CalibrationProcess = Calibration_command(wsc)
    CalibrationProcess.client.read_hardware_configuration()
    threading.Thread(target=wsc.connect).start()