import os

# os.add_dll_directory(r'D:\openslide-win32-20171122\bin')
import json
import dynamic_tiling
import tracking
import heatmap_generation
import sys
import csv

import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox
from PIL import ImageTk, ImageDraw
from functools import partial
from openslide import open_slide
from openslide.deepzoom import DeepZoomGenerator
from threading import Thread
from datetime import datetime


class App(tk.Tk):
    def __init__(self, root_window, deep_zoom_object, tiles_folder, level=0):

        self.root_window = root_window

        self.bbox = []
        self.x, self.y = 0, 0

        # x coordinate at top-left, y coordinate at top-left,
        # x coordinate at bottom-right, y coordinate at bottom-right
        box_coords = (0, 0, 0, 0)

        self.root_window.title("Large Scale Image Viewer")
        self.root_window.attributes("-fullscreen", True)
        root.config(bg='gray80')

        self.frame2 = tk.Frame(self.root_window, width=50, height=50)
        self.frame2.config(bg='gray80')
        self.frame2.pack(fill=None, expand=False)

        self.zoomLabel = tk.Label(self.frame2, text=str(level) + "x", bg='gray90', font=("Helvetica", 14), borderwidth=2, relief="groove")
        self.zoomLabel.pack(side=tk.LEFT, padx=(5, 5), pady=(15, 15))

        self.fileLabel = tk.Label(self.frame2, text=str("Source:\n" + root.file_name), bg='gray90', font=("Helvetica", 14), borderwidth=2, relief="groove")
        self.fileLabel.pack(side=tk.LEFT, padx=(5, 5), pady=(15, 15))

        self.buttonClose = tk.Button(self.frame2, font=("Helvetica", 14), text="Close", bg='gray80', command=on_closing)
        self.buttonClose.pack(side=tk.LEFT, padx=(5, 5), pady=(15, 15))

        self.frame = ResizingFrame(self.root_window, self)
        self.frame.config(bg='gray80')
        self.frame.pack(fill=tk.BOTH, expand=tk.YES)

        self.button1 = tk.Button(self.frame, text='Button1')

        self.canvas = tk.Canvas(self.frame, bg="gray90", width=800, height=600)

        # set up the horizontal scroll bar
        self.hbar = tk.Scrollbar(self.frame, orient=tk.HORIZONTAL)
        self.hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.hbar.config(command=self.__scroll_x)

        # set up the vertical scroll bar
        self.vbar = tk.Scrollbar(self.frame, orient=tk.VERTICAL)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.vbar.config(command=self.__scroll_y)

        # remember canvas position
        self.canvas.bind('<ButtonPress-1>', self.move_from)
        # move canvas to the new position
        self.canvas.bind('<B1-Motion>', self.move_to)
        # zoom for Windows and MacOS, but not Linux
        self.canvas.bind_all("<MouseWheel>", self.__wheel)
        # zoom for Linux, wheel scroll up
        self.canvas.bind('<Button-4>', self.__wheelup)
        # zoom for Linux, wheel scroll down
        self.canvas.bind('<Button-5>', self.__wheeldown)

        self.canvas.focus_set()
        self.canvas.bind("b", self.bounding_box)

        self.start_x = None
        self.start_y = None

        self.deep_zoom_object = deep_zoom_object

        # the dynamic tile generator, responsible for providing the image to the canvas to display
        # TODO: The value it is initialized with might not always remain the same
        self.tile_generator = dynamic_tiling.DynamicTiling(
            deep_zoom_object, level, self.canvas.winfo_reqwidth(), self.canvas.winfo_reqheight(), tiles_folder)

        # top left coordinate of the current selection relative to the svs file
        # (-1, -1) is used as the initial value since it cannot occur naturally
        self.top_left = (-1, -1)

        self.set_scroll_region()
        self.canvas.config(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        self.canvas.pack(expand=tk.YES, fill=tk.BOTH, padx=(100, 100), pady=(0, 10))

    def set_scroll_region(self):
        dim = self.tile_generator.get_dim()
        self.canvas.config(scrollregion=(0, 0, dim[0], dim[1]))

    def bounding_box(self, event):
        print(event.char)
        self.deactivate_bindings()
        self.activate_bbox_bindings()

    def activate_bbox_bindings(self):
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def activate_bindings(self):
        # remember canvas position
        self.canvas.bind('<ButtonPress-1>', self.move_from)
        # move canvas to the new position
        self.canvas.bind('<B1-Motion>', self.move_to)

    def deactivate_bindings(self):
        self.canvas.unbind('<ButtonPress-1>')
        self.canvas.unbind('<B1-Motion>')

    def on_button_press(self, event):
        # get coordinates of the event on the canvas
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.start_x = x
        self.start_y = y
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, 1, 1, fill="", outline="green")

    def on_move_press(self, event):
        curX = self.canvas.canvasx(event.x)
        curY = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)

    def on_save_pressed(self, textBox, MainWin):
        box = self.canvas.coords(self.rect)
        self.bbox.append(box)
        print(self.bbox)
        MainWin.destroy()
        file = open("bbox.csv", "a")
        file.write(textBox.get() + "," + str(box[0]) + "," + str(
            box[1]) + "," + str(box[2]) + "," + str(box[3]) + "\n")
        file.close()

    def on_button_release(self, event):
        MainWin = tk.Toplevel()
        MainWin.title("Enter Label")
        MainWin.geometry("150x100")

        lab1 = tk.StringVar()
        tk.Label(MainWin, text="Please Enter ID:").pack()
        e = tk.Entry(MainWin, textvariable=lab1)
        e.pack()
        tk.Button(MainWin, text="Save", width=10, height=1,
                  command=partial(self.on_save_pressed, lab1, MainWin)).pack()

        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.activate_bindings()

    def __scroll_x(self, *args):
        # scroll canvas horizontally and redraw the image
        self.canvas.xview(*args)
        self.draw_image_on_canvas()

    def __scroll_y(self, *args):
        # scroll canvas horizontally and redraw the image
        self.canvas.yview(*args)
        self.draw_image_on_canvas()

    def zoom(self, event, change):
        # get coordinates of the event on the canvas
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        old_dim = self.tile_generator.get_dim()

        # change the level in the tile generator to the new level
        self.tile_generator.change_level(self.tile_generator.level + change)
        self.zoomLabel.config(text=str(self.tile_generator.level) + "x")

        # get new image dimensions after level change
        new_dim = self.tile_generator.get_dim()

        # find the ratio increase/decrease in width and height
        ratio_w = float(new_dim[0]) / float(old_dim[0])
        ratio_h = float(new_dim[1]) / float(old_dim[1])

        # calculate new centre for the mouse after zooming in/out
        centre_x = x * ratio_w
        centre_y = y * ratio_h

        # calculate the new top left for the canvas using the new centre
        canvas_top_left = (max(0, centre_x - (self.frame.width // 2)),
                           max(0, centre_y - (self.frame.height // 2)))

        box_coords = (canvas_top_left[0], canvas_top_left[1],
                      canvas_top_left[0] + self.frame.width, canvas_top_left[1] + self.frame.height)

        # reset the top left
        self.top_left = (-1, -1)

        # the draw_image_on_canvas function cannot be used since this needs to scroll the canvas too
        image, self.top_left = self.get_image(box_coords)

        self.image = ImageTk.PhotoImage(image=image)

        # delete the old image and set the new image
        self.canvas.delete("all")
        self.image_on_canvas = self.canvas.create_image(
            canvas_top_left[0], canvas_top_left[1], image=self.image, anchor="nw")

        scrollbar_x = canvas_top_left[0] / new_dim[0]
        scrollbar_y = canvas_top_left[1] / new_dim[1]

        # set new dimensions as scroll region
        self.canvas.config(scrollregion=(0, 0, new_dim[0], new_dim[1]))

        # move the canvas to the calculated coordinates
        self.canvas.xview_moveto(scrollbar_x)
        self.canvas.yview_moveto(scrollbar_y)

        self.draw_image_on_canvas()

    # zoom for MacOS and Windows
    def __wheel(self, event):
        if event.delta == -120:  # zoom out
            change = -1
        else:  # zoom in
            change = +1

        self.zoom(event, change)

    # zoom in for Linux
    def __wheelup(self, event):
        self.zoom(event, +1)

    # zoom out for Linux
    def __wheeldown(self, event):
        self.zoom(event, -1)

    def move_from(self, event):
        # remember previous coordinates for scrolling with the mouse
        self.canvas.scan_mark(event.x, event.y)

    def move_to(self, event):
        # drag (move) canvas to the new position
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.draw_image_on_canvas()  # redraw the image

    def draw_image_on_canvas(self, force_generation=False):
        """Draws the image on the canvas.

        Args:
            force_generation: Is True if the image should be re-generated even if the bounds are same as before.
        """

        self.canvas_vertex = (self.canvas.canvasx(0), self.canvas.canvasy(0))
        box_coords = (self.canvas_vertex[0], self.canvas_vertex[1],
                      self.canvas_vertex[0] + self.frame.width, self.canvas_vertex[1] + self.frame.height)

        # some weird bug with canvas being 0 when scrolling back to origin
        if box_coords[0] == -1:
            box_coords = (box_coords[0] + 1, box_coords[1], box_coords[2] + 1, box_coords[3])

        if box_coords[1] == -1:
            box_coords = (box_coords[0], box_coords[1] + 1, box_coords[2], box_coords[3] + 1)

        image, self.top_left = self.get_image(box_coords, force_generation=force_generation)

        if image is not None:
            self.canvas.delete("all")

            # this ownership is necessary, or the image does not show up on the canvas
            self.image = ImageTk.PhotoImage(image=image)

            self.image_on_canvas = self.canvas.create_image(
                self.top_left[0], self.top_left[1], image=self.image, anchor="nw")

    # virtual method
    def get_image(self, box_coords):
        raise NotImplementedError()

    def generate_heatmap(self, event):
        heatmap_generation.generate_heatmap(self.deep_zoom_object, self.tile_generator.folder_path)


class Recorder(App):
    def __init__(self, root_window, deep_zoom_object, level=0):
        tiles_folder = set_up_folder(deep_zoom_object)
        # Python 2.x compatible constructor
        App.__init__(self, root_window, deep_zoom_object, tiles_folder, level=level)

        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

        self.imgEyeOff = ImageTk.PhotoImage(file=os.path.join(assets_dir, "icon2xOff.png"))
        self.imgEyeOn = ImageTk.PhotoImage(file=os.path.join(assets_dir, "icon2xOn.png"))

        # TODO: Fix the order of buttons
        self.notificationLabel = tk.Label(self.frame2, text="Gaze Recording Disabled", bg='gray90', font=("Helvetica", 14), borderwidth=2, relief="groove")
        self.notificationLabel.pack(side=tk.LEFT, padx=(5, 5), pady=(15, 15))

        self.gazeToggleButton = tk.Button(self.frame2, fg="red", text="hello", bg='gray80', image=self.imgEyeOff, command=self.start_stop_tracking)
        self.gazeToggleButton.pack(side=tk.LEFT, padx=(15, 15), pady=(15, 15))

        self.canvas.bind("t", self.start_stop_tracking)
        self.canvas.bind("h", self.generate_heatmap)

        # shows whether the gaze tracker is currently tracking
        self.is_tracking = False

    # event=None is needed because binding to a button does not generate an event
    def start_stop_tracking(self, event=None):

        if self.is_tracking:
            self.notificationLabel.configure(text="Gaze Recording Disabled")
            self.gazeToggleButton.configure(image=self.imgEyeOff)
            self.is_tracking = False
        else:
            self.gazeToggleButton.configure(image=self.imgEyeOn)
            self.notificationLabel.configure(text="Gaze Recording in Progress")
            self.is_tracking = True
            resolution = (self.root_window.winfo_screenwidth(),
                          self.root_window.winfo_screenheight()) # a tuple for resolution
            partial_function = partial(tracking.main, self, resolution)
            Thread(target=partial_function).start()

    def get_image(self, box_coords, force_generation=False):
        image, top_left = self.tile_generator.generate_image(box_coords, self.top_left)
        return image, top_left


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


class ResizingFrame(tk.Frame):

    def __init__(self, parent, app, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        self.app = app
        self.bind("<Configure>", self.on_resize)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()

    def on_resize(self, event):
        self.width = event.width
        self.height = event.height
        canvas = self.winfo_children()[0]  # TODO: add a better check for this
        canvas.config(width=self.width)
        canvas.config(height=self.height)

        print("width changed to {} height changed to {}".format(
            self.width, self.height))

        # when the frame is resized, change the dimensions in the app and re-generate the image
        self.app.tile_generator.frame_width = self.width
        self.app.tile_generator.frame_height = self.height
        self.app.draw_image_on_canvas()


class FileSelection:

    def __init__(self, master):

        self.master = master
        self.frame = tk.Frame(self.master)

        # select file button
        select_button = tk.Button(self.frame, text='Select File')
        select_button.pack(fill=tk.X)
        select_button.bind('<Button-1>', self.file_selection)

        self.frame.pack(padx=50, pady=50)

        if len(sys.argv) >= 2:
            root.tiles_directory = sys.argv[1]
        else:
            root.tiles_directory = None

    def file_selection(self, event):
        # open the file selection menu and get the file path
        root.file_path = filedialog.askopenfilename()

        # separate the file name from the full path
        root.file_name = os.path.basename(root.file_path)
        print("root.file_path: {}".format(root.file_path))

        self.frame.pack_forget()
        self.app = LevelSelection(self.master)


class LevelSelection:

    def __init__(self, master):

        frame = tk.Frame(root)
        frame.focus_force()
        slide = open_slide(root.file_path)
        dz_generator = DeepZoomGenerator(slide)

        select_level = ttk.Label(frame, text="Select Initial Level")
        select_level.pack()

        # combo box for initial level
        selection = ttk.Combobox(
            frame, values=[i for i in range(dz_generator.level_count)])
        selection.pack()

        # confirm button
        confirm = tk.Button(frame, text='OK')
        confirm.pack()

        def on_button_press(event):
            frame.pack_forget()

            # if tiles_dirctory is provided in args, the visualiser tool is run
            if root.tiles_directory is None:
                Recorder(root, deep_zoom_object=dz_generator, level=int(selection.get()))
            else:
                Visualiser(root, deep_zoom_object=dz_generator, level=int(selection.get()))

        confirm.bind('<Button-1>', on_button_press)

        frame.pack(padx=50, pady=50)


# function to set up the folders required and the information file
# Update (-Komal): converted from info.txt -> info.json for improved data retrieval
def set_up_folder(dz_generator):
    folder_path = os.path.join(os.path.dirname(os.path.abspath(
        __file__)), 'lsiv_output', datetime.now().strftime('%Y-%m-%d %H-%M-%S'))
    os.makedirs(folder_path)

    level_count = dz_generator.level_count
    level_details = []

    for level in range(level_count):
        width, height = dz_generator.level_dimensions[level]
        level_details.append({"Level": level, "Width": width, "Height": height})

    properties = {"File_Name": root.file_name,
                  "File_Path": root.file_path,
                  "Level_Count": level_count,
                  "Level_Details": level_details}

    with open(os.path.join(folder_path, 'info.json'), 'w+') as info:
        json.dump(properties, info, indent=4, separators=(',', ': '))
        info.close()

    return folder_path


def on_closing():
    if messagebox.askokcancel("Quit", "Do you really wish to quit?"):
        root.destroy()


root = tk.Tk()
root.minsize(width=250, height=125)
root.title("WSI Viewer")

app = FileSelection(root)
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()