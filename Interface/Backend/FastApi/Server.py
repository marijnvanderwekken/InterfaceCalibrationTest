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
        self.handle_status = statusHandler(self)
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
                    if self.data[:6] == "status":
                        self.status = self.data[6:]
                    if self.data[:7] == "picture":
                        await self.send_message_to_client("F1", self.handle_status.sendImage())
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


class statusHandler:
    def __init__(self, server: WebSocketServer):
        self.message = "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"
        self.server = server
        
    #1. Write incoming encoded string to file.bin
    #2. Decode image from file.bin
    #3. Combine all images into one image
    #4. Send combined image to Frontend

    def strToBin(self):
        with open("testing/decodedImage.bin", "wb") as file:
            file.write(self.message.encode())
            file.close()

    def decodeImage(self):
        f = open('testing/decodedImage.bin')
        byte = f.read()
        f.close()

        decode = open('testing/encodedimage.png', 'wb')
        decode.write(base64.b64decode(byte))
        decode.close()

    def combineImages(self):
        images = [Image.open(x) for x in ['testing/images/Cam1.png','testing/images/Cam2.png', 'testing/images/Cam3.png']]
        widths, heights = zip(*(i.size for i in images))

        total_width = sum(widths)
        max_height = max(heights)

        new_im = Image.new('RGB', (total_width, max_height))

        x_offset = 0
        for im in images:
            new_im.paste(im, (x_offset,0))
            x_offset += im.size[0]

        new_im.save('combined.jpg')

    def sendImage(self):
        self.combineImages()
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

    