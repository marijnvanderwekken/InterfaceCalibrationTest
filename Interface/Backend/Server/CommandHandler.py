import logging

class CommandHandler:
    def __init__(self, server):
        self.server = server
        self.commands = {
            
            "B_end_start_calibration": self.start_calibration,
            "B_end_stop_calibration": self.stop_calibration,
            "B_end_pause_calibration": self.pause_calibration,
            "B_end_send_images": self.send_images
        }

    async def execute_command(self,message: str,data: str):
        if message in self.commands:
            logging.info(f"Executing command: {message}")
            await self.commands[message](data)
        else:
            logging.warning(f"Unknown command received: {message}")

    async def start_calibration(self,data):
            await self.server.broadcast_to_backends("B_end_start_calibration",data)   

    async def stop_calibration(self, data):
        await self.server.broadcast_to_backends("B_end_stop_calibration","None")

    async def pause_calibration(self, data):
        await self.server.broadcast_to_backends("B_end_pause_calibration","None")

    async def send_images(self, data):
        combined_image = self.server.image_handler.prepare_image()
        for clientId in self.server.frontend_clients: 
            await self.server.send_message_to_client(clientId, {
                "type_message": "picture",
                "data": combined_image
            })
