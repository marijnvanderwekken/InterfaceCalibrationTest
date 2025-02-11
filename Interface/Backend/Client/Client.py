import threading
import websocket
import logging
import json
import base64
import os
import time
from sendStatus import *
from SimulateCalibration.Simulate import *

class WebSocketClient:
    def __init__(self):
        self.command = Calibration_command(self)
        self.current_ip = os.popen('hostname -I').read().strip().split()[0]
        self.last_octet = self.current_ip.split('.')[-1]
        
        self.clientId = self.last_octet
        self.uri = f"ws://192.168.1.90:8000/ws/Back-end{self.clientId}"
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
        machine_config = self.client.read_hardware_configuration()
        if isinstance(machine_config, str):
            update_status_error(f"in machine configuration: {machine_config}, stop calibration")
            return

        if data not in machine_config:
            update_status_error(f"Machine ID {data} not found in configuration, stop calibration")
            return

        machine = machine_config[data]
        

       

        
        
        for pc_key in machine['pcs']:
            pc = machine['pcs'][pc_key]
            if self.client.last_octet == str(pc['ip']):
                update_status_info(f"Start calibrating on this pc {pc['ip']}")
                if machine['type'] == "QG":   
                    first_calibration_qg = Calibration_qg()
                    calibration_qg_thread = threading.Thread(target=first_calibration_qg.main, args=(), daemon=True)
                    calibration_qg_thread.start()
                    self.client.send_image(pc['cameras'])
                else:
                    first_calibration_vs = Calibration_vs()
                    calibration_vs_thread = threading.Thread(target=first_calibration_vs.main, args=(), daemon=True)
                    calibration_vs_thread.start()
                    self.client.send_image(pc['cameras'])
            #self.client.send_image(pc['cameras'])
        #     first_overal_calibration = Calibration()
        # first_overal_calibration = threading.Thread(target=first_overal_calibration.main_calibration, args=(), daemon=True)
        # first_overal_calibration.start()
                
            
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