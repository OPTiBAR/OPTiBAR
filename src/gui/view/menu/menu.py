import tkinter as tk

from .help import HelpMenu


class MenuBar(tk.Menu):
    def __init__(self, parent):
        tk.Menu.__init__(self, parent)
        parent['menu'] = self
        self.help = HelpMenu(parent=self, root=parent)
        self.add_cascade(menu=self.help, label='Help')
