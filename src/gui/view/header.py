import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import math

class Header(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self['style'] = 'header.TFrame'
        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)
        self.original = Image.open("./data/images/header-2.png")
        self.image = ImageTk.PhotoImage(self.original)
        self.ratio = self.image.height()/self.image.width()
        self.display = tk.Canvas(self, bd=0, highlightthickness=0)
        self.display.create_image(0, 0, image=self.image,anchor='nw', tags="IMG")
        self.display.grid()
        self.display['background'] = '#37483e'
        self.bind("<Configure>", self.resize)

    def resize(self,event):
        width = event.width
        height = event.height
        if height < math.ceil(width * self.ratio):
            size = (math.ceil(height/self.ratio), height)
        else:
            size = (width, math.ceil(width * self.ratio))          
        resized = self.original.resize(size,Image.ANTIALIAS)
        self.last_size = size
        self.image = ImageTk.PhotoImage(resized)
        self.display.delete("IMG")
        self.display.create_image(int((width - size[0])/2), 0, image=self.image,anchor='nw', tags="IMG")
        self.display.config(width = max(size[0], width), height = size[1])
