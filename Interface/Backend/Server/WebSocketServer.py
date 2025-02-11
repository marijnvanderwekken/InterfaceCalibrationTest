from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from threading import Thread
import uvicorn
import json
import logging
import os
import configparser

from ImageHandler import ImageHandler
from CommandHandler import CommandHandler 
from Machine import Machine
import websockets

class WebSocketServer:
    def __init__(self):
        self._load_config()
        self._initialize_server()
        self._initialize_handlers()
        self._initialize_state()

    def _load_config(self):
        device_settings_path = os.getcwd() + "/config.ini"
        self.config = configparser.ConfigParser()
        self.config.read(device_settings_path)

    def _initialize_server(self):
        self.app = FastAPI()
        self.websocket_path = self.config.get('websocket', 'path', fallback="/ws/{clientId}")
        self.app.websocket(self.websocket_path)(self.websocket_endpoint)

    def _initialize_handlers(self):
        self.image_handler = ImageHandler()
        self.command_handler = CommandHandler(self)

    def _initialize_state(self):
        self.frontend_clients = {}
        self.backend_clients = {}
        self.status = ""
        self.machine_config = ""
        self.previous_machine_config = ""
        self.previous_status = ""
        self.previousClient = 0
        self.fclient = 0
        self.machines = []

    async def websocket_endpoint(self, websocket: WebSocket, clientId: str):
        await websocket.accept()
        if clientId.startswith("Front-end"):
            await self._handle_frontend_client(websocket, clientId)
        elif clientId.startswith("Back-end"):
            await self._handle_backend_client(websocket, clientId)
        else:
            logging.info(f"Invalid Client ID: {clientId}")
            await websocket.close()
            return

        logging.info(f"Client {clientId} connected")
        await self.broadcast_connected_pcs(self.machines)

        await self._receive_messages(websocket, clientId)

    async def _handle_frontend_client(self, websocket: WebSocket, clientId: str):
        self.fclient += 1
        unique_client_id = f"F{self.fclient}"
        self.frontend_clients[unique_client_id] = websocket
        clientId = unique_client_id
        logging.info(f"Client id is {clientId}")
        await self.broadcast_config(self.machine_config)
        await self.broadcast_status()

    async def _handle_backend_client(self, websocket: WebSocket, clientId: str):
        self.backend_clients[clientId] = websocket
        await self._initialize_backend_client(websocket, clientId)
        await self.broadcast_status()
        await self.broadcast_config(self.machine_config)

    async def _initialize_backend_client(self, websocket: WebSocket, clientId: str):
        try:
            while True:
                message = await websocket.receive_text()
                logging.info(message)
                data = self._parse_json(message, clientId)
                if not data:
                    continue

                if data.get("type_message", "") == "config":
                    self.machine_config = data.get("data", "")
                    await self._create_machine_object(clientId, self.machine_config)
                    self.previousClient = clientId
                    break
        except WebSocketDisconnect:
            logging.info(f"Backend client {clientId} disconnected during initial config")
            self.remove_client(clientId)
        except Exception as e:
            logging.error(f"WebSocket Error with backend client {clientId}: {e}")
            self.remove_client(clientId)

    async def _receive_messages(self, websocket: WebSocket, clientId: str):
        try:
            while True:
                message = await websocket.receive_text()
                data = self._parse_json(message, clientId)
                if not data:
                    continue

                message_type = data.get("type_message", "")
                # logging.info(f"Received message from {clientId}: {message}")
                if message_type == "command":
                    await self._execute_command(data)
        except WebSocketDisconnect:
            logging.info(f"Client {clientId} disconnected")
            self.remove_client(clientId)
            await self.broadcast_connected_pcs(self.machines)
        except Exception as e:
            logging.error(f"WebSocket Error with {clientId}: {e}")
            self.remove_client(clientId)

    def _parse_json(self, message: str, clientId: str):
        try:
            return json.loads(message)
        except json.JSONDecodeError:
            logging.error(f"Received invalid JSON message from {clientId}")
            return None

    async def _execute_command(self, data: dict):
        
        command_message = data.get("message", "")
        command_data = data.get("data", "")
        config_t = data.get("config", "")
        client_t = data.get("client", "")
        await self.command_handler.execute_command(command_message, command_data, config_t, client_t)

    async def _create_machine_object(self, clientId: str, config: str):
        ip = clientId[8:]
        logging.info(f"Extracted IP: {ip}")
        if not ip.isdigit():
            raise ValueError(f"Invalid IP extracted from clientId: {ip}")

        machine_id = Machine.find_machine_id_by_ip(config, int(ip))
        if machine_id is None:
            raise ValueError(f"No machine found with IP: {ip}")

        new_machine = Machine(machine_id, config)
        await self._add_or_update_machine(new_machine, ip)

    async def _add_or_update_machine(self, new_machine: Machine, ip: str):
        existing_machine_names = [machine.getMachineParameter('name') for machine in self.machines]
        if new_machine.getMachineParameter('name') in existing_machine_names:
            machine_index = existing_machine_names.index(new_machine.getMachineParameter('name'))
            logging.info(f"Machine object already created, continue")
            self.machines[machine_index].logged_pcs.append(ip)
        else:
            logging.info(f"Successfully created machine: {new_machine.getMachineParameter('name')} number of total machines: {len(self.machines)}")
            self.machines.append(new_machine)
            machine_index = self.machines.index(new_machine)
            self.machines[machine_index].logged_pcs.append(ip)

        logging.info(f"Succesfully put connected pc {ip} in connected")
        await self.broadcast_connected_pcs(self.machines)

        try:
            if new_machine in self.machines:
                machine_index = self.machines.index(new_machine)
            for pc_id, pc in self.machines[machine_index].getMachineParameter('pcs').items():
                logging.info(f"PC {pc_id} for machine {new_machine.getMachineParameter('name')}: {pc}")
        except Exception as e:
            logging.info(f"Cant find cameras error: {e}")

    async def broadcast_connected_pcs(self, machines):
        logging.info("Send connected pcs to frontend")
        for clientId in list(self.frontend_clients.keys()):
            await self._send_message_to_client(clientId, {
                "type_message": "connected_pcs",
                "data": [machine.logged_pcs for machine in machines]
            })

    async def broadcast_status(self):
        logging.info("Send status to frontend")
        for machine in self.machines:
            for pc_id, pc in machine.pcs.items():
                pc_data = {
                    
                    "pc_id": pc.pc_id,
                    "last_calibration": machine.last_calibration,
                    "ip": pc.ip,
                    "master": pc.master,
                    "cameras": pc.cameras,
                    "status": pc.status,
                    "last_images": pc.images
                    
                }
                for clientId in list(self.frontend_clients.keys()):
                    await self._send_message_to_client(clientId, {
                        "type_message": "status",
                        "data": pc_data,
                    })

    async def broadcast_config(self, config: str):
        for clientId in list(self.frontend_clients.keys()):
            await self._send_message_to_client(clientId, {
                "type_message": "config",
                "data": config
            })

    async def broadcast_to_backends(self, message: str, data: str):
        for clientId in list(self.backend_clients.keys()):
            await self._send_message_to_client(clientId, {
                "type_message": "command",
                "message": message,
                "data": data
            })

    async def send_image(self, message: str, data: str, client: str):
        for clientId in list(self.frontend_clients.keys()):
            await self._send_message_to_client(clientId, {
                "type_message": "command",
                "message": message,
                "data": data,
                "client": client
            })

    def remove_client(self, clientId: str):
        self.frontend_clients.pop(clientId, None)
        self.backend_clients.pop(clientId, None)
        for machine in self.machines:
            if clientId[8:] in machine.logged_pcs:
                pc_index = machine.logged_pcs.index(clientId[8:])
                logging.info(f"Log out pc: {machine.logged_pcs[pc_index]}")
                del machine.logged_pcs[pc_index]
                break

    def run_server(self):
        host = self.config.get('server', 'host', fallback="127.0.0.1")
        port = self.config.getint('server', 'port', fallback=8000)
        uvicorn.run(self.app, host=host, port=port, timeout_keep_alive=300)

    async def _send_message_to_client(self, clientId: str, message: dict):
        json_message = json.dumps(message)
        try:
            if clientId in self.frontend_clients:
                await self.frontend_clients[clientId].send_text(json_message)
            elif clientId in self.backend_clients:
                await self.backend_clients[clientId].send_text(json_message)
            else:
                logging.warning(f"Attempted to send message to non-existent client: {clientId}")
        except websockets.exceptions.ConnectionClosedOK:
            logging.info(f"Connection to {clientId} closed normally")
            self.remove_client(clientId)
        except RuntimeError as e:
            logging.error(f"Failed to send message to {clientId}: {e}")
            self.remove_client(clientId)