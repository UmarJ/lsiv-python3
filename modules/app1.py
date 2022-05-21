from PIL import ImageTk
import PIL.Image
import tkinter as tk
from tkinter import messagebox
from tkinter import *
import os

class App1(tk.Tk):
    def __init__(self,root_window,file_path):

        self.root_window = root_window

        self.assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..//assets")

        self.imgEyeOff = ImageTk.PhotoImage(file=os.path.join(self.assets_dir, "icon2xOff.png"))

        self.x, self.y = 0, 0
 
        self.img = file_path

        self.box_coords = (0, 0, 0, 0)

        self.root_window.title("Large Scale Image Viewer")
        self.root_window.attributes("-fullscreen", True)
        self.root_window.config(bg='gray80')

        self.root_window.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.frame2 = tk.Frame(self.root_window, width=50, height=50)

        self.frame2.config(bg='gray80')

        self.frame2.pack(fill=None, expand=False)

        self.zoomLabel = tk.Label(self.frame2, text=str(11) + "x", bg='gray90', font=("Helvetica", 14), borderwidth=2, relief="groove")
        self.zoomLabel.pack(side=tk.LEFT, padx=(5, 5), pady=(15, 15))

        self.fileLabel = tk.Label(self.frame2, text=str("Source:\n" + self.root_window.file_name), bg='gray90', font=("Helvetica", 14), borderwidth=2, relief="groove", width=20)
        self.fileLabel.pack(side=tk.LEFT, padx=(5, 5), pady=(15, 15))

        self.buttonClose = tk.Button(self.frame2, text="Close", command=self.on_closing)
        self.buttonClose.pack(side=tk.LEFT, padx=(5, 5), pady=(15, 15))

        self.notificationLabel = tk.Label(self.frame2, text="Gaze Recording Disabled", bg='gray90', font=("Helvetica", 14), borderwidth=2, relief="groove")
        self.notificationLabel.pack(side=tk.LEFT, padx=(5, 5), pady=(15, 15))

        self.gazeToggleButton = tk.Button(self.frame2, fg="red", text="hello", bg='gray80', image=self.imgEyeOff)
        self.gazeToggleButton.pack(side=tk.LEFT, padx=(15, 15), pady=(15, 15))

        self.frame = tk.Frame(self.root_window, width=900, height=750)
        self.frame.config(bg='gray80')
        self.frame.pack(fill=tk.BOTH, expand=tk.YES)

        self.button1 = tk.Button(self.frame, text='Button1')



        self.image1 = PIL.Image.open(self.img)
        self.x,self.y=self.image1.size
        self.image2 = ImageTk.PhotoImage(self.image1)

        self.canvas = tk.Canvas(self.frame, bg="gray80", width=1000, height=1000,scrollregion=(0,0,self.x,self.y))

        # set up the horizontal scroll bar
        self.hbar = tk.Scrollbar(self.frame, orient=tk.HORIZONTAL)
        self.hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.hbar.config(command=self.canvas.xview)
       

        # set up the vertical scroll bar
        self.vbar = tk.Scrollbar(self.frame, orient=tk.VERTICAL)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        # self.vbar.config(command=self._scroll_y)
        self.vbar.config(command=self.canvas.yview)
        
        self.canvas.config(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        self.canvas.pack(expand=tk.YES, fill=tk.BOTH, padx=(100, 100), pady=(0, 10))
        
        

          

        self.canvas['xscrollcommand'] = self.hbar.set
        
        self.canvas.create_image(0,0, image=self.image2,anchor=tk.NW)

        self.root_window.mainloop()        
            
    def set_scroll_region(self):
        self.canvas.config(scrollregion=(0, 0, 4000, 4000))        


    def __scroll_x(self, *args):
        # scroll canvas horizontally and redraw the image
        self.canvas.xview(*args)
        
    def __scroll_y(self, *args):
        # scroll canvas horizontally and redraw the image
        self.canvas.yview(*args)
        



    # virtual method
    def get_image(self, box_coords):
        raise NotImplementedError()

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you really wish to quit?"):
            self.root_window.destroy()
