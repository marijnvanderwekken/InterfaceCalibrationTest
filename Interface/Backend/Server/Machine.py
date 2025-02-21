import logging
from Pc import PC

class Machine:
    def __init__(self, machine_id, config):
        self.machine_id = machine_id
        self.machine_config = config
        self.type = config[machine_id]['type']
        self.name = config[machine_id]['name']
        self.numb_of_pcs = config[machine_id]['numb_of_pcs']
        self.numb_of_cameras = config[machine_id]['numb_of_cameras']
        self.pcs = {pc_id: PC(pc_id, pc_data) for pc_id, pc_data in config[machine_id]['pcs'].items()}
        self.logged_pcs = []
        self.last_calibration = None
        logging.info(f"Machine created with: type={self.type}, name={self.name}, numb_of_pcs={self.numb_of_pcs}, numb_of_cameras={self.numb_of_cameras}, pcs={self.pcs}")


    def __str__(self):
        return f"{self.name}"


    def getMachineParameter(self, parameter):
        return getattr(self, parameter, None)


    @staticmethod
    def find_machine_id_by_ip(config, ip):
        logging.info(f"Searching for machine with IP: {ip}")
        for machine_id, machine_data in config.items():
            for pc_id, pc_data in machine_data['pcs'].items():
                if pc_data['ip'] == ip:
                    logging.info(f"Found machine ID: {machine_id} for IP: {ip}")
                    return machine_id
        logging.warning(f"No machine found with IP: {ip}")
        return None