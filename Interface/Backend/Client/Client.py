import asyncio
import websockets
import logging
import json
import base64
import os

class WebSocketClient:
    def __init__(self):
        self.clientId = "B1"
        self.uri = f"ws://127.0.0.1:8000/ws/{self.clientId}"
        self.response = None
        self.status = ""
        self.previous_status = ""
        self.command_dict = {}
        self.image = ImageHandler('Interface/Backend/Client/images', 6)
        self.encoded_images = self.image.encode_images()
        self.send_ready = False

    async def connect(self):
        
        while True:
            try:
                async with websockets.connect(self.uri) as websocket:
                    logging.info("Connected to WebSocket server")

                    receive_task = asyncio.create_task(self.receive_message(websocket))
                    send_status_task = asyncio.create_task(self.send_status(websocket))
                    send_image_task = asyncio.create_task(self.send_image(websocket))

                    await asyncio.gather(receive_task, send_status_task, send_image_task)

            except Exception as e:
                logging.error(f"Connection error: {e}")
                logging.error("Reconnecting in 5 seconds...")
                await asyncio.sleep(5) 

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

    async def receive_message(self, websocket):
        while True:
            try:
                response = await websocket.recv()
                if not response:
                    logging.info("Received empty response, ignoring...")
                    continue 

                logging.info(f"Received: {response}")
                
                try:
                    command_data = json.loads(response)
                    command = command_data.get("data", "").strip()
                    logging.info(command)
                    if command in self.command_dict:    
                        self.command_dict[command]()
                        response_msg = {"status": f"Command received: {command}"}
                    else:
                        response_msg = {"error": f"Unknown command: {command}"}
                        logging.info(f"Unknown command: {command}")

                    await websocket.send(json.dumps(response_msg))  # Send response to server

                except json.JSONDecodeError:
                    logging.warning("Received non-JSON message, ignoring...")

            except websockets.ConnectionClosed:
                logging.info("Connection closed, stopping receive_message task")
                break
            except Exception as e:
                logging.error(f"Error receiving message: {e}")
                break 



class ImageHandler:
    def __init__(self, image_path, num_of_cams):
        self.image_path = image_path
        self.num_of_cams = num_of_cams

    def encode_images(self):
        """Encodes images in base64 format and returns a list."""
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


class Calibration:
    def __init__(self, client: WebSocketClient):
        self.client = client
        self.client.command_dict = { 
            "B_end_start_calibration": self.start_calibration,
            "B_end_stop_calibration": self.stop_calibration,
            "B_end_pause_calibration": self.pause_calibration,
            "B_end_send_images": self.send_images
        }

    def start_calibration(self):
        self.client.status = "Start calibration"  

    def stop_calibration(self):
        self.client.status = "Stop calibration"
          
    def pause_calibration(self):
        self.client.status = "Pause calibration"  

    def send_images(self):
        self.client.status = "Sending images"  
        self.client.send_ready = True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    wsc = WebSocketClient()
    CalibrationProcess = Calibration(wsc)  

    loop = asyncio.get_event_loop()
    loop.create_task(wsc.connect()) 
    loop.run_forever()
