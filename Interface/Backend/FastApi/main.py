from threading import Thread
import logging
from ImageHandler import ImageHandler
from CommandHandler import CommandHandler
from WebSocketServer import WebSocketServer


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ws_server = WebSocketServer()
    server_thread = Thread(target=ws_server.run_server, daemon=True)
    server_thread.start()
    server_thread.join()
