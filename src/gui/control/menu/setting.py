import tkinter as tk
from src.view.menu.setting import AutocadPath

class SettingMenu():
    def __init__(self, root, path_var: tk.StringVar) -> None:
        self.root = root
        self.path_var = path_var
        root.bind('<<open-acad-path>>', self.open_autocad_path)
    
    def open_autocad_path(self, *args):
        AutocadPath(self.root, self.path_var)

