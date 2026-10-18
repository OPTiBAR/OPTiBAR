import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk
import webbrowser
from gui.view.utils.common import Popup
from gui.setting import VERSION, REPO_URL, IMAGES_PATH

class HelpMenu(tk.Menu):
    def __init__(self, parent, root):
        super().__init__(parent)
        self.add_command(label='Documentation', command=lambda: root.event_generate("<<open-doc>>"))
        self.add_command(label='About', command=lambda: root.event_generate("<<about>>"))

class About(Popup):
    def __init__(self, root) -> None:
        Popup.__init__(self, title='About', root=root)
        main = self.main

        # widgets
        optibar_img = Image.open(IMAGES_PATH.joinpath('optibar.png')).convert("RGBA").resize((120,100))
        main.optibar_image = ImageTk.PhotoImage(optibar_img)
        logo_label = ttk.Label(main, image=main.optibar_image)
        version_label = ttk.Label(main, text='Software Version: ' + VERSION)
        repo_link = ttk.Label(main, text=REPO_URL, cursor="hand2", style='Link.TLabel')
        repo_link.bind('<Button-1>', lambda e: webbrowser.open(REPO_URL))
        ok_button = ttk.Button(main, text='OK', command=self.close)

        # geometry
        logo_label.grid(row=0,column=0, sticky='n', padx=40, pady=15)
        version_label.grid(row=1,column=0, sticky='w', padx=15, pady=(15,5))
        repo_link.grid(row=2,column=0, sticky='w', padx=15, pady=(5,15))
        ok_button.grid(row=3, column=0, sticky='s', padx=15, pady=15)

        for i in range(4):
            main.rowconfigure(i, weight=1)
        main.columnconfigure(0, weight=1)
