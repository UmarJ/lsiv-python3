import os
import time
gp = __import__("gazepoint.gazepoint")


def main(interface, resolution):
    # Gazepoint Control must be opened for tracking to work
    print("Import successful")
    gazetracker = gp.gazepoint.GazePoint()
    tile_generator = interface.tile_generator
    canvas = interface.canvas
    box_coords = interface.box_coords
    folder_path = tile_generator.folder_path

    current_level = tile_generator.level
    previous_level = current_level

    canvas_start_x = canvas.winfo_rootx()
    canvas_start_y = canvas.winfo_rooty()
    canvas_end_x = canvas_start_x + canvas.winfo_reqwidth()
    canvas_end_y = canvas_start_y + canvas.winfo_reqheight()

    csv_output = open(os.path.join(folder_path, "Level " + str(current_level) + ".csv"), "a")

    while interface.is_tracking:
        box_coords = interface.box_coords
        previous_level = current_level
        current_level = tile_generator.level

        # if the level changes, close the old csv and open a new csv file
        if previous_level != current_level:
            csv_output.close()
            csv_output = open(os.path.join(folder_path, "Level " + str(current_level) + ".csv"), "a")

        x, y = gazetracker.get_gaze_position()
        # returns a tuple with a value between 0 and 1, can also be negative if looking outside the screen
        if x is not None and y is not None:
            x *= resolution[0]
            y *= resolution[1]

            if x >= canvas_start_x and y >= canvas_start_y and x <= canvas_end_x and y <= canvas_end_y:
                # position of canvas on screen is subtracted so that
                # we can consider the top left of the viewer as the origin
                x = x - canvas_start_x + box_coords[0]
                y = y - canvas_start_y + box_coords[1]
                csv_output.write(str(int(x)) + "," + str(int(y)) + "\n")

        time.sleep(0.1)

    csv_output.close()
    gazetracker.stop()
