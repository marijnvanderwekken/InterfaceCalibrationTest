import asyncio
import websockets
import logging
import json

class WebSocketClient:
    def __init__(self):
        self.clientId = "B1"
        self.uri = f"ws://127.0.0.1:8000/ws/{self.clientId}"
        self.message = ""
        self.response = None
        self.status = " "
        self.previousstatus = ""
        self.command_dict = {}

    async def connect(self):
        while True:
            try:
                async with websockets.connect(self.uri) as websocket:
                    logging.info("Opened connection, press CTRL + C to close connection")

                    async def send_status():
                        while True:
                            if self.status != self.previousstatus:
                                await websocket.send(f"status{self.status}")
                                logging.info(f"Sent status: {self.status}")
                                self.previousstatus = self.status
                            await asyncio.sleep(1)

                    async def receive_message():
                        while True:
                            try:
                                self.response = await websocket.recv()
                                command = self.response.strip()

                                if command in self.command_dict:
                                    self.command_dict[command]()
                                    await websocket.send(f"Command received, running: {command}")
                                else:
                                    await websocket.send(f"Unknown command: {command}")
                                    logging.info(f"Unknown command: {command}")
                            except websockets.ConnectionClosed:
                                logging.info("Connection closed")
                                break

                    receive_task = asyncio.create_task(receive_message())
                    send_task = asyncio.create_task(send_status())

                    await asyncio.gather(receive_task, send_task)

            except Exception as e:
                logging.error(f"Connection error: {e}")
                logging.error("Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

class JSONReader:
    def __init__(self, client: WebSocketClient):
        self.client = client

    async def read_json(self):
        while True:
            try:
                with open('test2.json') as f:
                    d = json.load(f)
                    #self.client.status = d['status'] 
            except Exception as e:
                logging.error(f"Error reading JSON: {e}")
            await asyncio.sleep(1)

class Calibration:
    def __init__(self, client: WebSocketClient):
        self.client = client
        self.client.command_dict = { 
            "B_end_start_calibration": self.start_calibration,
            "B_end_stop_calibration": self.stop_calibration,
            "B_end_pause_calibration": self.pause_calibration
        }

    def start_calibration(self):
        self.client.status = "Start calibration"  

    def stop_calibration(self):
        self.client.status = "Stop calibration"
          
    def pause_calibration(self):
        self.client.status = "Pause calibration"  


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    wsc = WebSocketClient()
    json_reader = JSONReader(wsc)
    CalibrationProces = Calibration(wsc)  

    loop = asyncio.get_event_loop()
    loop.create_task(wsc.connect()) 
    loop.create_task(json_reader.read_json())
    loop.run_forever() 
