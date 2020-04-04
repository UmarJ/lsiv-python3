from app import App
import os
import csv
from PIL import ImageDraw


class Visualiser(App):
    def __init__(self, root_window, deep_zoom_object, level=0):
        self.tiles_directory = root_window.tiles_directory
        # Python 2.x compatible constructor
        App.__init__(self, root_window, deep_zoom_object, self.tiles_directory, level=level)
        # The radius of the ellipse drawn to represent the points.
        self.ellipse_radius = 10
        self.saved_csv_files = self.load_csv_files(self.tiles_directory, self.tile_generator.max_level)
        self.canvas.bind('<ButtonPress-1>', self.remove_point)

        # A list containing the csv levels that have been modified.
        self.modified_files = []

        # Draw initial image.
        self.draw_image_on_canvas()

    def get_image(self, box_coords, force_generation=False):
        image, top_left = self.tile_generator.generate_image(box_coords, self.top_left,
                                                             force_generation=force_generation)

        # if image is None, then it's the same as before and no processing needs to be done
        if image is None:
            return image, top_left

        else:
            current_level = self.tile_generator.level

            # if there is no saved csv, the image is returned without changes
            if current_level in self.saved_csv_files:
                # points that lie within the current selection
                relevant_points = []
                min_x = top_left[0]
                min_y = top_left[1]
                max_x = top_left[0] + image.size[0]
                max_y = top_left[1] + image.size[1]

                level_points = self.saved_csv_files[current_level]
                for x, y in level_points:
                    # If the point is within the range covered by the image.
                    if x > min_x and y > min_y and x < max_x and y < max_y:
                        # min_x and min_y are subtracted so that the resulting points are coordinates on the image,
                        # instead of on the whole svs file.
                        relevant_points.append((x - min_x, y - min_y))

                draw = ImageDraw.Draw(image)
                for x, y in relevant_points:
                    # top left of the ellipse cannot be less than the size of the image
                    ellipse_top_left = max(0, x - self.ellipse_radius), max(0, y - self.ellipse_radius)

                    # bottom right of the ellopse cannot exceed the size of the image
                    ellipse_bottom_right = min(image.size[0], x + self.ellipse_radius), min(image.size[1], y + self.ellipse_radius)

                    # draw a green ellipse
                    draw.ellipse([ellipse_top_left, ellipse_bottom_right], fill=(0, 255, 0, 255))

                return image, top_left
            else:
                return image, top_left

    def remove_point(self, event):
        # move_from needs to be called first, in case the user is just looking around and not removing.
        self.move_from(event)
        current_level = self.tile_generator.level
        level_points = self.saved_csv_files.get(current_level)

        # None is returned if the key does not exist in the dictionary.
        if level_points is not None:
            # x and y coordinates of the point on the slide
            x_on_slide = self.canvas.canvasx(event.x)
            y_on_slide = self.canvas.canvasy(event.y)

            for x, y in level_points:
                # Check if the click is within the radius of any gaze point.
                # TODO: Look for closes point if there are multiple points in range.
                if abs(x_on_slide - x) <= self.ellipse_radius and abs(y_on_slide - y) <= self.ellipse_radius:
                    level_points.remove((x, y))
                    self.draw_image_on_canvas(force_generation=True)

                    # If the current level has not been modified before, add it to the list of modified levels.
                    if current_level not in self.modified_files:
                        self.modified_files.append(current_level)
                    break

    def load_csv_files(self, directory, levels):
        csv_files = {}
        for level in range(levels):
            # list containing this level's points
            level_points = []

            # The path to the csv, which may or may not exist.
            csv_path = os.path.join(self.tiles_directory, "Level " + str(level) + ".csv")

            # Open the file if it exists and load the points to an array.
            if os.path.isfile(csv_path):
                with open(csv_path) as points_file:
                    for x, y in csv.reader(points_file, delimiter=','):
                        level_points.append((int(x), int(y)))

                # Add the points to the dictionary.
                csv_files[level] = level_points

        return csv_files
