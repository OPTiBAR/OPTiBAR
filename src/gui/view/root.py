import tkinter as tk
from tkinter import ttk
from pathlib import Path

from src.control.controller import Controller
from src.view.body.notebook import NoteBook
# from src.view.header import Header
from src.view.menu.menu import MenuBar
from src.view.utils.styles import Styler
from src.view.utils.router import Router

class Root(tk.Tk, Router):
    def __init__(self):
        tk.Tk.__init__(self)
        Router.__init__(self, 'root')

        # initialize styles
        Styler()

        # title and icon
        self.option_add('*tearOff', False)
        self.title("OPTiBAR")
        # self.iconphoto(True, tk.PhotoImage(file='./data/images/logo.png'))
        self.iconphoto(True, tk.PhotoImage(file=(Path(__file__).parent.parent.parent).joinpath('data', 'images', 'logo.png').absolute()))
        

        # widgets
        menu_bar = MenuBar(self)
        # header = Header(self)
        notebook = NoteBook(self)
        self.add_child(notebook)
        self.add_child(menu_bar)

        # geometry
        # header.grid(row=0, column=0, sticky='ensw')
        notebook.grid(row=1, column=0, sticky='ewns', pady=(10,0))
        self.columnconfigure(0, weight=1)
        # self.rowconfigure(0, weight=1, minsize=100)
        self.rowconfigure(1, weight=10)
        # add Controller
        Controller(self)
        # start event loop
        self.mainloop()