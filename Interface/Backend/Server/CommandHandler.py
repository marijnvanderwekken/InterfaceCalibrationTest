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

    async def execute_command(self, command: str, data: str):
        if command in self.commands:
            logging.info(f"Executing command: {command}")
            await self.commands[command](data)
        else:
            logging.warning(f"Unknown command received: {command}")

    async def start_calibration(self, data):
        await self.server.broadcast_to_backends("B_end_start_calibration")
        self.server.status = "Calibration Started"

    async def stop_calibration(self, data):
        await self.server.broadcast_to_backends("B_end_stop_calibration")


    async def pause_calibration(self, data):
        await self.server.broadcast_to_backends("B_end_pause_calibration")

    async def send_images(self, data):
        combined_image = self.server.image_handler.prepare_image()
        await self.server.send_message_to_client("F1", {
            "type_message": "picture",
            "data": combined_image
        })
