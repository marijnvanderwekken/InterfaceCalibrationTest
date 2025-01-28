from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Path
from threading import Thread
import uvicorn
import asyncio
import json
import time
import logging
import os
import configparser

# Adjusted path to go two directories up
device_settings_path = os.getcwd() + "/config.ini"

# Load configuration with interpolation disabled
config = configparser.ConfigParser(interpolation=None)
config.read(device_settings_path)

# Configure logging
logging_config = config['logging']
logging.basicConfig(
    filename=logging_config.get('filename'),
    filemode=logging_config.get('filemode'),
    format=logging_config.get('format'),
    datefmt=logging_config.get('datefmt'),
    level=getattr(logging, logging_config.get('level').upper(), logging.INFO)
)
logger = logging.getLogger(__name__)

# Add console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(getattr(logging, logging_config.get('level').upper(), logging.INFO))
console_handler.setFormatter(logging.Formatter(
    fmt=logging_config.get('format'),
    datefmt=logging_config.get('datefmt')
))
logger.addHandler(console_handler)

class WebSocketServer:
    def __init__(self):
        self.config = config
        self.app = FastAPI()
        self.message = "status ok"
        self.websocket_path = self.config.get('websocket', 'path', fallback='/ws/{clientId}')
        self.heartbeat_interval = self.config.getint('websocket', 'heartbeat_interval', fallback=30)
        self.clients = []
        self.app.websocket(self.websocket_path)(self.websocket_endpoint)

    async def websocket_endpoint(self, websocket: WebSocket, clientId: int = Path(...)):
        await websocket.accept()
        self.clients.append((websocket, clientId))
        logger.info(f"Client {clientId} connected, total clients: {len(self.clients)}")
        connected = True

        async def receive_messages():
            nonlocal connected
            while connected:
                try:
                    data = await websocket.receive_text()
                    logger.info(f"Client {clientId} sent data: {data}")
                except WebSocketDisconnect:
                    logger.info(f"Client {clientId} disconnected")
                    self.clients.remove((websocket, clientId))
                    connected = False
                    break
                except Exception as e:
                    logger.error(f"Error with client {clientId}: {e}")
                    connected = False
                    break

        asyncio.create_task(receive_messages())

        try:
            while connected:
                await asyncio.sleep(self.heartbeat_interval)
                if connected:
                    await websocket.send_text(f"{self.message}")
        except WebSocketDisconnect:
            logger.info(f"Client {clientId} disconnected")
            self.clients.remove((websocket, clientId))
        except Exception as e:
            logger.error(f"Error with client {clientId}: {e}")
        finally:
            if (websocket, clientId) in self.clients:
                self.clients.remove((websocket, clientId))
            connected = False


    def run_server(self):
        host = self.config.get('server', 'host')
        port = self.config.getint('server', 'port')

        uvicorn.run(self.app, host=host, port=port)

class JSONReader:
    def __init__(self, server: WebSocketServer):
        self.server = server
        self.config = config
        self.json_file_path = self.config.get('json', 'file_path', fallback='../../test.json')
        self.read_interval = self.config.getint('json', 'read_interval', fallback=1)
        self.last_content = None

    def read_json(self):
        while True:
            try:
                with open('test.json') as f:
                    content = f.read()
                    if content != self.last_content:
                        self.last_content = content
                        d = json.loads(content)
                        self.server.message = d['message']
                        logger.info(f"Updated message: {self.server.message}")
            except Exception as e:
                logger.error(f"Error reading JSON: {e}")
            time.sleep(self.read_interval)

if __name__ == "__main__":
    ws_server = WebSocketServer()
    json_reader = JSONReader(ws_server)

    server_thread = Thread(target=ws_server.run_server, daemon=True)
    server_thread.start()

    json_reader.read_json()