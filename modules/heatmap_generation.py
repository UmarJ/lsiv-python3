import os
from PIL import Image
import subprocess
import pandas as pd
import argparse
from openslide import open_slide
from openslide.deepzoom import DeepZoomGenerator


def generate_heatmap(deep_zoom_object, folder_path, gaussian_matrix_size, map_type="heatmap", alpha = 0.6,  include_unvisited_tiles=True):

    tiles_folder_path = os.path.join(folder_path, 'tiles')

    for level in range(deep_zoom_object.level_count):

        if not os.path.isfile(os.path.join(folder_path, "Level " + str(level) + ".csv")):
            print("No CSV for Level {}".format(level))
            continue

        # path to the directory pointing to this level's tiles
        current_level_path = os.path.join(tiles_folder_path, str(level))
        if not os.path.exists(current_level_path):
            os.makedirs(current_level_path)

        img_name = "Level " + str(level) + ".png"
        csv_name = "Level " + str(level) + ".csv"

        # tiles that were generated previously
        present_tiles = []

        files = os.listdir(current_level_path)

        if not files:
            include_unvisited_tiles = True

        for i in files:
            # first split to separate the extension, then split row/column
            column, row = i.split('.')[0].split('_')
            present_tiles.append((int(column), int(row)))

        # if unvisited tiles are to be included, then the entire area from top-left to bottom right needs to be covered
        if include_unvisited_tiles:
            first_row, first_column = (0, 0)
            column_count, row_count = deep_zoom_object.level_tiles[level]

        # only previously generated tiles are used for heatmap generation
        else:
            sorted_by_row = sorted(present_tiles, key=lambda tup: tup[0])
            first_row = sorted_by_row[0][0]
            row_count = sorted_by_row[-1][0] - first_row

            sorted_by_column = sorted(present_tiles, key=lambda tup: tup[1])
            first_column = sorted_by_column[0][1]
            column_count = sorted_by_column[-1][1] - first_column

        # first column/row may have a different width/height than other tiles, if they are the first in that level
        if first_column == 0:
            first_column_width, _ = deep_zoom_object.get_tile_dimensions(level, (0, 0))
        else:
            first_column_width, _ = deep_zoom_object.get_tile_dimensions(level, (1, 1))

        if first_row == 0:
            _, first_row_height = deep_zoom_object.get_tile_dimensions(level, (0, 0))
        else:
            _, first_row_height = deep_zoom_object.get_tile_dimensions(level, (1, 1))

        column_width, row_height = (0, 0)
        # column width and row height is only relevant when more than one column is required
        if column_count > 1 and row_count > 1:
            column_width, row_height = deep_zoom_object.get_tile_dimensions(level, (1, 1))
        elif column_count >1 or row_count > 1:
            column_width, row_height = deep_zoom_object.get_tile_dimensions(level, (column_count-1, row_count-1))


        first_index = first_column, first_row
        count = column_count, row_count
        dimensions = column_width, row_height
        first_dimensions = first_column_width, first_row_height

        final_img = construct_image(current_level_path, present_tiles,
                                    first_index, count, dimensions, first_dimensions, deep_zoom_object, level)
        size = final_img.size[0], final_img.size[1]
        print("Old Size: {}".format(size))

        scaling_factor = 1
        max_size = 5000, 5000

        if size[0] > max_size[0] or size[1] > max_size[1]:
            scaling_factor = max(size[0] / max_size[0], size[1] / max_size[1])
            print("Scaling Factor is {}".format(scaling_factor))
            df = pd.read_csv(os.path.join(folder_path, csv_name),
                             delimiter=',', header=None)
            # gazeheatplot requires ints
            df[0] = df[0] // scaling_factor
            df[1] = df[1] // scaling_factor
            csv_name = csv_name.split('.')[0] + ' Rescaled' + '.csv'
            df.to_csv(os.path.join(folder_path, csv_name), sep=',',
                      index=False, header=False)

        final_img = final_img.resize(
            (int(size[0] / scaling_factor), int(size[1] / scaling_factor)), Image.ANTIALIAS)
        print("New Size: {}".format(final_img.size))

        if map_type == "binarymap":
            heatmap_name = "Binarymap " + img_name
        else:
            heatmap_name = "Heatmap " + img_name

        # https://pillow.readthedocs.io/en/5.1.x/handbook/image-file-formats.html
        final_img.save(os.path.join(folder_path, img_name), quality=95)
        print("Generating map for Level {}".format(level))
        gazeheatplot_path = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), "..//GazePointHeatMap", "gazeheatplot.py")
        subprocess.call(["python", gazeheatplot_path, os.path.join(folder_path, csv_name), str(final_img.size[0]),
                         str(final_img.size[1]),
                         "-a " + str(alpha), "-o" + os.path.join(folder_path,heatmap_name), "-b" + os.path.join(folder_path, img_name),
                         "-n" + gaussian_matrix_size, "-m" + map_type])
        # -sd 20 to be added later

        # if the heatmap is not found in the folder then it must be in directory the python subprocess was called from
        if not os.path.isfile(os.path.join(folder_path, heatmap_name)):
            try:
                os.rename(heatmap_name, os.path.join(folder_path, heatmap_name))
            # this exception is thrown when the heatmap was not generated for some reason
            except IOError:
                print("Error while generating map for Level {}".format(level))
                continue

        print("Map saved as {}".format(map_type + " " + img_name))


# if no deep_zoom_object is passed, the area where no tiles are needed will be black
def construct_image(tiles_directory, present_tiles, first_index, count, dimensions, first_dimensions,
                    deep_zoom_object=None, level=0):

    first_column, first_row = first_index
    column_count, row_count = count
    column_width, row_height = dimensions
    first_column_width, first_row_height = first_dimensions

    image_width = 0
    image_height = 0

    # first column/row have a different width/height than other tiles

    if first_column == 0:
        image_width += first_column_width
        column_count -= 1
    if first_row == 0:
        image_height += first_row_height
        row_count -= 1

    image_width += column_count * column_width
    image_height += row_count * row_height

    result = Image.new('RGB', (image_width, image_height))

    current_x = 0
    current_y = 0




    for column in range(first_column, first_column + column_count + 1):
        prev = 0
        current_y = 0
        for row in range(first_row, first_row + row_count + 1):


            if (column, row) in present_tiles:
                tile_name = str(column) + '_' + str(row) + '.jpeg'

                tile = Image.open(os.path.join(tiles_directory, tile_name))
                result.paste(im=tile, box=(current_x, current_y))

            # if the tile has not been generated previously, then  generate the tile
            elif deep_zoom_object is not None:
                tile = deep_zoom_object.get_tile(level, (column, row))
                result.paste(im=tile, box=(current_x, current_y))

            current_y += tile.size[1]
            prev = tile.size[0]
        current_x +=prev
            
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("svs", help="Path to the SVS file.")
    parser.add_argument("lsiv_output", help="Path to the folder containing the CSV file and generated tiles directory.")
    args = parser.parse_args()
    svs_path = os.path.abspath(args.svs)
    lsiv_output_path = os.path.abspath(args.lsiv_output)
    # svs_path = "C:/Users/smart/Documents/Projects/lsiv-python3/62893.svs"
    # lsiv_output_path = "C:/Users/smart/Documents/Projects/lsiv-python3/2020-03-19 15-35-27"

    generate_heatmap(DeepZoomGenerator(open_slide(svs_path)), lsiv_output_path)
