from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from threading import Thread
import uvicorn
import asyncio
import json
import time
import logging
import os
import configparser
logger = logging.getLogger(__name__)


device_settings_path = os.getcwd() + "/config.ini"

class WebSocketServer:
    def __init__(self):
        self.app = FastAPI()
        self.message = "status ok"
        self.app.websocket("/ws")(self.websocket_endpoint)

    async def websocket_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        connected = True

        async def receive_messages():
            nonlocal connected
            while connected:
                try:
                    data = await websocket.receive_text()
                    print(f"Data: {data}")
                except WebSocketDisconnect:
                    print("Client disconnected")
                    connected = False
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    connected = False
                    break

        asyncio.create_task(receive_messages())

        try:
            while connected:
                await asyncio.sleep(1)
                if connected:
                    await websocket.send_text(f"{self.message}")
        except WebSocketDisconnect:
            print("Client disconnected")
        except Exception as e:
            print(f"Error: {e}")
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
                print(f"Error reading JSON: {e}")
            time.sleep(1)

if __name__ == "__main__":
    ws_server = WebSocketServer()
    json_reader = JSONReader(ws_server)

    server_thread = Thread(target=ws_server.run_server, daemon=True)
    server_thread.start()

    json_reader.read_json()