import tkinter as tk

from optibar.gui.view.utils.styles import set_theme
from .help import HelpMenu


class ViewMenu():
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.bind('<<toggle-theme>>', self.toggle_theme)

    def toggle_theme(self, *args):
        set_theme(self.root, 'dark' if self.root.menu.view.dark_var.get() else 'light')


class MenuBar():
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        ViewMenu(root)
        HelpMenu(root)
