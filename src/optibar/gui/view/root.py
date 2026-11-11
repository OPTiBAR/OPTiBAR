import tkinter as tk
from tkinter import ttk

from optibar.gui.view.body.upload import FileBar
from optibar.gui.view.body.calculation.notebook import SettingsPane
from optibar.gui.view.body.results import ResultsPane
from optibar.gui.view.menu.menu import MenuBar
from optibar.gui.view.utils.styles import enable_dpi_awareness, set_theme
from optibar.gui.setting import IMAGES_PATH

class Root(tk.Tk):
    """one window: the input file on top, the settings on the left, the results on the right"""
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
        self.file_bar = FileBar(self)
        separator = ttk.Separator(self, orient=tk.HORIZONTAL)
        self.panes = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.settings = SettingsPane(self.panes)
        self.results = ResultsPane(self.panes)
        self.panes.add(self.settings, weight=0)
        self.panes.add(self.results, weight=1)

        # geometry
        self.file_bar.grid(row=0, column=0, sticky='ew', padx=16, pady=(12, 10))
        separator.grid(row=1, column=0, sticky='ew')
        self.panes.grid(row=2, column=0, sticky='ewns', padx=16, pady=12)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self._set_size()

    def _set_size(self):
        """opens at a size that fits both panes, centered and within the screen"""
        self.update_idletasks()
        # the report pane gets more room than the settings, for its wide tables
        width = min(max(int(2.2 * self.settings.winfo_reqwidth()) + 60, 1200), int(self.winfo_screenwidth() * 0.92))
        height = min(max(self.settings.winfo_reqheight() + self.file_bar.winfo_reqheight() + 60, 720), int(self.winfo_screenheight() * 0.88))
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 3
        self.geometry(f'{width}x{height}+{x}+{y}')
        self.minsize(min(width, 1000), min(height, 640))
