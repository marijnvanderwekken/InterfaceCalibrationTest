
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
        folder_path = os.getcwd() + ""

        if os.path.exists(folder_path):
            all_files = os.listdir(folder_path)
            pattern = r'cam\d+_output\.jpg'
            image_files = [file for file in all_files if re.match(pattern, file)]
            num_images = len(image_files)
            print(f'Total number of images matching the pattern: {num_images}')
        else:
            print('The specified directory does not exist.')

        images = []

        for i in range(0, num_images):
            image_name = f'cam{i}_output.jpg'
            image_path = os.path.join(folder_path, image_name)

            if os.path.exists(image_path):
                img = cv2.imread(image_path)
                images.append(img)

        height, width, _ = images[0].shape
        combined_image = np.zeros((height, (width + 1) * num_images - 1, 3), dtype=np.uint8)

        for i, img in enumerate(images):
            combined_image[:, i * (width + 1):i * (width + 1) + width, :] = img

        for i in range(1, num_images):
            cv2.line(combined_image, (i * (width + 1) - 1, 0), (i * (width + 1) - 1, height), (255, 255, 255), 5)

        combined_image_path = os.path.join(folder_path, 'combined_image.jpg')
        cv2.putText(combined_image, f'Calibrated Center Y Line: {437} mm', (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        cv2.imwrite(combined_image_path, combined_image)
        print("Combined image saved as 'combined_image.jpg' in the same folder.")
        
