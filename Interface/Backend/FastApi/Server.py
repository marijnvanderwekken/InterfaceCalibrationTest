from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from threading import Thread
import uvicorn
import asyncio
import json
import time
import logging
import os
import configparser
import base64
from PIL import Image

device_settings_path = os.getcwd() + "/config.ini"

config = configparser.ConfigParser(interpolation=None)
config.read(device_settings_path)

logging_config = config['logging']
logging.basicConfig(
    filename=logging_config.get('filename'),
    filemode=logging_config.get('filemode'),
    format=logging_config.get('format'),
    datefmt=logging_config.get('datefmt'),
    level=getattr(logging,logging_config.get('level').upper(),logging.INFO)
)

class WebSocketServer:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(device_settings_path)
        self.frontend_clients = {}
        self.backend_clients = {}
        self.app = FastAPI()
        self.message = "status ok"
        self.previousmessage = ""
        self.websocket_path = self.config.get('websocket','path')
        self.websocket_keep_alive = 300
        self.app.websocket(self.websocket_path)(self.websocket_endpoint)
        self.data = ""
        self.status = ""
        self.previousstatus = ""
        self.handle_image = ImageHandler(self)

    async def websocket_endpoint(self, websocket: WebSocket, clientId: str):
        await websocket.accept()
        if clientId in self.frontend_clients or clientId in self.backend_clients:
            await websocket.close()
            logging.info(f"Client nr: {clientId} already connected")
            if clientId in self.frontend_clients:
                del self.frontend_clients[clientId]
            elif clientId in self.backend_clients:
                del self.backend_clients[clientId]
            return

        if clientId[:1] == "F":
            self.frontend_clients[clientId] = websocket
        elif clientId[:1] == "B":    
            self.backend_clients[clientId] = websocket
        else:
            logging.info("Client nr not available")
        logging.info(f"Client nr: {clientId} connected")

        connected = True
     
        async def receive_messages():
            nonlocal connected
            while connected:
                try:
                    self.data = await websocket.receive_text()
                    logging.info(f"Data from Client: {clientId} : {self.data}")
                    if self.data[:10] == "image_list":
                        await self.handle_image.save_base64_images(self.data)
                    if self.data[:6] == "status":
                        self.status = self.data[6:]
                    if self.data[:7] == "picture":
                        await self.send_message_to_client("F1", self.handle_image.prepare_image())
                except WebSocketDisconnect:
                    logging.info(f"Client nr: {clientId} disconnected")
                    if clientId in self.frontend_clients:
                        del self.frontend_clients[clientId]
                    elif clientId in self.backend_clients:
                        del self.backend_clients[clientId]
                    connected = False
                    break
                except Exception as e:
                    logging.info(f"Error: {e}")
                    connected = False
                    break   
                
        asyncio.create_task(receive_messages())
        
        #combine these two
        try:
            while connected:
                await asyncio.sleep(1)
                if connected and self.data != self.previousmessage:
                    messageType = self.data[:5]
                    self.data = self.data[5:]
                    if messageType == "B_end":
                        for clientId in self.backend_clients:
                            await self.send_message_to_client(clientId,self.data)
                            self.previousmessage = self.data
                if self.status != self.previousstatus:
                        for clientId in self.frontend_clients:
                            await self.send_message_to_client(clientId, self.status)
                            self.previousstatus = self.status

        except WebSocketDisconnect:
            logging.info(f"Client nr: {clientId} disconnected")
            if clientId in self.frontend_clients:
                del self.frontend_clients[clientId]
            elif clientId in self.backend_clients:
                del self.backend_clients[clientId]

        except Exception as e:
            logging.info(f"Error: {e}")
        finally:
            connected = False

    async def send_message_to_client(self, clientId: str, message: str):
        if clientId in self.frontend_clients:
            websocket = self.frontend_clients[clientId]
            await websocket.send_text(message) 
        elif clientId in self.backend_clients:    
            websocket = self.backend_clients[clientId]
            await websocket.send_text(message)
            logging.info(f"Sent message to Client {clientId}: {message}")
        else:
            logging.info(f"Client {clientId} not connected")

    def run_server(self):
        config = configparser.ConfigParser()
        config.read(device_settings_path)
        host = config.get('server', 'host')
        port = config.getint('server', 'port')
        uvicorn.run(self.app, host=host, port=port, timeout_keep_alive=300, ws_ping_interval=None, ws_ping_timeout=None)

class JSONReader:
    def __init__(self, server: WebSocketServer):
        self.server = server

    def read_json(self):
        while True:
            try:
                with open('test.json') as f:
                    d = json.load(f)
                    self.server.message = d['message']
                    self.server.message = f"message: {self.server.message}"
            except Exception as e:
                logging.info(f"Error reading JSON: {e}")
            time.sleep(1)


class ImageHandler:
    def __init__(self, server: WebSocketServer):
        self.server = server
        self.message = ""

    def str_to_bin(self):
        with open("testing/decodedImage.bin", "wb") as file:
            file.write(self.message.encode())
            file.close()

    async def save_base64_images(self, image_list, save_dir="decoded_images"):
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        image_list = image_list[10:] 
        images_data = image_list.split(',')
        logging.info(f"imagesdata: {images_data}")
        logging.info(f"Number of images to save: {len(images_data)}")

        for i, image_data in enumerate(images_data):
            try:
                if not image_data.strip():
                    logging.info(f"Image {i+1} is empty")
                    continue

                image_bytes = base64.b64decode(image_data)
                file_path = os.path.join(save_dir, f"Cam{i+1}.png")
                with open(file_path, "wb") as image_file:
                    image_file.write(image_bytes)
                logging.info(f"Saved image {i+1} to {file_path}")
            except Exception as e:
                logging.info(f"Error saving image {i+1}: {e}")

    def combine_images(self):
        images = [Image.open(x) for x in ['decoded_images/Cam1.png','decoded_images/Cam2.png', 'decoded_images/Cam3.png', 'decoded_images/Cam4.png']]
        widths, heights = zip(*(i.size for i in images))

        total_width = sum(widths)
        max_height = max(heights)

        new_im = Image.new('RGB', (total_width, max_height))

        x_offset = 0
        for im in images:
            new_im.paste(im, (x_offset,0))
            x_offset += im.size[0]

        new_im.save('combined.jpg')

    def prepare_image(self):
        self.combine_images()
        try:
            with open("combined.jpg", "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
        except Exception as e:
            logging.error(f"Error open file: {e} ")
            return "No picture found"   
        logging.error(f"picture{encoded_string}") 
        return f"picture{encoded_string}"

if __name__ == "__main__":
    ws_server = WebSocketServer()
    server_thread = Thread(target=ws_server.run_server, daemon=True)
    server_thread.start()
    json_reader = JSONReader(ws_server)
    json_reader.read_json()

    