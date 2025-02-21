import logging
from ImageHandler import ImageHandler
import json
from datetime import datetime
class CommandHandler:
    def __init__(self, server):
        self.image_handler = ImageHandler()
        self.server = server
        self.machine_id = ""
        self.lenpc = ""
        self.commands = {
            "start_calibration": self.start_calibration,
            "stop_calibration": self.stop_calibration,
            "send_combine_images": self.send_combine_images,
            "send_cam_image": self.send_cam_image,
            "initialize_machine": self.initialize_machine,
            "handle_config": self.handle_config,
            "handle_status" : self.handle_status,
            "handle_images" : self.handle_images
        }
    

    async def execute_command(self,message: str,data: str, config: str, client_t: int ):
        if message in self.commands:
            if message == "send_cam_image" or message == "handle_status" or message == "handle_images": 
                await self.commands[message](data,client_t)
            else:
                await self.commands[message](data)
        else:
            logging.warning(f"Unknown command received: {message}")


    async def initialize_machine(self,data):
        await self.handle_back_end(data,"initialize_machine")

    async def start_calibration(self, data):
        await self.handle_back_end(data,"start_calibration")
        
    async def stop_calibration(self,data):
        await self.handle_back_end(data,"stop_calibration")
    
    async def handle_status(self, data, client_t):
        self.server.status = data
        for machine in self.server.machines:
            if client_t in machine.logged_pcs:
                for pc_id, pc in machine.pcs.items():
                    if int(pc.ip) == int(client_t):
                        pc.status.append(self.server.status)
                        logging.info(f"Set status for PC {client_t} ip: {pc_id} in machine {machine.name} to {self.server.status}")
                        await self.server.broadcast_status()
                        break
                else:
                    logging.warning(f"PC {client_t} not found in machine {machine.name}")

    async def send_cam_image(self,data,client_t):
            await self.server.send_image("send_cam_image",data,client_t,)
    

    async def send_combine_images(self, data):
        combined_image = self.server.image_handler.prepare_image()
        for clientId in self.server.frontend_clients: 
            await self.server.send_message_to_client(clientId, {
                "type_message": "picture",
                "data": combined_image,
            })

    async def handle_config(self,data):
        self.server.machine_config = data.get("data", "")
        if self.server.config != self.server.previous_machine_config:
            await self.server.broadcast_config(self.server.machine_config)
    

    
    
    
    async def handle_images(self, data, client_t):
        if data != "":
            for machine in self.server.machines:
                if client_t in machine.logged_pcs:
                    for pc_id, pc in machine.pcs.items():
                        if int(pc.ip) == int(client_t):
                            pc.images = [data]
                            logging.info(f"Replaced image for pc {client_t} ip: {pc_id} in machine {machine.name}")

    async def handle_back_end(self,machineid,handling):
        for machine in self.server.machines:
            if machine.machine_id == machineid:
                machine.last_calibration = datetime.now().isoformat()
                machine_index = self.server.machines.index(machine)
                for ip, pc in self.server.machines[machine_index].getMachineParameter('pcs').items():
                    logging.info(f"Checking PC {pc.ip} in machine {machine.getMachineParameter('name')}")
                    if str(pc.ip) in machine.logged_pcs:
                        logging.info(f"{handling} on pc {pc.ip}")
                        await self.server.send_message_to_client(f"Back-end{pc.ip}", {
                                "type_message": "command",
                                "message": f"{handling}"
                        })
                    else:
                        logging.error(f"Cant start calibration on pc: Back-end{pc.ip} cant find {pc.ip} in {machine.logged_pcs}")