from tkinter import Label, ttk
import tkinter as tk
from src.view.utils.router import Router

class UserMenu(tk.Menu, Router):
    def __init__(self, parent, root):
        super().__init__(parent)
        Router.__init__(self, 'user')
        self.root = root

    def set_anonymous_layout(self):
        self.delete(0, 'end')
        self.add_command(label='Login', command=lambda: self.root.event_generate("<<login-pressed>>"))
        self.add_command(label='Sign up', command=lambda: self.root.event_generate("<<signup-pressed>>"))
        self.add_command(label='Password Reset', command=lambda: self.root.event_generate("<<password-reset-pressed>>"))

    def set_loged_in_layout(self):
        self.delete(0, 'end')
        self.add_command(label='Dashboard', command=lambda: self.root.event_generate("<<dashboard-pressed>>"))
        self.add_command(label='Logout', command=lambda: self.root.event_generate("<<logout-pressed>>"))