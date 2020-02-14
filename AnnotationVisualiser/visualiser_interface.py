import os
os.add_dll_directory(r'D:\openslide-win32-20171122\bin')

import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox
from PIL import ImageTk
from functools import partial
from openslide import open_slide
from openslide.deepzoom import DeepZoomGenerator
from threading import Thread
from datetime import datetime
#import dynamic_tiling
import json


class DirectorySelection:

    def __init__(self, master):

        self.master = master
        self.frame = tk.Frame(self.master)

        # select file button
        select_button = tk.Button(self.frame, text='Select Directory')
        select_button.pack(fill=tk.X)
        select_button.bind('<Button-1>', self.file_selection)

        self.frame.pack(padx=50, pady=50)

    # NOTE: root.file_path now points to the directory containing info.json
    # TO get path of .svs see entry_file_path in LevelSelection
    def file_selection(self, event):
        # open the file selection menu and get the file path
        root.file_path = filedialog.askdirectory(title='Please select a info.json containing directory')
        print("root.file_path: {}".format(root.file_path))

        self.frame.pack_forget()
        self.app = LevelSelection(self.master)


class LevelSelection:

    def __init__(self, master):

        frame = tk.Frame(root)
        frame.focus_force()

        with open(root.file_path+'/info.json') as f:
            data = json.load(f)
            file_path_default = data['File_Path']
            file_name = data['File_Name']

        # File path of source .svs
        label_file_name = tk.Label(frame, text="File Name: "+file_name)
        label_file_name.grid(column=1, row=0)

        label_file_source_path = tk.Label(frame, text="File Source: ")
        label_file_source_path.grid(sticky="E", column=0, row=1)

        # Entry Box for File Path
        entry_file_path = tk.Entry(frame, width=85)
        entry_file_path.insert(0, file_path_default)
        entry_file_path.grid(column=1, row=1)

        # Browse Button
        browse = tk.Button(frame, text='Browse')
        browse.grid(sticky="W", column=2, row=1, padx=(5,0))

        select_level = ttk.Label(frame, text="Select Initial Level: ")
        select_level.grid(sticky="E", column=0, row=4)

        # Combo box for initial level
        selection = ttk.Combobox(
            frame, values=[level for level in os.listdir(root.file_path+'/tiles')
                           if os.path.isdir(os.path.join(root.file_path+'/tiles', level))])
        selection.grid(sticky="W", column=1, row=4)

        # Confirm button
        confirm = tk.Button(frame, text='OK')
        confirm.grid(sticky="S", column=1, row=5, ipadx=10)

        def source_file_selection(event):
            new_file_path = filedialog.askopenfilename()
            if not new_file_path == "":
                entry_file_path.delete(0, "end")
                entry_file_path.insert(0, new_file_path)

        def on_button_press(event):
            # Warning if source .svs not discovered
            if not os.path.isfile(entry_file_path.get()):
                messagebox.showerror("Error", "Cannot find file source")
            elif selection.get() == "":
                messagebox.showerror("Error", "Please select level")
            else:
                frame.pack_forget()
                slide = open_slide(entry_file_path.get())
                dz_generator = DeepZoomGenerator(slide)

                # Start main program
                # App(root, root.file_path, deep_zoom_object=dz_generator,level=int(selection.get()))

        browse.bind('<ButtonRelease>', source_file_selection)
        confirm.bind('<ButtonRelease>', on_button_press)
        frame.pack(padx=50, pady=50)


class App(tk.Tk):
    def __init__(self, root_window, path, deep_zoom_object, level=0):

        self.deep_zoom_object = deep_zoom_object            #whyy?

        # the dynamic tile generator, responsible for providing the image to the canvas to display
        # self.tile_generator = dynamic_tiling.DynamicTiling(
        #     deep_zoom_object, level, 800, 600, folder_path)

        self.root_window = root_window

        self.x = self.y = 0

        # x coordinate at top-left, y coordinate at top-left,
        # x coordinate at bottom-right, y coordinate at bottom-right
        self.box_coords = (0, 0, 0, 0)
        self.base_dir = path

        self.root_window.title("Large Scale Image Viewer")
        self.root_window.attributes("-fullscreen", True)
        self.frame = ResizingFrame(self.root_window, self)
        self.frame.pack(fill=tk.BOTH, expand=tk.YES)

        self.canvas = tk.Canvas(self.frame, bg="#0F5FFF", width=800, height=600)

        # set up the horizontal scroll bar
        self.hbar = tk.Scrollbar(self.frame, orient=tk.HORIZONTAL)
        self.hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.hbar.config(command=self.__scroll_x)

        # set up the vertical scroll bar
        self.vbar = tk.Scrollbar(self.frame, orient=tk.VERTICAL)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.vbar.config(command=self.__scroll_y)

        # generate initial image for starting coordinates
        image, self.top_left = self.tile_generator.generate_image(
            (0, 0, 800, 600), (-1, -1))
        self.image = ImageTk.PhotoImage(image=image)

        # set the image on the canvas
        self.image_on_canvas = self.canvas.create_image(
            self.top_left[0], self.top_left[1], image=self.image, anchor="nw")

        # remember canvas position
        self.canvas.bind('<ButtonPress-1>', self.move_from)
        # move canvas to the new position
        self.canvas.bind('<B1-Motion>', self.move_to)
        # zoom for Windows and MacOS, but not Linux
        self.canvas.bind_all("<MouseWheel>", self.__wheel)

        self.canvas.focus_set()
        self.start_x = None
        self.start_y = None

        self.set_scroll_region()
        self.canvas.config(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        self.canvas.pack(expand=tk.YES, fill=tk.BOTH)

    def set_scroll_region(self):
        dim = self.tile_generator.get_dim()
        self.canvas.config(scrollregion=(0, 0, dim[0], dim[1]))

    def __scroll_x(self, *args):
        # scroll canvas horizontally and redraw the image
        self.canvas.xview(*args)
        self.get_data()

    def __scroll_y(self, *args):
        # scroll canvas horizontally and redraw the image
        self.canvas.yview(*args)
        self.get_data()

    # zoom for MacOS and Windows
    def __wheel(self, event):
        # zoom with mouse wheel

        # get coordinates of the event on the canvas
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        old_dim = self.tile_generator.get_dim()

        if event.delta == -120:  # zoom out
            change = -1
        else:  # zoom in
            change = +1

        v_reg = self.vbar.get()
        h_reg = self.hbar.get()

        print("v_reg: {}".format(v_reg))
        print("h_reg: {}".format(h_reg))

        # change the level in the tile generator to the new level
        self.tile_generator.change_level(self.tile_generator.level + change)
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

        self.box_coords = (canvas_top_left[0], canvas_top_left[1],
                           canvas_top_left[0] + self.frame.width, canvas_top_left[1] + self.frame.height)

        # get the new image using the new coordinates
        image, self.top_left = self.tile_generator.generate_image(
            self.box_coords, (-1, -1))

        self.image = ImageTk.PhotoImage(image=image)

        # delete the old image and set the new image
        self.canvas.delete(self.image_on_canvas)
        self.image_on_canvas = self.canvas.create_image(
            canvas_top_left[0], canvas_top_left[1], image=self.image, anchor="nw")

        scrollbar_x = canvas_top_left[0] / new_dim[0]
        scrollbar_y = canvas_top_left[1] / new_dim[1]

        # set new dimensions as scroll region
        self.canvas.config(scrollregion=(0, 0, new_dim[0], new_dim[1]))

        # move the canvas to the calculated coordinates
        self.canvas.xview_moveto(scrollbar_x)
        self.canvas.yview_moveto(scrollbar_y)

        self.get_data()

    def move_from(self, event):
        # remember previous coordinates for scrolling with the mouse
        self.canvas.scan_mark(event.x, event.y)

    def move_to(self, event):
        # drag (move) canvas to the new position
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.get_data()  # redraw the image

    def get_data(self):

        self.canvas_vertex = (self.canvas.canvasx(0), self.canvas.canvasy(0))
        self.box_coords = (self.canvas_vertex[0], self.canvas_vertex[1],
                           self.canvas_vertex[0] + self.frame.width, self.canvas_vertex[1] + self.frame.height)

        # some weird bug with canvas being 0 when scrolling back to origin
        if self.box_coords[0] == -1:
            self.box_coords = (
                self.box_coords[0] + 1, self.box_coords[1], self.box_coords[2] + 1, self.box_coords[3])

        if self.box_coords[1] == -1:
            self.box_coords = (
                self.box_coords[0], self.box_coords[1] + 1, self.box_coords[2], self.box_coords[3] + 1)

        image, top_left = self.tile_generator.generate_image(
            self.box_coords, self.top_left)
        if image is not None:
            self.canvas.delete(self.image_on_canvas)
            self.image = ImageTk.PhotoImage(image=image)

            self.image_on_canvas = self.canvas.create_image(
                top_left[0], top_left[1], image=self.image, anchor="nw")


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
        self.app.get_data()


# function to set up the folders required and the information file
def set_up_folder(dz_generator):
    folder_path = os.path.join(os.path.dirname(os.path.abspath(
        __file__)), 'lsiv_output', datetime.now().strftime('%Y-%m-%d %H-%M-%S'))
    os.makedirs(folder_path)
    with open(os.path.join(folder_path, 'info.txt'), 'w+') as info:
        level_count = dz_generator.level_count

        # write details to the file
        info.write("File Name: {}\n".format(root.file_name))
        info.write("Level Count: {}\n\n".format(level_count))
        info.write("Level Details: \n\n")
        info.write("{:>5} {:>7} {:>7}\n".format("Level", "Width", "Height"))

        # write width and height for each level
        for level in range(level_count):
            width, height = dz_generator.level_dimensions[level]
            info.write("{:5} {:7} {:7}\n".format(level, width, height))

    return folder_path


def on_closing():
    if messagebox.askokcancel("Quit", "Do you really wish to quit?"):
        root.destroy()


root = tk.Tk()
root.minsize(width=250, height=125)
root.title("Annotation Visualisation Tool")
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

DirectorySelection(root)
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop();