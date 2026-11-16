import tkinter as tk
from pathlib import Path
from tkinter import ttk
from tkinter.filedialog import askopenfilename

from PIL import Image, ImageTk

from optibar.gui.view.body.status import StatusBar
from optibar.gui.view.body.tooltip import ToolTip
from optibar.gui.view.utils.styles import themed_image

# style of the status badge for each kind of status
STATUS_STYLES = {
    'idle': 'Muted.TLabel',
    'busy': 'Muted.TLabel',
    'success': 'Success.TLabel',
    'warning': 'Warning.TLabel',
    'error': 'Error.TLabel',
}
LOGO_SIZE = 30 # px


class FileBar(ttk.Frame):
    """the header of the window: the app name on the left; the input file, Reload and Open… on the right.
    The file shows by its name, the full path is in its tooltip; its status is in the status bar."""
    def __init__(self, parent, status_bar: StatusBar):
        ttk.Frame.__init__(self, parent, padding=(16, 10, 16, 10))

        # variables
        self.path_var = tk.StringVar()
        self.status_var = status_bar.file_var
        self.name_var = tk.StringVar()
        self.folder_var = tk.StringVar()

        # widgets
        brand = ttk.Label(self, text=' OPTiBAR', compound='left', style='Brand.TLabel')
        self.brand = brand
        self._show_logo()
        # the gray bars of the logo would vanish on the dark theme, it has a light version
        self.bind('<<ThemeChanged>>', self._show_logo, add='+')
        file_frame = ttk.Frame(self)
        name_label = ttk.Label(file_frame, textvariable=self.name_var, style='FileName.TLabel')
        folder_label = ttk.Label(file_frame, textvariable=self.folder_var, style='Muted.TLabel')
        self.path_tip = ToolTip(name_label, '')
        status_label = status_bar.file_label
        status_label.bind('<Button-1>', lambda e: self.event_generate('<<status-clicked>>'))
        browse_button = ttk.Button(self, text="Open…", command=self.browse_fun, style='Accent.TButton')
        load_button = ttk.Button(self, text="Reload", command=self.load_fun)
        self.browse_button = browse_button
        self.load_button = load_button
        self.status_label = status_label

        # geometry
        brand.grid(row=0, column=0, sticky='w', padx=(0, 32))
        file_frame.grid(row=0, column=1, sticky='we')
        name_label.grid(row=0, column=0, sticky='w')
        folder_label.grid(row=0, column=1, sticky='w', padx=(10, 0))
        load_button.grid(row=0, column=3, padx=(16, 8))
        browse_button.grid(row=0, column=4)
        self.columnconfigure(1, weight=1)

        self.path_var.trace_add('write', self._show_path)
        self._show_path()

    def _show_logo(self, *args) -> None:
        logo = Image.open(themed_image('logo')).convert('RGBA').resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
        self._logo = ImageTk.PhotoImage(logo, master=self)
        self.brand.configure(image=self._logo)

    def _show_path(self, *args) -> None:
        path = self.path_var.get()
        if path:
            self.name_var.set(Path(path).name)
            self.folder_var.set(_shorten(str(Path(path).parent), 70))
        else:
            self.name_var.set('No input file')
            self.folder_var.set('Open the Access file that SAFE exports (.accdb or .mdb)')
        self.path_tip.text = path

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


def _shorten(text: str, length: int) -> str:
    """the end of a long path, which tells more than its start"""
    return text if len(text) <= length else '…' + text[-(length - 1):]
