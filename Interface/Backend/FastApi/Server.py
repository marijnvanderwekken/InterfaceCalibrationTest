from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from threading import Thread
import uvicorn
import asyncio
import json
import time
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

message = "status ok" 

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global message
    try:
        await websocket.accept()
        while True:
            await asyncio.sleep(1)
            await websocket.send_text(f"{message}")
            
            data = await websocket.receive_text()
            print(f"Data:{data}")
    except Exception as e:
        print(f"Error: {e}")

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000)



def read_json():
    global message
    while True:
        try:
            with open('test.json') as f:
                d = json.load(f)
                message = d['message']
                statatuscode= d['statuscode']
                message = f"message: {message}, statuscode: {statatuscode}"
        except Exception as e:
            print(f"Error reading JSON: {e}")
        time.sleep(1)

if __name__ == "__main__":
    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()
    #update_message()
    read_json()
