import tkinter as tk
from tkinter import ttk
from optibar.gui.view.body.tooltip import CreateToolTip
from .basic import Setting as BasicSetting
from .advanced import Setting as AdvancedSetting


class CalcType(ttk.LabelFrame):
    def __init__(self, parent):
        ttk.LabelFrame.__init__(self, parent, text='Type of Request')
        # variable and widget
        self.type_var = tk.StringVar()
        self.type_var.set('calculation')
        computation_radio = ttk.Radiobutton(self, text='Computation'+ u' \u24D8', variable=self.type_var, value='calculation', command=self.changed_fun)
        CreateToolTip(computation_radio, 'computation')
        analysis_radio = ttk.Radiobutton(self, text='Analysis'+ u' \u24D8', variable=self.type_var, value='analysis', command=self.changed_fun)
        CreateToolTip(analysis_radio, 'analysis')
        self.analysis_radio = analysis_radio
        # geometry
        computation_radio.grid(row=0, column=0, sticky='w')
        analysis_radio.grid(row=0, column=1, sticky='w')
        for child in self.winfo_children(): 
            child.grid_configure(padx=20, pady=20)
        
    def get_value(self):
        return self.type_var.get()

    def changed_fun(self):
        self.event_generate("<<calc-type-changed>>")
    


class Setting(ttk.Notebook):
    def __init__(self, parent):
        ttk.Notebook.__init__(self, parent)
        basic = BasicSetting(self)
        self.basic = basic
        advanced = AdvancedSetting(self)
        self.advanced = advanced

        basic.grid(sticky='nswe')
        advanced.grid(sticky='nswe')

        self.add(basic, text='Basic')
        self.add(advanced, text='Advanced')

        # geometry
        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)
    
    def get_values(self):
        basic = self.basic.get_values()
        advanced = self.advanced.get_values()
        basic['typical_arrangement']['exceptions'] = advanced['exceptions']
        basic['special_lengths'] = advanced['special_lengths']
        return basic

class CalcRequest(ttk.LabelFrame):
    def __init__(self, parent):
        ttk.LabelFrame.__init__(self, parent, text='Request')
        
        #variables
        self.button_var = tk.StringVar()
        self.button_var.set('Calculate')
        self.status_var = tk.StringVar()
        self.cut_var = tk.StringVar()
        self.cut_var.set('Not')

        
        #widgets
        status_label = ttk.Label(self, textvariable=self.status_var)
        self.progress = ttk.Progressbar(self, mode='determinate', length=220)
        self.calculate_button = ttk.Button(self, textvariable=self.button_var, command=self.calc_fun, style='Accent.TButton', width=12)
        
        #geometry
        status_label.grid(row=0, column=0, sticky='w')
        self.progress.grid(row=0, column=1, sticky='e')
        self.calculate_button.grid(row=0, column=2, sticky='e')
        self.progress.grid_remove()

        self.columnconfigure(0, weight=1)
        for child in self.winfo_children(): 
            child.grid_configure(padx=10, pady=8)
    
    def set_status(self, value: str) -> None:
        self.status_var.set('Status: ' + value)
    
    def set_button_state(self, state: str):
        """toggles the state of the calc botton

        Args:
            state (str): should be disabled or !disabled

        Raises:
            Exception: raises if the input value is not appropriate.
        """
        if state == 'disabled':
            # self.set_button_label(True)
            self.calculate_button.state(['disabled'])
        elif state == '!disabled':
            self.calculate_button.state(['!disabled'])
        else:
            raise Exception("state value should be disabled or !disabled")
    
    def start_progress(self) -> None:
        """a moving bar until the first progress report, or for runs that have none"""
        self.progress.grid()
        self.progress.configure(mode='indeterminate')
        self.progress.start(15)

    def set_progress(self, done: int, total: int) -> None:
        self.progress.stop()
        self.progress.configure(mode='determinate', maximum=total, value=done)

    def stop_progress(self) -> None:
        self.progress.stop()
        self.progress.configure(value=0)
        self.progress.grid_remove()

    def set_button_label(self, label: bool) -> None:
        self.button_var.set(label)
    
    def get_button_label(self) -> str:
        return self.button_var.get()

    def calc_fun(self):
        self.event_generate('<<calc-pressed>>')


class CalcNote(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        
        self.calc_type = CalcType(self)
        self.setting = Setting(self)
        self.request = CalcRequest(self)

        # geometry
        self.calc_type.grid(row=0, column=0, sticky='news', padx=20, pady=10)
        self.setting.grid(row=1, column=0, sticky='news', padx=20, pady=10)
        self.request.grid(row=2, column=0, sticky='news', padx=20, pady=10)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)





