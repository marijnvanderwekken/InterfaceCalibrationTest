from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from threading import Thread
import uvicorn
import asyncio
import json
import logging
import os
import configparser
import base64
import cv2
import re
import numpy as np
from PIL import Image

# Load Configurations
device_settings_path = os.getcwd() + "/config.ini"
config = configparser.ConfigParser(interpolation=None)
config.read(device_settings_path)

# Setup Logging
logging_config = config['logging']
logging.basicConfig(
    filename=logging_config.get('filename', fallback="server.log"),
    filemode=logging_config.get('filemode', fallback="a"),
    format=logging_config.get('format', fallback="%(asctime)s - %(levelname)s - %(message)s"),
    datefmt=logging_config.get('datefmt', fallback="%Y-%m-%d %H:%M:%S"),
    level=getattr(logging, logging_config.get('level', fallback="INFO").upper(), logging.INFO)
)

class WebSocketServer:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(device_settings_path)

        self.frontend_clients = {}
        self.backend_clients = {}

        self.app = FastAPI()
        self.websocket_path = self.config.get('websocket', 'path', fallback="/ws/{clientId}")
        self.app.websocket(self.websocket_path)(self.websocket_endpoint)

        self.image_handler = ImageHandler()
        self.status = ""
        self.previous_status = ""

    async def websocket_endpoint(self, websocket: WebSocket, clientId: str):
        """Handles WebSocket connections."""
        await websocket.accept()

        if clientId in self.frontend_clients or clientId in self.backend_clients:
            await websocket.close()
            logging.info(f"Client {clientId} already connected")
            return

        # Store client connection
        if clientId.startswith("F"):
            self.frontend_clients[clientId] = websocket
        elif clientId.startswith("B"):
            self.backend_clients[clientId] = websocket
        else:
            logging.info(f"Invalid Client ID: {clientId}")
            return
        logging.info(f"Client {clientId} connected")

        try:
            while True:
                message = await websocket.receive_text()
                logging.info(f"Received message from {clientId}: {message}")

                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    logging.error("Received invalid JSON message")
                    continue

                message_type = data.get("type_message", "")

                if message_type == "get_image":
                    await self.image_handler.save_base64_images(data.get("data", []))
                    combined_image = self.image_handler.prepare_image()
                    await self.send_message_to_client("F1", {
                        "type_message": "picture",
                        "data": combined_image
                    })
                elif message_type == "status":
                    self.status = data.get("data", "")
                    if self.status != self.previous_status:
                        await self.broadcast_status(self.status)
                        self.previous_status = self.status

                elif message_type == "command":
                    await self.broadcast_to_backends(data.get("data", ""))
          
        except WebSocketDisconnect:
            logging.info(f"Client {clientId} disconnected")
            self.remove_client(clientId)
        except Exception as e:
            logging.error(f"WebSocket Error: {e}")
            self.remove_client(clientId)

    async def send_message_to_client(self, clientId: str, message: dict):
        """Sends a message to a specific WebSocket client in JSON format."""
        json_message = json.dumps(message)
        if clientId in self.frontend_clients:
            await self.frontend_clients[clientId].send_text(json_message)
        elif clientId in self.backend_clients:
            await self.backend_clients[clientId].send_text(json_message)
        else:
            logging.warning(f"Attempted to send message to non-existent client: {clientId}")

    async def broadcast_status(self, status: str):
        """Broadcasts a status update to all frontend clients."""
        for clientId in self.frontend_clients:
            await self.send_message_to_client(clientId, {
                "type_message": "status",
                "data": status
            })

    async def broadcast_to_backends(self, command: str):
        """Sends a command to all backend clients."""
        for clientId in self.backend_clients:
            await self.send_message_to_client(clientId, {
                "type_message": "command",
                "data": command
            })

    def remove_client(self, clientId: str):
        """Removes a client from the client lists when they disconnect."""
        self.frontend_clients.pop(clientId, None)
        self.backend_clients.pop(clientId, None)

    def run_server(self):
        """Runs the FastAPI WebSocket server."""
        host = config.get('server', 'host', fallback="127.0.0.1")
        port = config.getint('server', 'port', fallback=8000)
        uvicorn.run(self.app, host=host, port=port, timeout_keep_alive=300)

class ImageHandler:
    """Handles image processing and saving."""
    def __init__(self):
        self.save_dir = "decoded_images"
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    async def save_base64_images(self, image_list):
        """Saves a list of base64 images to files."""
        if not image_list:
            logging.warning("Received empty image list")
            return

        logging.info(f"Saving {len(image_list)} images")
        for i, image_data in enumerate(image_list):
            try:
                if not image_data.strip():
                    logging.info(f"Skipping empty image {i}")
                    continue
                image_bytes = base64.b64decode(image_data)
                file_path = os.path.join(self.save_dir, f"cam{i}_output.jpg")
                with open(file_path, "wb") as image_file:
                    image_file.write(image_bytes)
                logging.info(f"Saved image {i+1} to {file_path}")
            except Exception as e:
                logging.error(f"Error saving image {i+1}: {e}")

    def prepare_image(self):
        """Combines images and encodes the result in base64."""
        combined_image_path = self.combine_images_from_folder()
        if not combined_image_path:
            return ""

        try:
            with open(combined_image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
        except Exception as e:
            logging.error(f"Error opening file: {e}")
            return ""

    def combine_images_from_folder(self):
        """Combines multiple images into one."""
        folder_path = self.save_dir
        pattern = r'cam\d+_output\.jpg'
        image_files = sorted([file for file in os.listdir(folder_path) if re.match(pattern, file)])

        if not image_files:
            logging.warning("No images found to combine")
            return None

        images = [cv2.imread(os.path.join(folder_path, img)) for img in image_files]
        if not images:
            logging.warning("Failed to load images")
            return None

        height, width, _ = images[0].shape
        combined_width = sum(img.shape[1] for img in images) + len(images) - 1
        combined_image = np.zeros((height, combined_width, 3), dtype=np.uint8)

        x_offset = 0
        for img in images:
            combined_image[:, x_offset:x_offset + img.shape[1], :] = img
            x_offset += img.shape[1] + 1

        combined_image_path = os.path.join(folder_path, 'combined_image.jpg')
        cv2.imwrite(combined_image_path, combined_image)
        logging.info(f"Saved combined image as {combined_image_path}")
        return combined_image_path

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ws_server = WebSocketServer()
    server_thread = Thread(target=ws_server.run_server, daemon=True)
    server_thread.start()
    server_thread.join()
