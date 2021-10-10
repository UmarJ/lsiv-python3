import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from modules import heatmap_generation
from openslide import open_slide
from openslide.deepzoom import DeepZoomGenerator
import json
import re
import csv
import glob



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

        self.frame = tk.Frame(root)
        self.frame.focus_force()

        with open(root.file_path+'/info.json') as f:
            data = json.load(f)
            file_path_default = data['File_Path']
            file_name = data['File_Name']
            self.max_level = int(data['Level_Count']) - 1

        # File path of source .svs
        label_file_name = tk.Label(self.frame, text="File Name: "+file_name)
        label_file_name.grid(column=1, row=0)

        label_file_source_path = tk.Label(self.frame, text="File Source: ")
        label_file_source_path.grid(sticky="E", column=0, row=1)

        # Entry Box for File Path
        self.entry_file_path = tk.Entry(self.frame, width=65)
        self.entry_file_path.insert(0, file_path_default)
        self.entry_file_path.grid(column=1, row=1)

        # Browse Button
        browse = tk.Button(self.frame, text='Browse')
        browse.grid(sticky="W", column=2, row=1, padx=(5,0))

        # Gaussian Matrix Size Selection Label
        gaussian_matrix_size_label = ttk.Label(self.frame, text="Gaussian Matrix Size: ")
        gaussian_matrix_size_label.grid(sticky="E", column=0, row=4)


        # Entry Box for Gaussian Matrix Selection
        self.gaussian_matrix_size = tk.Entry(self.frame, width=10)
        c = root.register(self.only_numeric_input)
        self.gaussian_matrix_size.configure(validate="key", validatecommand=(c, '%P'))
        self.gaussian_matrix_size.insert(0, 200)
        self.gaussian_matrix_size.grid(sticky="W", column=1, row=4)

        # Standard Deviation Label
        sd_label = ttk.Label(self.frame, text="\t\t\tStandard Deviation:", state='disabled')
        sd_label.grid(sticky="S",column=1, row=4)

        # Entry Box for Standard Deviation Selection
        self.standard_deviation = tk.Entry(self.frame, width=10, state='disabled')
        self.standard_deviation.configure(validate="key", validatecommand=(c, '%P'))
        self.standard_deviation.insert(0, 50)
        self.standard_deviation.grid(sticky="E",column=1, row=4)

        # Radio Button for level-wise & merged level
        self.var = tk.IntVar()
        tk.Radiobutton(self.frame, text="Merge All Levels", variable=self.var, value=1).grid(sticky="W",column=1, row=5)
        tk.Radiobutton(self.frame, text="Level-wise \t \t   ", variable=self.var, value=2).grid(sticky="E",column=1, row=5)
        self.var.set(1)

        # Radio Button for binary map & heat map
        self.map = tk.StringVar()
        tk.Radiobutton(self.frame, text="Heat Map", variable=self.map, value="heatmap").grid(sticky="W", column=1, row=6)
        tk.Radiobutton(self.frame, text="Binary Map \t \t   ", variable=self.map, value="binarymap").grid(sticky="E", column=1, row=6)
        self.map.set("heatmap")


        # Confirm button
        confirm = tk.Button(self.frame, text='OK')
        confirm.grid(sticky="S", column=1, row=8, ipadx=10)

       # self.merged_levels()
        browse.bind('<ButtonRelease>', self.source_file_selection)
        confirm.bind('<ButtonRelease>', self. on_button_press)
        self.frame.pack(padx=50, pady=50)

    def only_numeric_input(self,e):
        # this is allowing all numeric input
        if e.isdigit():
            return True
        # this will allow backspace to work
        elif e == "":
            return True
        else:
            return False

    def source_file_selection(self,event):
        new_file_path = filedialog.askopenfilename()
        if not new_file_path == "":
            self.entry_file_path.delete(0, "end")
            self.entry_file_path.insert(0, new_file_path)

    def merged_levels(self):
        max_level_merged = []
        count = 0;

        #bring level points to maxlevel
        os.chdir(root.file_path)
        result = [i for i in glob.glob('Level *[0-9].csv')]
        for file in result:
            level = int(re.findall(r'\d+', file)[0])
            scaling_factor = 2 ** (self.max_level - level)
            with open(file) as csv_file:
                reader = csv.reader(csv_file)
                for row in reader:
                    x = int(row[0]) * scaling_factor
                    y = int(row[1]) * scaling_factor
                    max_level_merged.append((x,y))
                    count = count + 1


        print("Count: ")
        print(len(max_level_merged))

        path = os.path.join(root.file_path, 'Merged_Levels')
        if not os.path.exists(path):
            os.makedirs(path)

        for newCSV in result:
            for level in range(9, self.max_level):
                scaling_factor = 2 ** (self.max_level - level)
                csv_output = open(os.path.join(path, "Level " + str(level) + ".csv"), "a")
                with open(csv_output.name, 'wb+') as csv_file:
                    writer = csv.writer(csv_file, delimiter=',')
                    saved_points = []
                    for x, y in max_level_merged:
                        saved_points.append( ( int(round(x/scaling_factor)), int (round(y/scaling_factor) ) ) )

                    writer.writerows(saved_points)



    def on_button_press(self, event):
        # Warning if source .svs not discovered
        if not os.path.isfile(self.entry_file_path.get()):
            messagebox.showerror("Error", "Cannot find file source")
        else:
            self.frame.pack_forget()
            slide = open_slide(self.entry_file_path.get())
            dz_generator = DeepZoomGenerator(slide)

            if self.var.get() == 2:

                heatmap_generation.generate_heatmap(dz_generator, root.file_path, self.gaussian_matrix_size.get(), self.map.get())
            else:
                self.merged_levels()
                # Start main program
                heatmap_generation.generate_heatmap(dz_generator,  os.path.join(root.file_path, 'Merged_Levels'),
                                                    self.gaussian_matrix_size.get(), self.map.get())
                print("DONE")




def on_closing():
    if messagebox.askokcancel("Quit", "Do you really wish to quit?"):
        root.destroy()


root = tk.Tk()
root.minsize(width=250, height=125)
root.title("Heatmap Generation Menu")

DirectorySelection(root)
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop();