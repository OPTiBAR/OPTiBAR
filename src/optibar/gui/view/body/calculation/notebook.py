import tkinter as tk
from tkinter import ttk
from optibar.gui.view.body.tooltip import CreateToolTip
from .basic import Setting as BasicSetting
from .advanced import Setting as AdvancedSetting
from optibar.gui.view.utils.styles import CARD_PADDING


class CalcType(ttk.LabelFrame):
    def __init__(self, parent):
        ttk.LabelFrame.__init__(self, parent, text='Type of request')
        # variable and widget
        self.type_var = tk.StringVar()
        self.type_var.set('calculation')
        computation_radio = ttk.Radiobutton(self, text='Computation', cursor='question_arrow', variable=self.type_var, value='calculation', command=self.changed_fun)
        CreateToolTip(computation_radio, 'computation')
        analysis_radio = ttk.Radiobutton(self, text='Analysis', cursor='question_arrow', variable=self.type_var, value='analysis', command=self.changed_fun)
        CreateToolTip(analysis_radio, 'analysis')
        self.analysis_radio = analysis_radio
        # geometry
        computation_radio.grid(row=0, column=0, sticky='w', padx=(0, 24), pady=(4, 0))
        analysis_radio.grid(row=0, column=1, sticky='w', pady=(4, 0))

    def get_value(self):
        return self.type_var.get()

    def changed_fun(self):
        self.event_generate("<<calc-type-changed>>")
    


class Setting(ttk.Notebook):
    """the pages of the settings: Basic, Special Lengths and Strips"""
    def __init__(self, parent):
        ttk.Notebook.__init__(self, parent)
        basic = BasicSetting(self)
        self.basic = basic
        self.add(basic, text='Basic')
        # adds the Special Lengths and Strips pages
        self.advanced = AdvancedSetting(self)

        # geometry
        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)
    
    def get_values(self):
        basic = self.basic.get_values()
        advanced = self.advanced.get_values()
        basic['typical_arrangement']['exceptions'] = advanced['exceptions']
        basic['special_lengths'] = advanced['special_lengths']
        return basic

class CalcRequest(ttk.Frame):
    """the footer of the settings: the state of the run, its progress and the Calculate button"""
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)

        #variables
        self.button_var = tk.StringVar()
        self.button_var.set('Calculate')
        self.status_var = tk.StringVar()
        self.cut_var = tk.StringVar()
        self.cut_var.set('Not')

        
        #widgets
        rule = ttk.Separator(self, orient=tk.HORIZONTAL)
        status_label = ttk.Label(self, textvariable=self.status_var, style='Status.TLabel')
        self.progress = ttk.Progressbar(self, mode='determinate', length=200)
        self.calculate_button = ttk.Button(self, textvariable=self.button_var, command=self.calc_fun, style='Accent.TButton', width=16)

        #geometry
        rule.grid(row=0, column=0, columnspan=3, sticky='we', pady=(0, 12))
        status_label.grid(row=1, column=0, sticky='w')
        self.progress.grid(row=1, column=1, sticky='e', padx=(12, 12))
        self.calculate_button.grid(row=1, column=2, sticky='e', ipady=2)
        self.progress.grid_remove()

        self.columnconfigure(0, weight=1)
    
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


class SettingsPane(ttk.Frame):
    """the left pane, a card: the type of request, the settings, and the Calculate button"""
    def __init__(self, parent):
        # the gray margin to the results card; the card is inside it
        ttk.Frame.__init__(self, parent, style='App.TFrame', padding=(0, 0, 6, 0))
        card = ttk.Frame(self, style='Card.TFrame', padding=CARD_PADDING)

        title = ttk.Label(card, text='Settings', style='Section.TLabel')
        self.calc_type = CalcType(card)
        self.setting = Setting(card)
        self.request = CalcRequest(card)

        # geometry
        card.grid(row=0, column=0, sticky='news')
        title.grid(row=0, column=0, sticky='w', pady=(0, 8))
        self.calc_type.grid(row=1, column=0, sticky='news', pady=(0, 14))
        self.setting.grid(row=2, column=0, sticky='news', pady=(0, 14))
        self.request.grid(row=3, column=0, sticky='news')
        card.columnconfigure(0, weight=1)
        card.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
