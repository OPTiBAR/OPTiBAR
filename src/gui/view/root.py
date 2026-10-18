import tkinter as tk

from gui.view.body.notebook import NoteBook
from gui.view.menu.menu import MenuBar
from gui.view.utils.styles import Styler
from gui.setting import IMAGES_PATH

class Root(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)

        # initialize styles
        Styler()

        # title and icon
        self.option_add('*tearOff', False)
        self.title("OPTiBAR")
        self.iconphoto(True, tk.PhotoImage(file=IMAGES_PATH.joinpath('logo.png')))

        # widgets
        self.menu = MenuBar(self)
        self.notebook = NoteBook(self)

        # geometry
        self.notebook.grid(row=1, column=0, sticky='ewns', pady=(10,0))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=10)
