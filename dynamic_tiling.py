import os
import numpy as np
import stitch
from functools import partial
from threading import Thread


class DynamicTiling:

    def __init__(self, deep_zoom_object, level, frame_width, frame_height, folder_path):
        self.deep_zoom = deep_zoom_object
        self.max_level = deep_zoom_object.level_count
        self.level = level
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.file_extension = '.jpeg'
        self.images_width, self.images_height = self.get_file_details()
        self.folder_path = folder_path
        self.tiles_folder_path = os.path.join(folder_path, 'tiles')
        self.level_path = os.path.join(self.tiles_folder_path, str(level))
        self.tiles_generated = {}

        os.makedirs(self.level_path)

    def get_dim(self):
        return self.deep_zoom.level_dimensions[self.level]

    def get_file_details(self):

        self.columns, self.rows = self.deep_zoom.level_tiles[self.level]
        images_width = np.zeros((self.columns, self.rows), dtype=np.int32)
        images_height = np.zeros((self.columns, self.rows), dtype=np.int32)

        width, height = self.deep_zoom.get_tile_dimensions(
            self.level, (0, 0))  # top left tile
        self.first_column_width = width
        self.first_row_height = height

        # the if is needed for images where there is only one tile, (0, 0)
        if self.columns > 1 and self.rows > 1:

            width, height = self.deep_zoom.get_tile_dimensions(self.level, (1, 1))
            self.column_width = width
            self.row_height = height
            images_width[:, :] = width
            images_height[:, :] = height
        else:
            self.column_width = self.first_column_width
            self.row_height = self.first_row_height

        images_width[:, 0] = width
        images_height[0, :] = height

        width, height = self.deep_zoom.get_tile_dimensions(
            self.level, (self.columns - 1, self.rows - 1))  # bottom right tile

        images_width[:, -1] = width
        images_height[-1, :] = height

        return images_width, images_height

    def generate_image(self, image_bounds, previous_top_left):

        left_column = image_bounds[0]

        if left_column < 0:
            left_column = 0

        first_column = 0
        if left_column >= self.first_column_width:
            first_column += 1
            left_column -= self.first_column_width
        first_column += int(left_column // self.column_width)

        right_column = image_bounds[2]
        # the 1 is added because of the first column
        last_column = int(
            (right_column - self.first_column_width) // self.column_width) + 1
        if last_column >= self.columns:
            last_column = self.columns - 1

        top_row = image_bounds[1]

        if top_row < 0:
            top_row = 0

        first_row = 0
        if top_row >= self.first_row_height:
            first_row += 1
            top_row -= self.first_row_height
        first_row += int(top_row // self.row_height)

        bottom_row = image_bounds[3]
        # the 1 is added because of the first row
        last_row = int((bottom_row - self.first_row_height) // self.row_height) + 1
        if last_row >= self.rows:
            last_row = self.rows - 1

        top_left = (0, 0)

        if first_column != 0:
            top_left = (self.first_column_width + (first_column - 1) * self.column_width, top_left[1])

        if first_row != 0:
            top_left = (top_left[0], self.first_row_height + (first_row - 1) * self.row_height)

        if top_left == previous_top_left and top_left != (0, 0):
            return None, top_left

        img = self.stitch_parts(first_column, last_column, first_row, last_row)

        return img, top_left

    def stitch_parts(self, first_column, last_column, first_row, last_row):

        files_list = [str(column) + '_' + str(row) + self.file_extension
                      for column in range(first_column, last_column + 1)
                      for row in range(first_row, last_row + 1)]
        self.generate_with_threads(self.level_path, files_list, num_threads=3)

        files_list = split_list(files_list, last_column - first_column + 1)

        image_columns = []
        for column in files_list:
            image_columns.append(stitch.join_vertically(self.level_path, column))
        img = stitch.join_horizontally(image_columns)

        return img

    def generate_with_threads(self, path, file_names, num_threads=1):
        # split the file names into 'thread' parts
        file_names = split_list(file_names, num_threads)
        threads = []

        for i in range(num_threads):
            # create a thread with a partial function
            t = Thread(target=partial(self.generate_tiles, path, file_names[i]))
            t.start()  # start the thread
            threads.append(t)

        for t in threads:  # call to join is blocked until the thread finishes execution
            t.join()

    def generate_tiles(self, path, file_names):
        current_level_tiles = self.tiles_generated.setdefault(self.level, [])
        for file in file_names:
            if not os.path.isfile(os.path.join(self.level_path, file)):
                column, row = file.split('_')
                row = row.split('.')[0]
                current_level_tiles.append((int(row), int(column)))
                image = self.deep_zoom.get_tile(self.level, (int(column), int(row)))
                image.save(os.path.join(path, file), "JPEG")

    def change_level(self, new_level):
        if new_level < self.max_level and new_level >= 0:
            self.level = new_level
            print("Now on level: {}".format(new_level))

            new_path = os.path.join(self.tiles_folder_path, str(new_level))

            if not os.path.isdir(new_path):
                os.mkdir(new_path)

            self.level_path = new_path
            self.images_width, self.images_height = self.get_file_details()


def split_list(input_list, parts):
    part_length = len(input_list) // parts
    output_list = []
    # iterate to 1 less so that remaining elements can be appended at the end
    for i in range(parts - 1):
        output_list.append(input_list[i * part_length: (i + 1) * part_length])
    # append what is left of the list
    output_list.append(input_list[(parts - 1) * part_length:])
    return(output_list)
