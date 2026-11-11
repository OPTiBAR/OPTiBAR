import tkinter as tk

from .help import HelpMenu


class FileMenu(tk.Menu):
    def __init__(self, parent, root):
        super().__init__(parent)
        self.add_command(label='Open…', accelerator='Ctrl+O', command=lambda: root.event_generate("<<open-file>>"))
        self.add_command(label='Reload', accelerator='F5', command=lambda: root.event_generate("<<reload-file>>"))
        self.add_separator()
        self.add_command(label='Exit', command=root.destroy)
        root.bind_all('<Control-o>', lambda e: root.event_generate("<<open-file>>"))
        root.bind_all('<F5>', lambda e: root.event_generate("<<reload-file>>"))


class ViewMenu(tk.Menu):
    def __init__(self, parent, root):
        super().__init__(parent)
        self.dark_var = tk.BooleanVar(root, False)
        self.add_checkbutton(label='Dark Theme', variable=self.dark_var, command=lambda: root.event_generate("<<toggle-theme>>"))


class MenuBar(tk.Menu):
    def __init__(self, parent):
        tk.Menu.__init__(self, parent)
        parent['menu'] = self
        self.file = FileMenu(parent=self, root=parent)
        self.add_cascade(menu=self.file, label='File')
        self.view = ViewMenu(parent=self, root=parent)
        self.help = HelpMenu(parent=self, root=parent)
        self.add_cascade(menu=self.view, label='View')
        self.add_cascade(menu=self.help, label='Help')
