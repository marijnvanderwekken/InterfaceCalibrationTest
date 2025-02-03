import asyncio
import websockets
import logging
import json
import base64
import os
import sys
from sendStatus import get_status
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
        #self.encoded_images = self.image.encode_images()
        self.send_ready = False 
        self.calibration_config = ""
    async def connect(self):
        
        while True:
            try:
                async with websockets.connect(self.uri) as websocket:
                    logging.info(f"Connected to WebSocket server, your ID is: B{self.clientId} ")

                    receive_task = asyncio.create_task(self.receive_message(websocket))
                    send_status_task = asyncio.create_task(self.send_status(websocket))
                    send_image_task = asyncio.create_task(self.send_image(websocket))

                    await asyncio.gather(receive_task, send_status_task, send_image_task)

            except Exception as e:
                logging.error(f"Connection error: {e}")
                logging.error("Reconnecting in 5 seconds...")
                await asyncio.sleep(5) 

    async def send_status(self, websocket):
            while True:
                if self.status != self.previous_status:
                    message_data = {
                        "type_message": "status",
                        "data": self.status
                    }
                    await websocket.send(json.dumps(message_data))  
                    logging.info(f"Sent status: {self.status}")
                    self.previous_status = self.status
                await asyncio.sleep(1)

    async def send_image(self, websocket):
        while True:
            if self.send_ready:
                message_data = {
                    "type_message": "get_image",
                    "data": self.encoded_images
                }
                await websocket.send(json.dumps(message_data)) 
                logging.info("Sent image list")
                self.send_ready = False
            await asyncio.sleep(1)
    
    
    async def receive_message(self, websocket):
        while True:
            try:
                self.response = await websocket.recv()
                logging.info(f"Received message: {self.response}")
                try:
                    command_data = json.loads(self.response)
                    command = command_data.get("message", "").strip()
                    data = command_data.get("data", "").strip()
                    logging.info(f"Executing command: {command} with data: {data}")
                    if command in self.command_dict:
                        await self.command_dict[command](data)
                    else:
                        logging.warning(f"Unknown command: {command}")
                except json.JSONDecodeError:
                    logging.warning("Received non-JSON message, ignoring...")
            except websockets.ConnectionClosed:
                logging.info("Connection closed")
                break
            


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
            "B_end_start_calibration": self.start_calibration,
            "B_end_send_images": self.send_images
        }

        self.calibration_config = ""
        self.machine_config_ip = ""
        self.machine_config_num_machines = ""
        self.machine_config_machine_config = ""



    async def start_calibration(self,data):
        self.client.status = "Started calibration"
        try:
  
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
        
        first_calibration.main_calibration(self.machine_config_ip, self.machine_config_num_machines, self.machine_config_machine_config)


    async def send_images(self, data):
        self.client.status = "Sending images"
        self.client.send_ready = True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    wsc = WebSocketClient()
    CalibrationProcess = Calibration_command(wsc)  

    first_calibration = Calibration()

    loop = asyncio.get_event_loop()
    loop.create_task(wsc.connect()) 
    loop.run_forever()