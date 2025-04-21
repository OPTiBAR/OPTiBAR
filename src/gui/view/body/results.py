from logging import Manager
from threading import stack_size
import tkinter as tk
from tkinter import ttk
from typing import List, Dict
from src.view.utils.router import Router
from src.view.utils.common import LogWindow, Popup
from pathlib import Path
from PIL import Image, ImageTk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import math


class FileFrame(ttk.LabelFrame, Router):
    def __init__(self, parent):
        ttk.LabelFrame.__init__(self, parent, text='Files')
        Router.__init__(self, 'files')
        
        # widgets
        # exl_img = Image.open("./src/view/images/excel.png").convert("RGBA").resize((35,35))
        # self.excel_image = ImageTk.PhotoImage(exl_img)
        # self.excel_button = ttk.Button(self, text='Excel', image=self.excel_image, command=lambda: self.event_generate("<<excel-button-pressed>>"), compound="left")

        dwg_img = Image.open((Path(__file__).parent.parent.parent.parent).joinpath('data', 'images', 'dwg.png').absolute()).convert("RGBA").resize((35,35))
        self.dwg_image = ImageTk.PhotoImage(dwg_img)
        self.dwg_button = ttk.Button(self, text='DWG', image=self.dwg_image, command=lambda: self.event_generate("<<dwg-button-pressed>>"), compound="left")

        self.language_var = tk.StringVar()
        self.language_var.set('english')
        english_radio = ttk.Radiobutton(self, text='English', variable=self.language_var, value='english', command=self.changed_language)
        persian_radio = ttk.Radiobutton(self, text='Persian', variable=self.language_var, value='persian', command=self.changed_language)

        s = ttk.Separator(self, orient=tk.VERTICAL)

        dgr_img = Image.open((Path(__file__).parent.parent.parent.parent).joinpath('data', 'images', 'diagram.png').absolute()).convert("RGBA").resize((35,35))
        self.dgr_image = ImageTk.PhotoImage(dgr_img)
        self.diagram_button = ttk.Button(self, text='Diagram', image=self.dgr_image, command=lambda: self.event_generate("<<diagram-button-pressed>>"), compound="left")
        
        self.diagram_type_var = tk.StringVar()
        self.diagram_type_var.set('total')
        total_radio = ttk.Radiobutton(self, text='Total', variable=self.diagram_type_var, value='total')
        additional_radio = ttk.Radiobutton(self, text='Additional', variable=self.diagram_type_var, value='additional')

        # geometry
        # self.excel_button.grid(row=0, column=0)
        self.dwg_button.grid(rowspan=2, row=0, column=0)
        english_radio.grid(row=0, column=1, sticky='nsw')
        persian_radio.grid(row=1, column=1, sticky='nsw')
        s.grid(row=0, column=2,rowspan=2, sticky='ns')
        self.diagram_button.grid(rowspan=2, row=0, column=3)
        total_radio.grid(row=0, column=4,sticky='nsw')
        additional_radio.grid(row=1, column=4,sticky='nsw')

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)
        self.columnconfigure(4, weight=1)
        for child in self.winfo_children(): 
            child.grid_configure(padx=10, pady=10)
    
    def get_language(self):
        return self.language_var.get()

    def get_diagram_type(self):
        return self.diagram_type_var.get()
    
    def changed_language(self, *args):
        self.event_generate('<<language-changed>>')

    def set_buttons_state(self, name: str, state: str):
        """toggles the state of the bottons

        Args:
            state (str): should be disabled or !disabled
            name (str): name of button that could be 'dwg', 'excel', 'diagram'

        Raises:
            Exception: raises if the input value is not appropriate.
        """
        if name not in ('dwg', 'excel', 'diagram'):
            raise ValueError("button name should be dwg, excel or diagram")
        if state == 'disabled':
            getattr(self, name + '_button').state(['disabled'])
        elif state == '!disabled':
            getattr(self, name + '_button').state(['!disabled'])
        else:
            raise ValueError("state value should be disabled or !disabled")

class Diagram():
    def __init__(self, root) -> None:
        window = tk.Toplevel(root)
        window.title('Mass Diagram')
        main = ttk.Frame(window)
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        fig = Figure(figsize=(6, 4), dpi=100)
        self.sub = fig.add_subplot(1,1,1)

        canvas = FigureCanvasTkAgg(fig, master=main)  # A tk.DrawingArea.
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1, pady=(10,15), padx=10)
        self.canvas = canvas

        toolbar = NavigationToolbar2Tk(canvas, main)
        toolbar.update()
        self.toolbar = toolbar
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    
    def plot(self, mass_dict: Dict[int, Dict[str, List[int]]], title) -> None:
        sub = self.sub
        for stack_num in mass_dict:
            sub.plot(mass_dict[stack_num]['total_num'], mass_dict[stack_num]['mass'], label=str(stack_num) + ' piece stack', marker='o', markersize=4)
        sub.title.set_text(title)
        sub.set_xlabel('Number of Length Types')
        sub.set_ylabel('mass(ton)')
        sub.legend(loc='upper left', frameon=True)
        sub.invert_xaxis()
        self.canvas.draw()
        self.toolbar.update()

class BugFrame(ttk.LabelFrame, Router):
    def __init__(self, parent):
        ttk.LabelFrame.__init__(self, parent, text='Bug Report')
        Router.__init__(self, 'bug')
        self.button = ttk.Button(self, text='Report Bug', command=lambda: self.event_generate("<<report-bug-pressed>>"))
        self.button.grid(row=0, column=0, padx=10, pady=10, sticky='e')
        self.columnconfigure(0, weight=1)
    def set_button_state(self, state):
        self.button.state([state])


        
class BugPopup(Popup):
    def __init__(self, root) -> None:
        Popup.__init__(self, root, title='Bug Report')
        self.root = root
        main = self.main

        text = tk.Text(main, wrap='none', height=10, width=30)
        # text['state'] = 'disabled'
        self.text = text
        # yscroll = ttk.Scrollbar(main, orient = 'vertical', command = text.yview)
        # xscroll = ttk.Scrollbar(main, orient = 'horizontal', command = text.xview)
        # text['yscrollcommand'] = yscroll.set
        # text['xscrollcommand'] = xscroll.set
        text.grid(column = 0, row = 0, sticky = 'nwes', pady=(10,10), padx=(20,20))
        # xscroll.grid(column = 0, row = 1, sticky = 'we', padx=(20,0), pady=(0,10))
        # yscroll.grid(column = 1, row = 0, sticky = 'ns', padx=(0,20), pady=(20,0))
        main.grid_columnconfigure(0, weight = 1)
        main.grid_rowconfigure(0, weight = 1)
        main.grid_columnconfigure(1, weight = 1)
        main.grid_rowconfigure(1, weight = 1)

        button = ttk.Button(main, text='report', command=self.report_fun)
        button.grid(row=1, column=0, padx=10, pady=10)
    
    def get_report(self):
        return self.text.get("1.0",tk.END)

    def report_fun(self):
        self.root.event_generate('<<bug-send-pressed>>')


class ResultNote(ttk.Frame, Router):
    def __init__(self, parent):
        ttk.Frame.__init__(self,parent)
        Router.__init__(self, 'results')
        file_frame = FileFrame(self)
        log_window = LogWindow(self)
        bug_frame = BugFrame(self)
        
        self.add_child(file_frame)
        self.add_child(log_window)
        self.add_child(bug_frame)

        # geometry
        file_frame.grid(row=0, column=0, sticky='news', padx=20, pady=10)
        log_window.grid(row=1, column=0, sticky='news', padx=20, pady=10)
        bug_frame.grid(row=2, column=0, sticky='news', padx=20, pady=10)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
