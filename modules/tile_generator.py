import sys
import os
from openslide import open_slide
from openslide.deepzoom import DeepZoomGenerator
import re

def listen_and_generate(file_path, current_level, current_level_path):
    slide = open_slide(file_path)
    deep_zoom = DeepZoomGenerator(slide)

    while True:
        file_list = sys.stdin.readline().strip()
        file_list = file_list.split(';')

        for file in file_list:
            if not os.path.isfile(os.path.join(current_level_path, file)):
                column, row = file.split('_')
                row = row.split('.')[0]
                
                image = deep_zoom.get_tile(current_level, (int(column), int(row)))
                
                image.save(os.path.join(current_level_path, file), "JPEG")
        sys.stdout.write("\n")
        sys.stdout.flush()


if __name__ =='__main__':
    file_path = sys.stdin.readline().strip()
    current_level = int(sys.stdin.readline().strip())
    current_level_path = sys.stdin.readline().strip()
    listen_and_generate(file_path, current_level, current_level_path)

else:
    pass
