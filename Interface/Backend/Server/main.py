from threading import Thread
import logging
from ImageHandler import ImageHandler
from CommandHandler import CommandHandler
from WebSocketServer import WebSocketServer
import configparser

if __name__ == "__main__":
    ws_server = WebSocketServer()
    config = configparser.RawConfigParser()
    config.read('config.ini')

    logging_config = config['logging']

    logging.basicConfig(
        filename=logging_config.get('filename'),
        filemode=logging_config.get('filemode'),
        format=logging_config.get('format'),
        datefmt=logging_config.get('datefmt'),
        level=logging_config.get('level').upper()
    )
    
    server_thread = Thread(target=ws_server.run_server, daemon=True)
    server_thread.start()
    server_thread.join()
