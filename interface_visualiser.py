import os
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
from openslide import open_slide
from openslide.deepzoom import DeepZoomGenerator
from modules.visualiser import Visualiser
import json

class DirectorySelection:

    def __init__(self, master):

        self.master = master
        self.frame = tk.Frame(self.master)

        # select file button
        select_button = tk.Button(self.frame, text='Select Directory')
        select_button.pack(fill=tk.X)
        select_button.bind('<Button-1>', self.directory_selection)

        self.frame.pack(padx=50, pady=50)

        # if len(sys.argv) >= 2:
        #     root.tiles_directory = sys.argv[1]
        # else:
        #     root.tiles_directory = None

    def directory_selection(self, event):
        # open the file selection menu and get the file path
        root.file_path = filedialog.askdirectory(title='Please select a info.json containing directory')
        print("root.file_path: {}".format(root.file_path))
        root.tiles_directory=root.file_path

        self.frame.pack_forget()
        self.app = LevelSelection(self.master)


class LevelSelection:

    def __init__(self, master):

        frame = tk.Frame(root)
        frame.focus_force()

        with open(root.file_path + '/info.json') as f:
            data = json.load(f)
            file_path_default = data['File_Path']
            file_name = data['File_Name']

        # File path of source .svs
        label_file_name = tk.Label(frame, text="File Name: " + file_name)
        label_file_name.grid(column=1, row=0)
        # separate the file name from the full path
        root.file_name=file_name

        label_file_source_path = tk.Label(frame, text="File Source: ")
        label_file_source_path.grid(sticky="E", column=0, row=1)

        # Entry Box for File Path
        entry_file_path = tk.Entry(frame, width=85)
        entry_file_path.insert(0, file_path_default)
        entry_file_path.grid(column=1, row=1)

        # Browse Button
        browse = tk.Button(frame, text='Browse')
        browse.grid(sticky="W", column=2, row=1, padx=(5, 0))

        # Level Selection
        select_level = ttk.Label(frame, text="Select Initial Level: ")
        select_level.grid(sticky="E", column=0, row=4)

        # Combo box for initial level
        selection = ttk.Combobox(
            frame, values=[level for level in os.listdir(root.file_path + '/tiles')
                           if os.path.isdir(os.path.join(root.file_path + '/tiles', level))])
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
            else:
                frame.pack_forget()
                slide = open_slide(entry_file_path.get())
                dz_generator = DeepZoomGenerator(slide)

                # Start main program
                Visualiser(root, deep_zoom_object=dz_generator, level=int(selection.get()))
                print ("Visualiser")

        browse.bind('<ButtonRelease>', source_file_selection)
        confirm.bind('<ButtonRelease>', on_button_press)
        frame.pack(padx=50, pady=50)


root = tk.Tk()
root.minsize(width=250, height=125)
root.title("Annotation Visualisation Tool")

app = DirectorySelection(root)
root.mainloop()
