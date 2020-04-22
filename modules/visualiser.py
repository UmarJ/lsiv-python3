from app import App
import os
import csv
import Tkinter as tk
from PIL import ImageDraw
import tkSimpleDialog as simpledialog


class Visualiser(App):
    def __init__(self, root_window, deep_zoom_object, level=0):
        self.tiles_directory = root_window.tiles_directory
        # Python 2.x compatible constructor
        App.__init__(self, root_window, deep_zoom_object, self.tiles_directory, level=level)

        # When pressed, toggles the bounding box point removal tool.
        self.toggle_bounding_box_button = tk.Button(self.frame2, text="Bounding\n Box", command=self.toggle_bounding_box_mode)
        self.toggle_bounding_box_button.pack(side=tk.LEFT, padx=(5, 5), pady=(15, 15))
        self.button_original_bg = self.toggle_bounding_box_button.cget("background")

        # When pressed, undoes the most recent deletion.
        self.undo_button = tk.Button(self.frame2, text="Undo", command=self.undo)
        self.undo_button.pack(side=tk.LEFT, padx=(5, 5), pady=(15, 15))

        # When pressed, prompts for new file names of modified CSVs, and saves them.
        save_csv_button = tk.Button(self.frame2, text='Save', command=self.save_modified)
        save_csv_button.pack(side=tk.LEFT, padx=(5, 5), pady=(15, 15))

        # The radius of the ellipse drawn to represent the points.
        self.ellipse_radius = 10
        self.saved_points = self.load_csv_files(self.tiles_directory, self.tile_generator.max_level)

        # Bind left mouse click to removing a point.
        self.canvas.bind('<ButtonPress-1>', self.remove_point)

        # Bind b key to toggling bounding box point removal tool.
        self.canvas.bind('b', self.toggle_bounding_box_mode)

        # Whether the bounding box mode is currently activated.
        self.bb_mode = False

        # A list containing the csv levels that have been modified.
        self.modified_files = []

        # A dictionary where the key is the level and the value is an "undo stack".
        # An undo stack is a list of lists, where each list contains points that were deleted in that step.
        self.undo_stacks = {}

        # Initialize undo stacks to empty lists.
        for level in range(self.tile_generator.max_level):
            self.undo_stacks[level] = []

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
            if current_level in self.saved_points:
                # points that lie within the current selection
                relevant_points = []
                min_x = top_left[0]
                min_y = top_left[1]
                max_x = top_left[0] + image.size[0]
                max_y = top_left[1] + image.size[1]

                level_points = self.saved_points[current_level]
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

        # None is returned if the key does not exist in the dictionary.
        level_points = self.saved_points.get(current_level)

        if level_points is not None:
            # x and y coordinates of the point on the slide
            x_on_slide = self.canvas.canvasx(event.x)
            y_on_slide = self.canvas.canvasy(event.y)

            for x, y in level_points:
                # Check if the click is within the radius of any gaze point.
                # TODO: Look for closest point if there are multiple points in range.
                if abs(x_on_slide - x) <= self.ellipse_radius and abs(y_on_slide - y) <= self.ellipse_radius:
                    level_points.remove((x, y))
                    self.push_points([(x, y)])
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

    def get_names_for_modified(self, modified_levels):

        file_names = {}

        for level in modified_levels:
            new_name = simpledialog.askstring("Enter Name", "Enter new name for CSV for Level {}. "
                                                            "Leave empty to overwrite saved file.".format(level))

            # If the string is empty, overwrite the saved csv file.
            if not new_name:
                new_name = "Level " + str(level)
            file_names[level] = new_name

        return file_names

    def save_modified(self):

        # If array is not empty.
        if self.modified_files:
            file_names = self.get_names_for_modified(self.modified_files)

            for level, new_name in file_names.items():
                # The path to the save location of the csv
                csv_path = os.path.join(self.tiles_directory, new_name + ".csv")
                with open(csv_path, 'wb+') as csv_file:
                    writer = csv.writer(csv_file, delimiter=',')
                    writer.writerows(self.saved_points.get(level))

            self.modified_files = []

    # event=None is needed because binding to a button does not generate an event
    def toggle_bounding_box_mode(self, event=None):
        # Resets the bindings to normal if bounding box mode was active before.
        if self.bb_mode:
            # Bind left mouse click to removing a point.
            self.canvas.bind("<ButtonPress-1>", self.remove_point)
            # Move canvas to the new position using the anchor.
            self.canvas.bind("<B1-Motion>", self.move_to)
            self.canvas.unbind("<ButtonRelease-1>")
            self.toggle_bounding_box_button.config(bg=self.button_original_bg)
            self.bb_mode = False
        else:
            self.activate_bb_mode()
            self.toggle_bounding_box_button.config(bg='gray60')
            self.bb_mode = True

    # The visualiser goes into "bounding box mode", where bounding boxes can be drawn to remove points.
    # event=None is needed because binding to a button does not generate an event
    def activate_bb_mode(self):
        self.canvas.bind("<ButtonPress-1>", self.bb_left_mouse_press)
        self.canvas.bind("<B1-Motion>", self.bb_mouse_motion)
        self.canvas.bind("<ButtonRelease-1>", self.bb_mouse_release)

    def bb_left_mouse_press(self, event):
        # x and y coordinates of the point on the slide.
        self.bb_start_x = self.canvas.canvasx(event.x)
        self.bb_start_y = self.canvas.canvasy(event.y)

        # Create the rectangle for the bounding box.
        self.bb_rectangle = self.canvas.create_rectangle(self.bb_start_x, self.bb_start_y, self.bb_start_x,
                                                         self.bb_start_y, fill='', outline="green")

    def bb_mouse_motion(self, event):
        # x and y coordinates of the current position of the mouse on the slide.
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # Change the dimensions of the bounding box rectangle.
        self.canvas.coords(self.bb_rectangle, self.bb_start_x, self.bb_start_y, x, y)

    def bb_mouse_release(self, event):
        # x and y coordinates of the position where the mouse was released on the slide.
        final_x = self.canvas.canvasx(event.x)
        final_y = self.canvas.canvasy(event.y)

        # List of points that have been removed.
        points_removed = self.remove_points_between_bounds(self.bb_start_x, self.bb_start_y, final_x, final_y)

        # If points were removed, we need to redraw the image since there are now less points.
        if points_removed:
            self.push_points(points_removed)
            self.draw_image_on_canvas(force_generation=True)

        # If no points were removed, we only need to delete the rectangle.
        else:
            self.canvas.delete(self.bb_rectangle)

    def remove_points_between_bounds(self, x1, y1, x2, y2):

        # List of points that have to be removed.
        points_to_remove = []

        # Change the current representation into top-left coordinates and bottom-right coordinates.

        # This function could probably be made neater.

        # The lesser of the two is the x-coordinate of the top left pixel.
        if x1 < x2:
            top_left_x = x1
        else:
            top_left_x = x2

        bottom_right_x = top_left_x + abs(x2 - x1)

        # The lesser of the two is the y-coordinate of the top left pixel.
        if y1 < y2:
            top_left_y = y1
        else:
            top_left_y = y2

        bottom_right_y = top_left_y + abs(y2 - y1)

        current_level = self.tile_generator.level

        # None is returned if the key does not exist in the dictionary.
        level_points = self.saved_points.get(current_level)

        if level_points is not None:
            for x, y in level_points:
                # Check if the current point is within the range of the bounding box.
                # A separate list is used since iteration is messed up if removing while iterating.
                if x >= top_left_x and x <= bottom_right_x and y >= top_left_y and y <= bottom_right_y:
                    points_to_remove.append((x, y))

                    # If the current level has not been modified before, add it to the list of modified levels.
                    if current_level not in self.modified_files:
                        self.modified_files.append(current_level)

        # If points were removed, then remove them from the list using a comprehension.
        # A better solution could be found.
        if points_to_remove:
            level_points[:] = [point for point in level_points if point not in points_to_remove]

        return points_to_remove

    def push_points(self, points):
        """Pushes points onto the current level's undo stack.

        Args:
            points: A list of points, where each point is an x, y coordinate pair.
        """
        current_level_stack = self.undo_stacks[self.tile_generator.level]
        current_level_stack.append(points)

    # Pops and returns the most recently pushed list of points from the current level's undo stack.
    def pop_points(self):
        current_level_stack = self.undo_stacks[self.tile_generator.level]

        # Only pop if the stack is not empty.
        if current_level_stack:
            return current_level_stack.pop()
        else:
            return None

    def undo(self):
        # Pop points.
        points = self.pop_points()

        current_level = self.tile_generator.level

        # If a list is returned, merge it with the current level's saved points.
        if points:
            self.saved_points[current_level] += points

            # Note: Modified files might not always be accurate
            # since an undo could be returning it to an unmodified state.
            if current_level not in self.modified_files:
                self.modified_files.append(current_level)
            self.draw_image_on_canvas(force_generation=True)
