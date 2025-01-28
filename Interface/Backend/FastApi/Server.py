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
    await websocket.accept()
    connected = True
    
    async def receive_messages():
        nonlocal connected
        while connected:
            try:
                data = await websocket.receive_text()
                print(f"Data: {data}")
            except WebSocketDisconnect:
                print("Client disconnected")
                connected = False
                break
            except Exception as e:
                print(f"Error: {e}")
                connected = False
                break

    asyncio.create_task(receive_messages())

    try:
        while connected:
            await asyncio.sleep(1)
            if connected: 
                await websocket.send_text(f"{message}")
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        connected = False

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000)

def read_json():
    global message
    while True:
        try:
            with open('test.json') as f:
                d = json.load(f)
                message = d['message']

                message = f"message: {message}"
        except Exception as e:
            print(f"Error reading JSON: {e}")
        time.sleep(1)

if __name__ == "__main__":
    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()
    read_json()