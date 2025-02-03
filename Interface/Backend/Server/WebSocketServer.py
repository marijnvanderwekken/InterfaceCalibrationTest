from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from threading import Thread
import uvicorn
import json
import logging
import os
import configparser
from ImageHandler import ImageHandler
from CommandHandler import CommandHandler 

class WebSocketServer:
    def __init__(self):
        device_settings_path = os.getcwd() + "/config.ini"
        self.config = configparser.ConfigParser()
        self.config.read(device_settings_path)

        self.frontend_clients = {}
        self.backend_clients = {}

        self.app = FastAPI()
        self.websocket_path = self.config.get('websocket', 'path', fallback="/ws/{clientId}")
        self.app.websocket(self.websocket_path)(self.websocket_endpoint)

        self.image_handler = ImageHandler()
        self.command_handler = CommandHandler(self)
        self.status = ""
        self.previous_status = ""
        self.machine_config = ""
    async def websocket_endpoint(self, websocket: WebSocket, clientId: str):
        await websocket.accept()
        if clientId.startswith("F"):
            self.frontend_clients[clientId] = websocket
        elif clientId.startswith("B"):
            self.backend_clients[clientId] = websocket
        else:
            logging.info(f"Invalid Client ID: {clientId}")
            await websocket.close()
            return
        logging.info(f"Client {clientId} connected")

        try:
            while True:
                message = await websocket.receive_text()
                logging.info(f"Received message from {clientId}: {message}")
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    logging.error(f"Received invalid JSON message from {clientId}")
                    continue
                message_type = data.get("type_message", "")
                if message_type == "command":
                    message = data.get("message", "")
                    data = data.get("data", "")
                    await self.command_handler.execute_command(message,data)

                elif message_type == "status":
                    self.status = data.get("data", "")
                    if self.status != self.previous_status:
                        await self.broadcast_status(self.status)
    
        except WebSocketDisconnect:
            logging.info(f"Client {clientId} disconnected")
            self.remove_client(clientId)
        except Exception as e:
            logging.error(f"WebSocket Error with {clientId}: {e}")
            self.remove_client(clientId)

    async def broadcast_status(self, status: str):
        for clientId in self.frontend_clients:
            await self.send_message_to_client(clientId, {
                "type_message": "status",
                "data": status
            })

    async def broadcast_to_backends(self, message: str, data: str):
        for clientId in self.backend_clients:
            await self.send_message_to_client(clientId, {
                "type_message": "command",
                "message" : message,
                "data": data
            })

    def remove_client(self, clientId: str):
        self.frontend_clients.pop(clientId, None)
        self.backend_clients.pop(clientId, None)

    def run_server(self):
        host = self.config.get('server', 'host', fallback="127.0.0.1")
        port = self.config.getint('server', 'port', fallback=8000)
        uvicorn.run(self.app, host=host, port=port, timeout_keep_alive=300)

    async def send_message_to_client(self, clientId: str, message: dict):
        json_message = json.dumps(message)
        if clientId in self.frontend_clients:
            await self.frontend_clients[clientId].send_text(json_message)
        elif clientId in self.backend_clients:
            await self.backend_clients[clientId].send_text(json_message)
        else:
            logging.warning(f"Attempted to send message to non-existent client: {clientId}")
