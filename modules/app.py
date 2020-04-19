import dynamic_tiling
import heatmap_generation
from PIL import ImageTk
import Tkinter as tk
import tkMessageBox as messagebox


class App(tk.Tk):
    def __init__(self, root_window, deep_zoom_object, tiles_folder, level=0):

        self.root_window = root_window

        self.x, self.y = 0, 0

        # x coordinate at top-left, y coordinate at top-left,
        # x coordinate at bottom-right, y coordinate at bottom-right
        self.box_coords = (0, 0, 0, 0)

        self.root_window.title("Large Scale Image Viewer")
        self.root_window.attributes("-fullscreen", True)
        self.root_window.config(bg='gray80')
        self.root_window.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.frame2 = tk.Frame(self.root_window, width=50, height=50)
        self.frame2.config(bg='gray80')
        self.frame2.pack(fill=None, expand=False)

        self.zoomLabel = tk.Label(self.frame2, text=str(level) + "x", bg='gray90', font=("Helvetica", 14), borderwidth=2, relief="groove")
        self.zoomLabel.pack(side=tk.LEFT, padx=(5, 5), pady=(15, 15))

        self.fileLabel = tk.Label(self.frame2, text=str("Source:\n" + self.root_window.file_name), bg='gray90', font=("Helvetica", 14), borderwidth=2, relief="groove")
        self.fileLabel.pack(side=tk.LEFT, padx=(5, 5), pady=(15, 15))

        self.buttonClose = tk.Button(self.frame2, text="Close", command=self.on_closing)
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

        # Sets the anchor which can be used to move the canvas if the mouse is dragged.
        self.canvas.bind('<ButtonPress-1>', self.move_from)
        # Move canvas to the new position using the anchor.
        self.canvas.bind('<B1-Motion>', self.move_to)
        # zoom for Windows and MacOS, but not Linux
        self.canvas.bind_all("<MouseWheel>", self.__wheel)
        # zoom for Linux, wheel scroll up
        self.canvas.bind('<Button-4>', self.__wheelup)
        # zoom for Linux, wheel scroll down
        self.canvas.bind('<Button-5>', self.__wheeldown)

        self.canvas.focus_set()

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

        self.box_coords = (canvas_top_left[0], canvas_top_left[1],
                           canvas_top_left[0] + self.frame.width, canvas_top_left[1] + self.frame.height)

        # reset the top left
        self.top_left = (-1, -1)

        # the draw_image_on_canvas function cannot be used since this needs to scroll the canvas too
        image, self.top_left = self.get_image(self.box_coords)

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
        # scan_mark sets the anchor for the scan_dragto function to use.
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

        self.box_coords = box_coords

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

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you really wish to quit?"):
            self.root_window.destroy()


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
