import logging

class PC:
    def __init__(self, pc_id, pc_data):
        self.pc_id = pc_id
        self.ip = pc_data['ip']
        self.master = pc_data['master']
        self.cameras = pc_data['cameras']
        logging.info(f"PC created with: pc_id={self.pc_id}, ip={self.ip}, master={self.master}, cameras={self.cameras}")
        self.status = []

    def __str__(self):
        return f"PC{self.pc_id} (IP: {self.ip})"