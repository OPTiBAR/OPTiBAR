import tkinter as tk
from tkinter.constants import SE

from .help import HelpMenu
from .user import UserMenu
from .setting import SettingMenu


class MenuBar():
    def __init__(self, root, token_var: tk.StringVar, path_var: tk.StringVar) -> None:
        self.root = root
        HelpMenu(root)
        UserMenu(root, token_var)
        SettingMenu(root, path_var)
        




