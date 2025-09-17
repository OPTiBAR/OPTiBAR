import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from ..utils.registery import Registry
from ..utils.common import LogWindow

class UploadNote(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self,parent)
        registry = Registry()
        registry.register(self, 'upload')

        file_browser = FileBrowser(self)
        upload_log = LogWindow(self)

        self.add_child(file_browser)
        self.add_child(upload_log)

        # geometry
        file_browser.grid(row=0, column=0, sticky='new')
        upload_log.grid(row=1, column=0, sticky='news', padx=20, pady=10)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)


class FileBrowser(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        registry = Registry()
        registry.register(self, 'browser')
        
        # variables
        self.path_var = tk.StringVar()
        self.status_var = tk.StringVar()

        # widgets
        browse_button = ttk.Button(self, text="Browse", command=self.browse_fun)
        path_label = ttk.Label(self, textvariable=self.path_var, borderwidth=2, relief="solid", width=20)
        upload_button = ttk.Button(self, text="Upload", command=self.upload_fun)
        status_label = ttk.Label(self, textvariable=self.status_var)
        self.upload_button = upload_button
        self.browse_button = browse_button

        # geometry
        browse_button.grid(row=0, column=1, padx=20, pady=10, sticky='e')
        path_label.grid(row=0, column=0, padx=20, pady=10, sticky='we')
        upload_button.grid(row=1, column=1, padx=20, pady=10, sticky='e')
        status_label.grid(row=1, column=0, padx=20, pady=10, sticky='w')
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=10)
        self.columnconfigure(0, weight=10)
        self.columnconfigure(1, weight=1)
        

    def upload_fun(self):
        """generates an event when upload button is pressed
        """
        self.event_generate("<<upload-button-pressed>>")

    def set_status(self, value:str):
        self.status_var.set('Status: ' + value)
    
    def set_upload_button_state(self, state: str):
        """toggles the state of the upload botton

        Args:
            state (str): should be disabled or !disabled

        Raises:
            Exception: raises if the input value is not appropriate.
        """
        if state == 'disabled':
            self.upload_button.state(['disabled'])
        elif state == '!disabled':
            self.upload_button.state(['!disabled'])
        else:
            raise Exception("state value should be disabled or !disabled")
    
    def set_browse_button_state(self, state: str):
        """toggles the state of the upload botton

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
        file_path = tk.filedialog.askopenfilename(filetypes = file_extentions, defaultextension = file_extentions)
        self.path_var.set(file_path)
    
