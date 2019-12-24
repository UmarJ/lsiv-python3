import os.path
from PIL import Image
import subprocess
import pandas as pd


def stitch_images(deep_zoom_object, tiles_generated, folder_path):

    tiles_folder_path = folder_path + 'tiles/'

    for level, images in tiles_generated.items():

        if not os.path.isfile(folder_path + "Level " + str(level) + ".csv"):
            print("No csv for Level: ".format(level))
            continue

        current_level_path = tiles_folder_path + str(level) + '/'

        img_name = "Level " + str(level) + ".png"
        csv_name = "Level " + str(level) + ".csv"

        sorted_by_row = sorted(images, key=lambda tup: tup[0])
        first_row = sorted_by_row[0][0]
        row_count = sorted_by_row[-1][0] - first_row

        sorted_by_column = sorted(images, key=lambda tup: tup[1])
        first_column = sorted_by_column[0][1]
        column_count = sorted_by_column[-1][1] - first_column

        first_column_width, first_row_height = deep_zoom_object.get_tile_dimensions(level, (0, 0))
        column_width, row_height = (0, 0)

        if column_count > 0 and row_count > 0:
            column_width, row_height = deep_zoom_object.get_tile_dimensions(level, (1, 1))

        first_index = first_column, first_row
        count = column_count, row_count
        dimensions = column_width, row_height
        first_dimensions = first_column_width, first_row_height

        final_img = construct_image(
            current_level_path, images, first_index, count, dimensions, first_dimensions, deep_zoom_object, level)
        size = final_img.size[0], final_img.size[1]
        print("Old Size: {}".format(size))

        scaling_factor = 1
        max_size = 5000, 5000

        if size[0] > max_size[0] or size[1] > max_size[1]:
            scaling_factor = max(size[0] / max_size[0], size[1] / max_size[1])
            print("Scaling Factor is {}".format(scaling_factor))
            df = pd.read_csv(folder_path + csv_name,
                             delimiter=',', header=None)
            # gazeheatplot requires ints
            df[0] = df[0] // scaling_factor
            df[1] = df[1] // scaling_factor
            csv_name = csv_name.split('.')[0] + ' Rescaled' + '.csv'
            df.to_csv(folder_path + csv_name, sep=',',
                      index=False, header=False)

        final_img = final_img.resize(
            (int(size[0] / scaling_factor), int(size[1] / scaling_factor)), Image.ANTIALIAS)
        print("New Size: {}".format(final_img.size))

        heatmap_name = "Heatmap " + img_name
        # https://pillow.readthedocs.io/en/5.1.x/handbook/image-file-formats.html
        final_img.save(folder_path + img_name, quality=95)
        print("Generating Heatmap for Level: {}".format(level))
        gazeheatplot_path = os.path.dirname(os.path.abspath(
            __file__)) + "/GazePointHeatMap/gazeheatplot.py"
        subprocess.call(["python", gazeheatplot_path, folder_path + csv_name, str(final_img.size[0]),
                         str(final_img.size[1]),
                         "-a 0.6", "-o" + heatmap_name, "-b" + folder_path + img_name, "-n 200"])
        # -sd 20 to be added later

        # if the heatmap is not found in the folder then it must be in directory the python subprocess was called from
        if not os.path.isfile(folder_path + heatmap_name):
            os.rename(heatmap_name, folder_path + heatmap_name)

        print("Heatmap saved as {}".format('Heatmap ' + img_name))

# if no deep_zoom_object is passed, the area where no tiles are needed will be black
def construct_image(path, files, first_index, count, dimensions, first_dimensions, deep_zoom_object=None, level=0):

    first_column, first_row = first_index
    column_count, row_count = count
    column_width, row_height = dimensions
    first_column_width, first_row_height = first_dimensions

    print(first_index)
    print(count)
    print(dimensions)
    print(first_dimensions)

    image_width = 0
    image_height = 0

    if first_column == 0:
        image_width += first_column_width
        column_count -= 1
    if first_row == 0:
        image_height += first_row_height
        row_count -= 1

    image_width += column_count * column_width
    image_height += row_count * row_height

    result = Image.new('RGB', (image_width, image_height))
    print(result.size)

    current_x = 0
    current_y = 0

    for column in range(first_column, first_column + column_count):
        for row in range(first_row, first_row + row_count):
            if (row, column) in files:
                tile_name = str(column) + '_' + str(row) + '.jpeg'
                print("Found: " + tile_name)
                tile = Image.open(path + tile_name)
                result.paste(im=tile, box=(current_x, current_y))
            elif deep_zoom_object is not None:
                tile = deep_zoom_object.get_tile(level, (column, row))
                result.paste(im=tile, box=(current_x, current_y))

            current_y += tile.size[1]
        current_y = 0
        current_x += tile.size[0]

    return result
