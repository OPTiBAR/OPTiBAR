import tkinter as tk
import webbrowser
from gui.view.menu.help import About
from gui.setting import DOCS_URL


class HelpMenu():
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.bind('<<open-doc>>', self.open_doc_fun)
        root.bind('<<about>>', self.about_fun)

    def open_doc_fun(self, e):
        webbrowser.open(DOCS_URL)

    def about_fun(self, e):
        About(self.root)
