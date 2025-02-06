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
            "B_end_send_combine_images": self.send_combine_images,
            "W_send_cam_image": self.send_cam_image,
            "B_end_initialize_machine": self.initialize_machine,
        }

    
    async def execute_command(self,message: str,data: str, config: str, client_t: int ):
        if message in self.commands:
            logging.info(f"Executing command: {message}")
            if message == "B_end_initialize_machine":
                await self.commands[message]()
            elif message == "W_send_cam_image":
                await self.commands[message](data,client_t)
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

    async def send_cam_image(self,data,client_t):
            await self.server.send_image("W_send_cam_image",data,client_t,)
            
    
    async def send_combine_images(self, data):
        combined_image = self.server.image_handler.prepare_image()
        for clientId in self.server.frontend_clients: 
            await self.server.send_message_to_client(clientId, {
                "type_message": "picture",
                "data": combined_image,
            })
