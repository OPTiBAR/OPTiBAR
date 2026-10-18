import tkinter as tk

from .help import HelpMenu


class ViewMenu(tk.Menu):
    def __init__(self, parent, root):
        super().__init__(parent)
        self.dark_var = tk.BooleanVar(root, False)
        self.add_checkbutton(label='Dark Theme', variable=self.dark_var, command=lambda: root.event_generate("<<toggle-theme>>"))


class MenuBar(tk.Menu):
    def __init__(self, parent):
        tk.Menu.__init__(self, parent)
        parent['menu'] = self
        self.view = ViewMenu(parent=self, root=parent)
        self.help = HelpMenu(parent=self, root=parent)
        self.add_cascade(menu=self.view, label='View')
        self.add_cascade(menu=self.help, label='Help')
