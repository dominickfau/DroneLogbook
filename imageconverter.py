import os
import base64
import json
from dronelogbook.models import ImageData, Image
from dronelogbook.config import ENCODING_STR


image_folder = os.path.join(os.curdir, "dronelogbook", "drone_geometry", "originals")
output_file = os.path.join(os.curdir, "dronelogbook", "drone_geometry", "imagedata.py")
data = {}

for root, dirs, files in os.walk(image_folder):
    for file in files:
        image_data = Image.convert_to_bytes(os.path.join(root, file)) # type: ImageData
        data[image_data.file_name] = {
            "data": base64.b64encode(image_data.data).decode(ENCODING_STR),
            "file_extension": image_data.file_extension,
            "file_name": image_data.file_name
        }

with open(output_file, 'w') as f:
    f.write(f"data = {json.dumps(data, indent=4)}")