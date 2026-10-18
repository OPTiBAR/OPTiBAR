import tkinter as tk
from tkinter import ttk
from typing import List, Dict
from gui.view.utils.common import LogWindow
from gui.view.utils.styles import palette

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


class FileFrame(ttk.LabelFrame):
    def __init__(self, parent):
        ttk.LabelFrame.__init__(self, parent, text='Files')

        # widgets
        self.save_button = ttk.Button(self, text='Save Results', command=lambda: self.event_generate("<<save-button-pressed>>"))
        self.pdf_button = ttk.Button(self, text='PDF Drawing', command=lambda: self.event_generate("<<pdf-button-pressed>>"))
        self.dxf_button = ttk.Button(self, text='DXF Drawing', command=lambda: self.event_generate("<<dxf-button-pressed>>"))
        separator = ttk.Separator(self, orient=tk.VERTICAL)

        self.diagram_button = ttk.Button(self, text='Diagram', command=lambda: self.event_generate("<<diagram-button-pressed>>"))

        self.diagram_type_var = tk.StringVar()
        self.diagram_type_var.set('total')
        total_radio = ttk.Radiobutton(self, text='Total', variable=self.diagram_type_var, value='total')
        additional_radio = ttk.Radiobutton(self, text='Additional', variable=self.diagram_type_var, value='additional')

        # geometry
        self.save_button.grid(rowspan=2, row=0, column=0)
        self.pdf_button.grid(rowspan=2, row=0, column=1)
        self.dxf_button.grid(rowspan=2, row=0, column=2)
        separator.grid(rowspan=2, row=0, column=3, sticky='ns')
        self.diagram_button.grid(rowspan=2, row=0, column=4)
        total_radio.grid(row=0, column=5,sticky='nsw')
        additional_radio.grid(row=1, column=5,sticky='nsw')

        for i in range(6):
            self.columnconfigure(i, weight=1)
        for child in self.winfo_children():
            child.grid_configure(padx=10, pady=10)

    def get_diagram_type(self):
        return self.diagram_type_var.get()

    def set_button_state(self, name: str, state: str):
        """toggles the state of a button

        Args:
            name (str): should be save, pdf, dxf or diagram
            state (str): should be disabled or !disabled

        Raises:
            ValueError: raises if the input value is not appropriate.
        """
        if name not in ('save', 'pdf', 'dxf', 'diagram'):
            raise ValueError("button name should be save, pdf, dxf or diagram")
        if state not in ('disabled', '!disabled'):
            raise ValueError("state value should be disabled or !disabled")
        getattr(self, name + '_button').state([state])

class Diagram():
    def __init__(self, root) -> None:
        window = tk.Toplevel(root)
        window.title('Mass Diagram')
        main = ttk.Frame(window)
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        fig = Figure(figsize=(6, 4), dpi=100)
        self.sub = fig.add_subplot(1,1,1)
        # match the app theme
        colors = palette()
        fig.set_facecolor(ttk.Style(window).lookup('TFrame', 'background') or colors['text_bg'])
        self.sub.set_facecolor(colors['text_bg'])
        self.sub.tick_params(colors=colors['text_fg'])
        for item in (self.sub.xaxis.label, self.sub.yaxis.label, self.sub.title):
            item.set_color(colors['text_fg'])
        for spine in self.sub.spines.values():
            spine.set_color(colors['border'])
        self.sub.grid(True, color=colors['border'], linewidth=0.6)

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


class ResultNote(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self,parent)
        self.files = FileFrame(self)
        self.log = LogWindow(self)

        # geometry
        self.files.grid(row=0, column=0, sticky='news', padx=20, pady=10)
        self.log.grid(row=1, column=0, sticky='news', padx=20, pady=10)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
