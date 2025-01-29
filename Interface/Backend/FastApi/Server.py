from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from threading import Thread
import uvicorn
import asyncio
import json
import time
import logging
import os
import configparser


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
        self.clients = {}
        self.app = FastAPI()
        self.message = "status ok"
        self.previousmessage = ""
        self.websocket_path = self.config.get('websocket','path')
        self.websocket_keep_alive = 300
        self.app.websocket(self.websocket_path)(self.websocket_endpoint)
        self.data = ""


    async def websocket_endpoint(self, websocket: WebSocket, clientId: str):
        await websocket.accept()
        self.clients[clientId] = websocket
        logging.info(f"Client nr: {clientId} connected")
    
        connected = True
        
        async def receive_messages():
            nonlocal connected
            while connected:
                try:
                    self.data = await websocket.receive_text()
                    logging.info(f"Data from Client: {clientId} : {self.data}")
                except WebSocketDisconnect:
                    logging.info(f"Client nr: {clientId} disconnected")
                    del self.clients[clientId]
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
                        await self.send_message_to_client("B1",self.data)
                        self.previousmessage = self.data
                    elif messageType == "F_end":
                        await self.send_message_to_client("F1",self.data)
                        self.previousmessage = self.data

                if connected and self.data != self.previousmessage:
                    await self.send_message_to_client("F1",self.data)

        except WebSocketDisconnect:
            logging.info(f"Client nr: {clientId} disconnected")
            del self.clients[clientId]
        except Exception as e:
            logging.info(f"Error: {e}")
        finally:
            connected = False

    async def send_message_to_client(self, clientId: str, message: str):
        if clientId in self.clients:
            websocket = self.clients[clientId]
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

if __name__ == "__main__":
    ws_server = WebSocketServer()
    json_reader = JSONReader(ws_server)
    server_thread = Thread(target=ws_server.run_server, daemon=True)
    server_thread.start()
    json_reader.read_json()