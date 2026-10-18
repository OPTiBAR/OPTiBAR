import tkinter as tk
from tkinter import ttk
from typing import List, Dict
from gui.view.utils.common import LogWindow
from gui.setting import IMAGES_PATH
from PIL import Image, ImageTk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


class FileFrame(ttk.LabelFrame):
    def __init__(self, parent):
        ttk.LabelFrame.__init__(self, parent, text='Files')

        # widgets
        dgr_img = Image.open(IMAGES_PATH.joinpath('diagram.png')).convert("RGBA").resize((35,35))
        self.dgr_image = ImageTk.PhotoImage(dgr_img)
        self.diagram_button = ttk.Button(self, text='Diagram', image=self.dgr_image, command=lambda: self.event_generate("<<diagram-button-pressed>>"), compound="left")

        self.diagram_type_var = tk.StringVar()
        self.diagram_type_var.set('total')
        total_radio = ttk.Radiobutton(self, text='Total', variable=self.diagram_type_var, value='total')
        additional_radio = ttk.Radiobutton(self, text='Additional', variable=self.diagram_type_var, value='additional')

        # geometry
        self.diagram_button.grid(rowspan=2, row=0, column=0)
        total_radio.grid(row=0, column=1,sticky='nsw')
        additional_radio.grid(row=1, column=1,sticky='nsw')

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        for child in self.winfo_children():
            child.grid_configure(padx=10, pady=10)

    def get_diagram_type(self):
        return self.diagram_type_var.get()

    def set_diagram_button_state(self, state: str):
        """toggles the state of the diagram botton

        Args:
            state (str): should be disabled or !disabled

        Raises:
            Exception: raises if the input value is not appropriate.
        """
        if state not in ('disabled', '!disabled'):
            raise ValueError("state value should be disabled or !disabled")
        self.diagram_button.state([state])

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
