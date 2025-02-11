import os
import re
import shutil
import configparser
import platform
import random
import json
from time import sleep
from datetime import datetime
from pathlib import Path
import logging
import queue
from threading import Thread
import queue
import threading
import time
from sendStatus import *

class Calibration_vs:
        def main(self):
            update_status_info("Starting vs grader script")

class Calibration_qg:
    def main(self):
            update_status_info("Starting qg grader script")
    
class Calibration:
    
    def validate_ip(self,ip):
        pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
        return bool(re.match(pattern, ip))

    def simulate_ping(self,ip):
        sleep(random.uniform(0.1, 0.5))  
        return random.choice([True, False])

    def clear_directory(self,directory_path):
        sleep(random.uniform(0.1, 0.5))  
        update_status_info(f"Clearing directory: {directory_path}")

    def retrieve_data_from_file(self,file_path):
        sleep(random.uniform(0.1, 0.5))  
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                data = [line.strip() for line in file if line.strip()]
            update_status_info(f"Reading {len(data)} lines from {file_path}")
            return data
        else:
            update_status_info(f"Warning: File {file_path} not found.")
            return []

    def simulate_ssh_command(self,ip, command):
        sleep(random.uniform(0.1, 0.5))
        update_status_info(f"SSH command on {ip}: {command}")

    def merge_files_in_folder(self,folder_path):
        sleep(random.uniform(0.1, 0.5))
        update_status_info(f"Merging files in {folder_path}")

    def extract_exposure(self,ip):
        sleep(random.uniform(0.1, 0.5)) 
        update_status_info(f"Exposure extraction for {ip}")

    def extract_cam_images(self,ip, wd):
        sleep(random.uniform(0.1, 0.5))
        update_status_info(f"Camera image extraction from {ip} to {wd}")


    def main_calibration(self):
        
        ip_addres = "1.1.1.1"
        number_pc = 2
        machine_config = 63
        machine_id = 1

        wd = Path.cwd() / "utilities"

        update_status_info(f"Starting calibration with ip: {ip_addres}" f" and with {number_pc} number of pcs "  f"And with machine config: {machine_config} on machine: {machine_id}")
        exposuretime_file = wd / "exposuretime.txt"
        device_settings_file = wd / "G_device_settings.ini"
        
        main_ip = ip_addres
        while not self.validate_ip(main_ip):
            main_ip = input("Invalid IP address. Please enter a valid IP: ")

        num_machines = number_pc
        

        config = machine_config
        big_config_bool = config == "90"

        ips = [main_ip]
        for i in range(1, num_machines):
            new_ip = f"{'.'.join(main_ip.split('.')[:-1])}.{int(main_ip.split('.')[-1]) + i}"
            ips.append(new_ip)

        update_status_info(f" IPs: {ips}")


        for ip in ips:
            if self.simulate_ping(ip):
                update_status_info(f" {ip} is reachable.")
            else:
                update_status_error(f" {ip} is NOT reachable.")


        for ip in ips:
            self.simulate_ssh_command(ip, f"ssh-keygen -R {ip}")


        self.simulate_ssh_command(ips[0], f"scp {device_settings_file}")
        self.simulate_ssh_command(ips[0], f"scp QG_device_settings.ini")


        global_d = {}
        global_d["G_settings"] = configparser.ConfigParser()

        if os.path.exists(device_settings_file):
            global_d["G_settings"].read(str(device_settings_file))
            update_status_info(f"Loaded configuration from {device_settings_file}")
        else:
            update_status_error(f"Configuration file {device_settings_file} not found.")

        config_name = "_Farmer"
        machine_id = random.randint(1, 10)
        save_name = f"{config_name}_machine{machine_id}"

        self.clear_directory(wd / "calibration_images")


        for ip in ips:
            self.extract_cam_images(ip, wd)
            


        avg_real_middle_distance = 437 
        result_dict = {"_data": "values"}
        num_images = random.randint(10, 50)
        cam_info = {"cam1": "Camera Data"}
        middel_point_list = [random.randint(50, 150) for _ in range(num_images)]

        for ip in ips:
            self.extract_exposure(ip)

        self.merge_files_in_folder(wd)


        exposuretime_list = self.retrieve_data_from_file(exposuretime_file)


        device_settings_path = wd / "QG_device_settings.ini"
        device_config = configparser.ConfigParser()

        if os.path.exists(device_settings_path):
            device_config.read(str(device_settings_path))
            update_status_info(f" Loaded device settings from {device_settings_path}")
        else:
            update_status_error(f" Device settings file {device_settings_path} not found.")

        device_config["QG_decisions"]["numbofrows"] = "4"
        for index, exposure in enumerate(exposuretime_list):
            section_name = f"QG_Cam{index}"
            if not device_config.has_section(section_name):
                device_config.add_section(section_name)
            device_config[section_name]["exposuretime"] = exposure
            device_config[section_name]["calibrated_exposuretime"] = exposure


        with open(device_settings_path, 'w') as configFile:
            device_config.write(configFile)
            update_status_info(f" Updated settings saved to {device_settings_path}")

        pdf_saved = True 
        update_status_info(f" Generated PDF for {save_name}")

        if len(ips) > 1:
            self.simulate_ssh_command(ips[0], "python3 sync_code_with_slaves.py")
            self.simulate_ssh_command(ips[0], "python3 sync_qg_settings_with_slaves.py")
            self.simulate_ssh_command(ips[0], "python3 sync_g_settings_with_slaves.py")


        now = datetime.now()
        save_dir_base = Path.home() / "_Kalibratie_qualitygrader"
        save_dir = save_dir_base / save_name
        save_dir_QG = save_dir / "QG"
        save_dir_date = save_dir_QG / f"{now.day}_{now.month}_{now.year}"
        save_dir_hour_minute = save_dir_date / f"{now.hour}_{now.minute}"
        save_dir_hour_minute.mkdir(parents=True, exist_ok=True)

        update_status_info(f" Saving results to {save_dir_hour_minute}")

        if pdf_saved:
            update_status_info(" PDF file copied successfully.")
        else:
            update_status_error(" PDF file could not be copied.")

        update_status_info("Simulation complete. All steps executed.")

# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#     fist_calibration = Calibration()

#     calibration_thread = Thread(target=fist_calibration.main_calibration(), daemon=True)
#     calibration_thread.start()
#     calibration_thread.join()
