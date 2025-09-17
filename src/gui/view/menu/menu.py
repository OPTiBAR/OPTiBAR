from tkinter import Label, ttk
import tkinter as tk

from ..utils.registery import Registry
from .help import HelpMenu
from .setting import SettingMenu
from .user.user import UserMenu



class MenuBar(tk.Menu):
    def __init__(self, parent):
        tk.Menu.__init__(self, parent)
        registry = Registry()
        registry.register(self, 'menu')
        parent['menu'] = self
        menu_user = UserMenu(parent=self, root=parent)
        menu_help = HelpMenu(parent=self, root=parent)
        menu_setting = SettingMenu(parent=self, root=parent)
        self.add_cascade(menu=menu_user, label='User')
        self.add_cascade(menu=menu_setting, label='Setting')
        self.add_cascade(menu=menu_help, label='Help')

        self.add_child(menu_user)





        
        



