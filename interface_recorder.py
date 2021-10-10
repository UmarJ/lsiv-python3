import os
import tkinter as tk
import sys
from tkinter import filedialog
from tkinter import ttk
from openslide import open_slide
from openslide.deepzoom import DeepZoomGenerator
from modules.recorder import Recorder

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

            Recorder(root, deep_zoom_object=dz_generator, level=int(selection.get()))
            #     print ("Recorder")

            # # if tiles_dirctory is provided in args, the visualiser tool is run
            # if root.tiles_directory is None:
            #     Recorder(root, deep_zoom_object=dz_generator, level=int(selection.get()))
            #     print ("Recorder")
            # else:
            #     Visualiser(root, deep_zoom_object=dz_generator, level=int(selection.get()))
            #     print ("Visualiser")


        confirm.bind('<Button-1>', on_button_press)

        frame.pack(padx=50, pady=50)

root = tk.Tk()
root.minsize(width=250, height=125)
root.title("WSI Viewer")

app = FileSelection(root)
root.mainloop()
