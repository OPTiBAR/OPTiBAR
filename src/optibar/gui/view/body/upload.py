import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename

# style of the status badge for each kind of status
STATUS_STYLES = {
    'idle': 'Muted.TLabel',
    'busy': 'Muted.TLabel',
    'success': 'Success.TLabel',
    'warning': 'Warning.TLabel',
    'error': 'Error.TLabel',
}


class FileBar(ttk.Frame):
    """the input file across the top of the window: its path, Open..., Reload and a status badge"""
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)

        # variables
        self.path_var = tk.StringVar()
        self.status_var = tk.StringVar()

        # widgets
        label = ttk.Label(self, text='Input file')
        path_entry = ttk.Entry(self, textvariable=self.path_var, state='readonly', width=20)
        browse_button = ttk.Button(self, text="Open…", command=self.browse_fun, style='Accent.TButton')
        load_button = ttk.Button(self, text="Reload", command=self.load_fun)
        status_label = ttk.Label(self, textvariable=self.status_var, style=STATUS_STYLES['idle'], cursor='hand2')
        status_label.bind('<Button-1>', lambda e: self.event_generate('<<status-clicked>>'))
        self.browse_button = browse_button
        self.load_button = load_button
        self.status_label = status_label

        # geometry
        label.grid(row=0, column=0, padx=(0, 8), sticky='w')
        path_entry.grid(row=0, column=1, padx=(0, 8), sticky='we')
        browse_button.grid(row=0, column=2, padx=(0, 8))
        load_button.grid(row=0, column=3, padx=(0, 16))
        status_label.grid(row=0, column=4, sticky='w')
        self.columnconfigure(1, weight=3)
        self.columnconfigure(4, weight=2, minsize=220)

    def load_fun(self):
        """generates an event when the file should be (re)loaded"""
        self.event_generate("<<load-button-pressed>>")

    def set_status(self, value: str, kind: str = 'idle'):
        """kind is one of idle, busy, success, warning, error"""
        self.status_var.set(value)
        self.status_label.configure(style=STATUS_STYLES[kind])

    def set_load_button_state(self, state: str):
        """state should be disabled or !disabled"""
        if state not in ('disabled', '!disabled'):
            raise ValueError("state value should be disabled or !disabled")
        self.load_button.state([state])

    def set_browse_button_state(self, state: str):
        """state should be disabled or !disabled"""
        if state not in ('disabled', '!disabled'):
            raise ValueError("state value should be disabled or !disabled")
        self.browse_button.state([state])

    def browse_fun(self):
        """asks for an Access file and loads it"""
        file_extentions = [
            ('Access File', '*.accdb'),
            ('Access File', '*.mdb'),
        ]
        file_path = askopenfilename(filetypes = file_extentions, defaultextension = ".accdb")
        if file_path:
            self.path_var.set(file_path)
            self.load_fun()
