from modules.app import App
from modules.utils import set_up_folder
import os
from modules import tracking
import tkinter as tk
from PIL import ImageTk
from functools import partial
from threading import Thread


class Recorder(App):
    def __init__(self, root_window, deep_zoom_object, level=0):
        tiles_folder = set_up_folder(deep_zoom_object, root_window.file_name, root_window.file_path)
        # Python 2.x compatible constructor
        App.__init__(self, root_window, deep_zoom_object, tiles_folder, level=level)

        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..//assets")

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
