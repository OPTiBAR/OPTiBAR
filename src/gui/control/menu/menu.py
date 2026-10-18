import tkinter as tk

from .help import HelpMenu


class MenuBar():
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        HelpMenu(root)
