import tkinter as tk
from tkinter import ttk
from src.view.utils.common import Popup

class SettingMenu(tk.Menu):
    def __init__(self, parent, root):
        super().__init__(parent)
        self.add_command(label='Autocad Path', command=lambda: root.event_generate("<<open-acad-path>>"))

class AutocadPath(Popup):
    def __init__(self, root, path_var: tk.StringVar) -> None:
        Popup.__init__(self, title='Autocad Path', root=root)
        main = self.main

        # variable
        self.path_var = path_var

        # widgets
        browse_button = ttk.Button(main, text="Browse", command=self.browse_fun)
        path_label = ttk.Label(main, textvariable=self.path_var, borderwidth=2, relief="solid", width=60)
        
        # geometry
        browse_button.grid(row=0,column=1, sticky='n')
        path_label.grid(row=0,column=0, sticky='w')
        
        main.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=0)
        main.columnconfigure(1, weight=1)

        for child in main.winfo_children(): 
            child.grid_configure(padx=15, pady=15)
    
    def browse_fun(self):
        """open the ask for file window and sets the file_path variable value.
        """
        file_extentions = [
            ('exe file', '*.exe'),
        ]
        file_path = tk.filedialog.askopenfilename(filetypes = file_extentions, defaultextension = file_extentions)
        self.path_var.set(file_path)