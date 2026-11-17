import tkinter as tk
from tkinter import ttk


class StatusBar(ttk.Frame):
    """the line at the bottom of the window: the state of the input file on the left, the state of the
    run and its progress on the right. The file bar and the Calculate footer write to it."""
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)

        # variables
        self.file_var = tk.StringVar(self)
        self.run_var = tk.StringVar(self)

        # widgets
        rule = ttk.Separator(self, orient=tk.HORIZONTAL)
        self.file_label = ttk.Label(self, textvariable=self.file_var, style='Muted.TLabel', cursor='hand2')
        self.run_label = ttk.Label(self, textvariable=self.run_var, style='Status.TLabel')
        self.progress = ttk.Progressbar(self, mode='determinate', length=200)

        # geometry
        rule.grid(row=0, column=0, columnspan=3, sticky='we')
        self.file_label.grid(row=1, column=0, sticky='w', padx=(16, 0), pady=6)
        self.progress.grid(row=1, column=1, sticky='e', padx=(0, 12))
        self.run_label.grid(row=1, column=2, sticky='e', padx=(0, 16), pady=6)
        self.progress.grid_remove()
        self.columnconfigure(0, weight=1)
