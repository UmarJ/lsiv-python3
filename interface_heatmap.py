import os
import Tkinter as tk
import ttk
import tkFileDialog as filedialog
import tkMessageBox as messagebox
from modules import heatmap_generation
from openslide import open_slide
from openslide.deepzoom import DeepZoomGenerator
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
        self.app = HeatMapSettingsMenu(self.master)


class HeatMapSettingsMenu:

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

        # Gaussian Matrix Size Selection Label
        select_level = ttk.Label(frame, text="Gaussian Matrix Size: ")
        select_level.grid(sticky="E", column=0, row=4)

        def only_numeric_input(e):
            # this is allowing all numeric input
            if e.isdigit():
                return True
            # this will allow backspace to work
            elif e == "":
                return True
            else:
                return False


        # Entry Box for Gaussian Matrix Selection
        gaussian_matrix_size = tk.Entry(frame, width=10)
        c = root.register(only_numeric_input)
        gaussian_matrix_size.configure(validate="key", validatecommand=(c, '%P'))
        gaussian_matrix_size.insert(0, 200)
        gaussian_matrix_size.grid(sticky="W", column=1, row=4)


        # # Level Selection
        # select_level = ttk.Label(frame, text="Select Initial Level: ")
        # select_level.grid(sticky="E", column=0, row=4)
        #
        # # Combo box for initial level
        # selection = ttk.Combobox(
        #     frame, values=[level for level in os.listdir(root.file_path+'/tiles')
        #                    if os.path.isdir(os.path.join(root.file_path+'/tiles', level))])
        # selection.grid(sticky="W", column=1, row=4)

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
                heatmap_generation.generate_heatmap(dz_generator, root.file_path, gaussian_matrix_size.get())

        browse.bind('<ButtonRelease>', source_file_selection)
        confirm.bind('<ButtonRelease>', on_button_press)
        frame.pack(padx=50, pady=50)


def on_closing():
    if messagebox.askokcancel("Quit", "Do you really wish to quit?"):
        root.destroy()


root = tk.Tk()
root.minsize(width=250, height=125)
root.title("Heatmap Generation Menu")

DirectorySelection(root)
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop();