import tkinter as tk
from tkinter import ttk
from src.view.body.tooltip import CreateToolTip
from src.view.utils.router import Router
from .basic import Setting as BasicSetting
from .advanced import Setting as AdvancedSetting


class CalcType(ttk.LabelFrame, Router):
    def __init__(self, parent):
        ttk.LabelFrame.__init__(self, parent, text='Type of Request')
        Router.__init__(self, 'type')
        # variable and widget
        self.type_var = tk.StringVar()
        self.type_var.set('calculation')
        computation_radio = ttk.Radiobutton(self, text='Computation'+ u' \u24BE', variable=self.type_var, value='calculation', command=self.changed_fun)
        CreateToolTip(computation_radio, 'computation')
        analysis_radio = ttk.Radiobutton(self, text='Analysis'+ u' \u24BE', variable=self.type_var, value='analysis', command=self.changed_fun)
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
    


class Setting(ttk.Notebook, Router):
    def __init__(self, parent):
        ttk.Notebook.__init__(self, parent)
        Router.__init__(self, 'setting')
        basic = BasicSetting(self)
        self.basic = basic
        advanced = AdvancedSetting(self)
        self.advanced = advanced

        self.add_child(basic)
        self.add_child(advanced)

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

class CalcRequest(ttk.LabelFrame, Router):
    def __init__(self, parent):
        ttk.LabelFrame.__init__(self, parent, text='Request')
        Router.__init__(self, 'request')
        
        #variables
        self.button_var = tk.StringVar()
        self.button_var.set('Calculate')
        self.status_var = tk.StringVar()
        self.cut_var = tk.StringVar()
        self.cut_var.set('Not')

        
        #widgets
        status_label = ttk.Label(self, textvariable=self.status_var)
        self.calculate_button = ttk.Button(self, textvariable=self.button_var, command=self.calc_fun)
        
        #geometry
        status_label.grid(row=1, column=0, sticky='w')
        self.calculate_button.grid(row=1, column=1, sticky='e')

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=10)
        for child in self.winfo_children(): 
            child.grid_configure(padx=10, pady=10)
    
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
    
    def set_button_label(self, label: bool) -> None:
        self.button_var.set(label)
    
    def get_button_label(self) -> str:
        return self.button_var.get()

    def calc_fun(self):
        self.event_generate('<<calc-pressed>>')


class CalcNote(ttk.Frame, Router):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        Router.__init__(self, 'calc')
        
        calc_type = CalcType(self)
        setting = Setting(self)
        request = CalcRequest(self)
        
        self.add_child(calc_type)
        self.add_child(setting)
        self.add_child(request)

        # geometry
        calc_type.grid(row=0, column=0, sticky='news', padx=20, pady=10)
        setting.grid(row=1, column=0, sticky='news', padx=20, pady=10)
        request.grid(row=2, column=0, sticky='news', padx=20, pady=10)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)





