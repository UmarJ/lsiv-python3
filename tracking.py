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

    csv_output = open(folder_path + "Level " + str(current_level) + ".csv", "a")

    while interface.is_tracking:
        box_coords = interface.box_coords
        previous_level = current_level
        current_level = tile_generator.level

        if previous_level != current_level:
            csv_output.close()
            csv_output = open(folder_path + "Level " + str(current_level) + ".csv", "a")

        try:
            canvas_x = canvas.winfo_rootx()
        except:
            print("ERROR X")
            canvas_x = 0
        try:
            canvas_y = canvas.winfo_rooty()
        except:
            print("ERROR Y")
            canvas_y = 0

        print("box coords {}".format(box_coords))
        print("current level {}".format(tile_generator.level))
        x, y = gazetracker.get_gaze_position()
        # returns a tuple with a value between 0 and 1, can also be negative if looking outside the screen
        if x is not None and y is not None:
            x *= resolution[0]
            y *= resolution[1]

            if x >= canvas_x and y >= canvas_y:
                # position of canvas on screen is subtracted so that
                # we can consider the top left of the viewer as the origin
                print("Resolution: {}, x: {}, y: {}, canvas_0: {}, canvas_1: {}".format(
                    resolution, x, y, box_coords[0], box_coords[1]))
                print("Can x: {} Can y: {}".format(canvas_x, canvas_y))
                x = x - canvas_x + box_coords[0]
                y = y - canvas_y + box_coords[1]
                csv_output.write(str(int(x)) + "," + str(int(y)) + "\n")

        time.sleep(0.1)

    csv_output.close()
    gazetracker.stop()
