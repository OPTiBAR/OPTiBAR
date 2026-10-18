import tkinter as tk

from optibar.gui.view.body.notebook import NoteBook
from optibar.gui.view.menu.menu import MenuBar
from optibar.gui.view.utils.styles import enable_dpi_awareness, set_theme
from optibar.gui.setting import IMAGES_PATH

class Root(tk.Tk):
    def __init__(self, theme: str = 'light'):
        enable_dpi_awareness()
        tk.Tk.__init__(self)
        set_theme(self, theme)

        # title and icon
        self.option_add('*tearOff', False)
        self.title("OPTiBAR")
        self.iconphoto(True, tk.PhotoImage(file=IMAGES_PATH.joinpath('logo.png')))

        # widgets
        self.menu = MenuBar(self)
        self.notebook = NoteBook(self)

        # geometry
        self.notebook.grid(row=0, column=0, sticky='ewns', padx=12, pady=12)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._set_size()

    def _set_size(self):
        """opens at a size that fits the calculation tab, centered and within the screen"""
        self.update_idletasks()
        width = min(max(self.notebook.winfo_reqwidth() + 24, 1000), int(self.winfo_screenwidth() * 0.9))
        height = min(max(self.notebook.winfo_reqheight() + 24, 720), int(self.winfo_screenheight() * 0.85))
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 3
        self.geometry(f'{width}x{height}+{x}+{y}')
        self.minsize(min(width, 900), min(height, 640))
