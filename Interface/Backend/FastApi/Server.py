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
        self.clients = []
        self.app = FastAPI()
        self.message = "status ok"
        self.websocket_path = self.config.get('websocket','path')
        self.app.websocket(self.websocket_path)(self.websocket_endpoint)

    async def websocket_endpoint(self, websocket: WebSocket, clientId: int):
        await websocket.accept()
        self.clients.append(websocket)
        logging.info(f"Client nr: {clientId} connected")
        
        connected = True
        
        async def receive_messages():
            nonlocal connected
            while connected:
                try:
                    data = await websocket.receive_text()
                    logging.info(f"Data from Client: {clientId} : {data}")
                except WebSocketDisconnect:
                    logging.info(f"Client nr: {clientId} disconnected")
                    self.clients.remove(websocket)
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
                if connected:
                    await websocket.send_text(f"{self.message}")
        except WebSocketDisconnect:
            logging.info(f"Client nr: {clientId} disconnected")
            self.clients.remove(websocket)
        except Exception as e:
            logging.info(f"Error: {e}")
        finally:
            connected = False

    def run_server(self):
        config = configparser.ConfigParser()
        config.read(device_settings_path)
        host = config.get('server', 'host')
        port = config.getint('server', 'port')
        uvicorn.run(self.app, host=host, port=port)

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