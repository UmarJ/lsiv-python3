import sys
import os
from openslide import open_slide
from openslide.deepzoom import DeepZoomGenerator
import re
from numpy import round

def listen_and_generate(file_path, current_level, current_level_path):
    slide = open_slide(file_path)
    deep_zoom = DeepZoomGenerator(slide)
    
    #count starts from 0
    max_level = deep_zoom.level_count-1
    max_tile_dimensions = deep_zoom.level_dimensions[max_level]
    current_level_dimensions = deep_zoom.level_dimensions[current_level]

    downsample = round(max_tile_dimensions[0]/current_level_dimensions[0])


    while True:
        file_list = sys.stdin.readline().strip()
        file_list = file_list.split(';')

        for file in file_list:
            if not os.path.isfile(os.path.join(current_level_path, file)):
                column, row = file.split('_')
                row,extension = row.split('.')
                image = deep_zoom.get_tile(current_level, (int(column), int(row)))
                x_coord,y_coord = deep_zoom.get_tile_coordinates(current_level,(int(column),int(row)))[0]
                x_coord, y_coord = int(x_coord/downsample), int(y_coord/downsample)

                #image.save(os.path.join(current_level_path, file), "JPEG")
                image.save(os.path.join(current_level_path, str(column)+"_"+str(row)+"-"+str(x_coord)+"_"+str(y_coord)+"."+extension), "JPEG")
        sys.stdout.write("\n")
        sys.stdout.flush()


if __name__ =='__main__':
    file_path = sys.stdin.readline().strip()
    current_level = int(sys.stdin.readline().strip())
    current_level_path = sys.stdin.readline().strip()
    listen_and_generate(file_path, current_level, current_level_path)

else:
    pass
