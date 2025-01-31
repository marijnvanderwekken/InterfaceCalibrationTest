

from threading import Thread
import logging
import os
import base64
import cv2
import re
import numpy as np

class ImageHandler:
    def __init__(self):
        self.save_dir = "decoded_images"
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    async def save_base64_images(self, image_list):
        if not image_list:
            logging.warning("Received empty image list")
            return

        logging.info(f"Saving {len(image_list)} images")
        for i, image_data in enumerate(image_list):
            try:
                if not image_data.strip():
                    logging.info(f"Skipping empty image {i}")
                    continue
                image_bytes = base64.b64decode(image_data)
                file_path = os.path.join(self.save_dir, f"cam{i}_output.jpg")
                with open(file_path, "wb") as image_file:
                    image_file.write(image_bytes)
                logging.info(f"Saved image {i+1} to {file_path}")
            except Exception as e:
                logging.error(f"Error saving image {i+1}: {e}")

    def prepare_image(self):
        combined_image_path = self.combine_images_from_folder()
        if not combined_image_path:
            return ""
        try:
            with open(combined_image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
        except Exception as e:
            logging.error(f"Error opening file: {e}")
            return ""

    def combine_images_from_folder(self):
        folder_path = self.save_dir
        pattern = r'cam\d+_output\.jpg'
        image_files = sorted([file for file in os.listdir(folder_path) if re.match(pattern, file)])

        if not image_files:
            logging.warning("No images found to combine")
            return None

        images = [cv2.imread(os.path.join(folder_path, img)) for img in image_files]
        if not images:
            logging.warning("Failed to load images")
            return None

        height, width, _ = images[0].shape
        combined_width = sum(img.shape[1] for img in images) + len(images) - 1
        combined_image = np.zeros((height, combined_width, 3), dtype=np.uint8)

        x_offset = 0
        for img in images:
            combined_image[:, x_offset:x_offset + img.shape[1], :] = img
            x_offset += img.shape[1] + 1

        combined_image_path = os.path.join(folder_path, 'combined_image.jpg')
        cv2.imwrite(combined_image_path, combined_image)
        logging.info(f"Saved combined image as {combined_image_path}")
        return combined_image_path