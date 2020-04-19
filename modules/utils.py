import os
import json
from datetime import datetime


# function to set up the folders required and the information file
# Update (-Komal): converted from info.txt -> info.json for improved data retrieval
def set_up_folder(dz_generator, file_name, file_path):
    folder_path = os.path.join(os.path.dirname(os.path.abspath(
        __file__)), '..//output', datetime.now().strftime('%Y-%m-%d %H-%M-%S'))
    os.makedirs(folder_path)

    level_count = dz_generator.level_count
    level_details = []

    for level in range(level_count):
        width, height = dz_generator.level_dimensions[level]
        level_details.append({"Level": level, "Width": width, "Height": height})

    properties = {"File_Name": file_name,
                  "File_Path": file_path,
                  "Level_Count": level_count,
                  "Level_Details": level_details}

    with open(os.path.join(folder_path, 'info.json'), 'w+') as info:
        json.dump(properties, info, indent=4, separators=(',', ': '))
        info.close()

    return folder_path
