from src.view.utils.router import Router
from src.view.menu.help import About, Contacts
from tkinter.messagebox import showinfo, askyesno
from src.control.utils.urls import get_url
from pathlib import Path
from packaging import version
from src.setting import VERSION
import requests
import webbrowser
import os


class HelpMenu():
    def __init__(self, root: Router) -> None:
        self.root = root
        root.bind('<<open-doc>>', self.open_doc_fun)
        root.bind('<<about>>', self.about_fun)
        root.bind('<<contacts>>', self.contacts_fun)
        self.monitor = Monitor(root)
    
    def open_doc_fun(self, e):
        # os.startfile(os.path.abspath("./data/doc/optibar.pdf"))
        path = (Path(__file__).parent.parent.parent.parent).joinpath('data', 'doc', 'optibar.pdf').absolute()
        os.startfile(path)
    
    def about_fun(self, e):
        About(self.root)

    def contacts_fun(self, e):
        Contacts(self.root)