import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from PIL import ImageTk
from functools import partial
from openslide import open_slide
from openslide.deepzoom import DeepZoomGenerator
from threading import Thread
import dynamic_tiling
import tracking
import heatmap_generation


class App(tk.Tk):
    def __init__(self, root_window, path, deep_zoom_object, level=0):

        self.deep_zoom_object = deep_zoom_object
        self.tile_generator = dynamic_tiling.DynamicTiling(
            deep_zoom_object, level, 800, 600)
        self.is_tracking = False

        self.root_window = root_window

        self.bbox = []
        self.x = self.y = 0
        self.box_coords = (0, 0, 0, 0)
        self.base_dir = path

        self.root_window.title("Large Scale Image Viewer")
        self.root_window.attributes("-fullscreen", True)
        self.frame = ResizingFrame(self.root_window, self)
        self.frame.pack(fill=tk.BOTH, expand=tk.YES)

        self.canvas = tk.Canvas(
            self.frame, bg="#FFFFFF", width=800, height=600)

        self.hbar = tk.Scrollbar(self.frame, orient=tk.HORIZONTAL)
        self.hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.hbar.config(command=self.__scroll_x)

        self.vbar = tk.Scrollbar(self.frame, orient=tk.VERTICAL)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.vbar.config(command=self.__scroll_y)

        image, self.top_left = self.tile_generator.generate_image(
            (0, 0, 800, 600), (-1, -1))

        self.image = ImageTk.PhotoImage(image=image)

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
        self.canvas.config(xscrollcommand=self.hbar.set,
                           yscrollcommand=self.vbar.set)
        self.canvas.pack(expand=tk.YES, fill=tk.BOTH)

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
        """ Scroll canvas horizontally and redraw the image """
        self.canvas.xview(*args)  # scroll horizontally
        self.get_data()  # redraw the image

    def __scroll_y(self, *args):
        """ Scroll canvas horizontally and redraw the image """
        self.canvas.yview(*args)  # scroll horizontally
        self.get_data()  # redraw the image

    def __wheel(self, event):
        """ Zoom with mouse wheel """

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

        self.tile_generator.change_level(self.tile_generator.level + change)
        new_dim = self.tile_generator.get_dim()

        ratio_w = float(new_dim[0]) / float(old_dim[0])
        ratio_h = float(new_dim[1]) / float(old_dim[1])

        # TODO: fix zoom IT'S STILL BROKEN EVEN AFTER IVE WASTED AN HOUR ON IT
        centre_x = x * ratio_w
        centre_y = y * ratio_h
        canvas_top_left = max(0, centre_x - (self.frame.width // 2)), max(0, centre_y - (self.frame.height // 2))

        self.box_coords = (canvas_top_left[0], canvas_top_left[1], canvas_top_left[0] + self.frame.width, canvas_top_left[1] + self.frame.height)

        image, self.top_left = self.tile_generator.generate_image(
            self.box_coords, (-1, -1))

        self.image = ImageTk.PhotoImage(image=image)
        self.canvas.delete(self.image_on_canvas)

        self.image_on_canvas = self.canvas.create_image(
            canvas_top_left[0], canvas_top_left[1], image=self.image, anchor="nw")
        
        scrollbar_x = canvas_top_left[0] / new_dim[0]
        scrollbar_y = canvas_top_left[1] / new_dim[1]

        self.canvas.config(scrollregion=(0, 0, new_dim[0], new_dim[1]))
        self.canvas.xview_moveto(scrollbar_x)
        self.canvas.yview_moveto(scrollbar_y)

        self.get_data()

    def __wheelup(self, event):
        self.tile_generator.change_level(self.tile_generator.level + 1)
        self.set_scroll_region()
        self.get_data()

    def __wheeldown(self, event):
        self.tile_generator.change_level(self.tile_generator.level - 1)
        self.set_scroll_region()
        self.get_data()

    def move_from(self, event):
        ''' Remember previous coordinates for scrolling with the mouse '''
        self.canvas.scan_mark(event.x, event.y)

    def move_to(self, event):
        ''' Drag (move) canvas to the new position '''
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
            self.is_tracking = False
        else:
            self.is_tracking = True
            resolution = (self.root_window.winfo_screenwidth(),
                          self.root_window.winfo_screenheight())  # a tuple for resolution
            partial_function = partial(tracking.main, self, resolution)
            Thread(target=partial_function).start()

    def generate_heatmap(self, event):
        heatmap_generation.stitch_images(
            self.deep_zoom_object, self.tile_generator.tiles_generated, self.tile_generator.folder_path)


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

        self.app.tile_generator.frame_width = self.width
        self.app.tile_generator.frame_height = self.height
        self.app.get_data()


class FileSelection:

    def __init__(self, master):

        self.master = master
        self.frame = tk.Frame(self.master)

        select_button = tk.Button(self.frame, text='Select File')
        select_button.pack(fill=tk.X)
        select_button.bind('<Button-1>', self.file_selection)

        self.frame.pack(padx=50, pady=50)

    def file_selection(self, event):
        root.file_path = filedialog.askopenfilename()
        print("root.file_path: {}".format(root.file_path))

        self.frame.pack_forget()
        self.newWindow = tk.Toplevel(self.master)
        self.app = LevelSelection(self.newWindow)


class LevelSelection:

    def __init__(self, master):

        frame = tk.Frame(root)
        frame.focus_force()
        slide = open_slide(root.file_path)
        dz_generator = DeepZoomGenerator(slide)

        select_level = ttk.Label(frame, text="Select Initial Level")
        selection = ttk.Combobox(
            frame, values=[i for i in range(dz_generator.level_count)])
        confirm = tk.Button(frame, text='OK')
        select_level.pack()
        selection.pack()
        confirm.pack()

        def on_button_press(event):
            frame.pack_forget()
            App(root, root.file_path, deep_zoom_object=dz_generator,
                level=int(selection.get()))

        confirm.bind('<Button-1>', on_button_press)

        frame.pack(padx=50, pady=50)


def on_closing():
    root.destroy()


root = tk.Tk()
root.minsize(width=200, height=160)

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

app = FileSelection(root)
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
