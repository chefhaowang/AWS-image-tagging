import base64
import cv2
import numpy as np


def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

# Example usage:
image_path = ''
encoded_image = encode_image_to_base64(image_path)


