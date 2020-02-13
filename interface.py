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
import json
import dynamic_tiling
import tracking
import heatmap_generation


class App(tk.Tk):
    def __init__(self, root_window, path, deep_zoom_object, level=0):

        self.deep_zoom_object = deep_zoom_object
        folder_path = set_up_folder(deep_zoom_object)

        # the dynamic tile generator, responsible for providing the image to the canvas to display
        self.tile_generator = dynamic_tiling.DynamicTiling(
            deep_zoom_object, level, 800, 600, folder_path)

        # shows whether the gaze tracker currently tracking
        self.is_tracking = False

        self.root_window = root_window

        self.bbox = []
        self.x = self.y = 0

        # x coordinate at top-left, y coordinate at top-left,
        # x coordinate at bottom-right, y coordinate at bottom-right
        self.box_coords = (0, 0, 0, 0)
        self.base_dir = path

        self.root_window.title("Large Scale Image Viewer")
        self.root_window.attributes("-fullscreen", True)
        root.config(bg='gray80')


        self.frame2 = tk.Frame(self.root_window ,width=50, height = 50)
        self.frame2.config(bg='gray80')
        self.frame2.pack(fill=None, expand=False)


        self.imgEyeOff = ImageTk.PhotoImage(file=r"Assets\icon2xOff.png")
        self.imgEyeOn = ImageTk.PhotoImage(file=r"Assets\icon2xOn.png")

        self.button = tk.Button(self.frame2,fg="red",text="hello",bg='gray80',image=self.imgEyeOff,command=self.start_stop_tracking)
        self.button.pack(side=tk.LEFT,padx=(15,15),pady=(15,15))

        self.zoomLabel = tk.Label(self.frame2,text = str(level) +"X" ,bg='gray90',font=("Helvetica", 14),borderwidth=2, relief="groove")
        self.zoomLabel.pack(side=tk.LEFT,padx=(5,5),pady=(15,15))

        self.notificationLabel = tk.Label(self.frame2,text="Gaze Recording Disabled",bg='gray90',font=("Helvetica", 14),borderwidth=2, relief="groove")
        self.notificationLabel.pack(side=tk.LEFT,padx=(5,5),pady=(15,15))

        self.fileLabel = tk.Label(self.frame2,text=str("Source:\n"+root.file_name),bg='gray90',font=("Helvetica", 14),borderwidth=2, relief="groove")
        self.fileLabel.pack(side=tk.LEFT,padx=(5,5),pady=(15,15))

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
        # zoom for Linux, wheel scroll up
        self.canvas.bind('<Button-4>', self.__wheelup)
        # zoom for Linux, wheel scroll down
        self.canvas.bind('<Button-5>', self.__wheeldown)

        self.canvas.focus_set()
        self.canvas.bind("b", self.bounding_box)
        self.canvas.bind("t", self.start_stop_tracking)
        self.canvas.bind("h", self.generate_heatmap)

        self.start_x = None
        self.start_y = None

        self.set_scroll_region()
        self.canvas.config(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        self.canvas.pack(expand=tk.YES, fill=tk.BOTH,padx=(100,100), pady=(0,10))

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

        print(v_reg)
        print(h_reg)

        # change the level in the tile generator to the new level
        self.tile_generator.change_level(self.tile_generator.level + change)
        self.zoomLabel.config(text=str(self.tile_generator.level)+"X")
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

    # zoom in for Linux
    def __wheelup(self, event):
        self.tile_generator.change_level(self.tile_generator.level + 1)
        self.set_scroll_region()
        self.get_data()

    # zoom out for Linux
    def __wheeldown(self, event):
        self.tile_generator.change_level(self.tile_generator.level - 1)
        self.set_scroll_region()
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

    def start_stop_tracking(self, event):

        if self.is_tracking:
            self.notificationLabel.configure(text="Gaze Recording Disabled")
            self.button.configure(image=self.imgEyeOff)
            self.is_tracking = False
        else:
            self.button.configure(image=self.imgEyeOn)
            self.notificationLabel.configure(text="Gaze Recording in Progress")    
            self.is_tracking = True
            resolution = (self.root_window.winfo_screenwidth(),
                          self.root_window.winfo_screenheight())  # a tuple for resolution
            partial_function = partial(tracking.main, self, resolution)
            Thread(target=partial_function).start()

    def generate_heatmap(self, event):
        heatmap_generation.generate_heatmap(self.deep_zoom_object, self.tile_generator.folder_path)


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


class FileSelection:

    def __init__(self, master):

        self.master = master
        self.frame = tk.Frame(self.master)

        # select file button
        select_button = tk.Button(self.frame, text='Select File')
        select_button.pack(fill=tk.X)
        select_button.bind('<Button-1>', self.file_selection)

        self.frame.pack(padx=50, pady=50)

    def file_selection(self, event):
        # open the file selection menu and get the file path
        root.file_path = filedialog.askopenfilename()

        # separate the file name from the full path
        root.file_name = os.path.basename(root.file_path)
        print("root.file_path: {}".format(root.file_path))

        self.frame.pack_forget()
        # self.newWindow = tk.Toplevel(self.master)
        # self.app = LevelSelection(self.newWindow)
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
            App(root, root.file_path, deep_zoom_object=dz_generator,
                level=int(selection.get()))

        confirm.bind('<Button-1>', on_button_press)

        frame.pack(padx=50, pady=50)


# function to set up the folders required and the information file
# Update (-Komal): converted from info.txt -> info.json for improved data retrieval
def set_up_folder(dz_generator):
    folder_path = os.path.join(os.path.dirname(os.path.abspath(
        __file__)), 'lsiv_output', datetime.now().strftime('%Y-%m-%d %H-%M-%S'))
    os.makedirs(folder_path)

    level_count = dz_generator.level_count
    level_details = [];

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
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

app = FileSelection(root)
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
