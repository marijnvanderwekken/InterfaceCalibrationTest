import logging
from ImageHandler import ImageHandler
import json
class CommandHandler:
    def __init__(self, server):
        self.image_handler = ImageHandler()
        self.server = server
        self.machine_id = ""
        self.lenpc = ""
        self.commands = {
            
            "B_end_start_calibration": self.start_calibration,
            "B_end_stop_calibration": self.stop_calibration,
            "B_end_send_images": self.send_images,
            "B_end_initialize_machine": self.initialize_machine,
        }

    
    async def execute_command(self,message: str,data: str, config: str, clientId: int ):
        if message in self.commands:
            logging.info(f"Executing command: {message}")
            if message == "B_end_initialize_machine":
                await self.commands[message]()
            elif message == "W_combine_image":
                await self.commands[message](data, config,clientId)
            else:
                await self.commands[message](data)
        else:
            logging.warning(f"Unknown command received: {message}")
    async def initialize_machine(self):
        await self.server.broadcast_to_backends("B_end_initialize_machine","None")

    async def start_calibration(self,data):
            await self.server.broadcast_to_backends("B_end_start_calibration",data)   

    async def stop_calibration(self):
        await self.server.broadcast_to_backends("B_end_stop_calibration","None")

    
    async def send_images(self, data):
        combined_image = self.server.image_handler.prepare_image()
        for clientId in self.server.frontend_clients: 
            await self.server.send_message_to_client(clientId, {
                "type_message": "picture",
                "data": combined_image
            })
