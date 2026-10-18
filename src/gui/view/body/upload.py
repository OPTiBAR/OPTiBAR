import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from gui.view.utils.common import LogWindow

class UploadNote(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self,parent)

        self.browser = FileBrowser(self)
        self.log = LogWindow(self)

        # geometry
        self.browser.grid(row=0, column=0, sticky='new')
        self.log.grid(row=1, column=0, sticky='news', padx=20, pady=10)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)


class FileBrowser(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)

        # variables
        self.path_var = tk.StringVar()
        self.status_var = tk.StringVar()

        # widgets
        browse_button = ttk.Button(self, text="Browse", command=self.browse_fun)
        path_label = ttk.Label(self, textvariable=self.path_var, borderwidth=2, relief="solid", width=20)
        load_button = ttk.Button(self, text="Load", command=self.load_fun)
        status_label = ttk.Label(self, textvariable=self.status_var)
        self.load_button = load_button
        self.browse_button = browse_button

        # geometry
        browse_button.grid(row=0, column=1, padx=20, pady=10, sticky='e')
        path_label.grid(row=0, column=0, padx=20, pady=10, sticky='we')
        load_button.grid(row=1, column=1, padx=20, pady=10, sticky='e')
        status_label.grid(row=1, column=0, padx=20, pady=10, sticky='w')
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=10)
        self.columnconfigure(0, weight=10)
        self.columnconfigure(1, weight=1)


    def load_fun(self):
        """generates an event when load button is pressed
        """
        self.event_generate("<<load-button-pressed>>")

    def set_status(self, value:str):
        self.status_var.set('Status: ' + value)

    def set_load_button_state(self, state: str):
        """toggles the state of the load botton

        Args:
            state (str): should be disabled or !disabled

        Raises:
            Exception: raises if the input value is not appropriate.
        """
        if state == 'disabled':
            self.load_button.state(['disabled'])
        elif state == '!disabled':
            self.load_button.state(['!disabled'])
        else:
            raise Exception("state value should be disabled or !disabled")

    def set_browse_button_state(self, state: str):
        """toggles the state of the browse botton

        Args:
            state (str): should be disabled or !disabled

        Raises:
            Exception: raises if the input value is not appropriate.
        """
        if state == 'disabled':
            self.browse_button.state(['disabled'])
        elif state == '!disabled':
            self.browse_button.state(['!disabled'])
        else:
            raise Exception("state value should be disabled or !disabled")

    def browse_fun(self):
        """open the ask for file window and sets the file_path variable value.
        """
        file_extentions = [
            ('Access File', '*.accdb'),
            ('Access File', '*.mdb'),
        ]
        file_path = askopenfilename(filetypes = file_extentions, defaultextension = file_extentions)
        self.path_var.set(file_path)
