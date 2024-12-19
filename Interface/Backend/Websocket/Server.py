from threading import Thread
import time
import json
from websocket_server import WebsocketServer 

message = "status ok"


def new_client(client, server):
    print(f"New client connected: {client['id']}")


def message_received(client, server, msg):
    print(f"Message from client {client['id']}: {msg}")

def send_updates(server):
    global message
    while True:
        server.send_message_to_all(message)
        time.sleep(1)
def read_json():
    global message
    while True:
        try:
            with open("test.json") as f:
                d = json.load(f)
                message_content = d.get("message", "No message")
                status_code = d.get("statuscode", "No statuscode")
                message = f"message: {message_content}, statuscode: {status_code}"
        except Exception as e:
            print(f"Error reading JSON: {e}")
        time.sleep(1)
def run_websocket_server():
    server = WebsocketServer(host="127.0.0.1", port=8000)
    server.set_fn_new_client(new_client)
    server.set_fn_message_received(message_received)

    server_thread = Thread(target=server.run_forever, daemon=True)
    server_thread.start()
    send_updates(server)


if __name__ == "__main__":
    websocket_thread = Thread(target=run_websocket_server, daemon=True)
    websocket_thread.start()

    read_json()
