from src.view.body.table import Excel
import tkinter as tk
from tkinter import ttk
from src.view.utils.common import IntEntry
from typing import List, Dict
from src.setting import REBAR_LIST
from ...utils.registery import Registry

class Setting(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        registry = Registry()
        registry.registery(self, 'advanced')
        self.special_length = SpecialLength(self)
        self.typical = Typical(self)
        self.add_child(self.special_length)
        self.add_child(self.typical)
        self.special_length.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        self.typical.grid(row=0, column=1, padx=10, pady=10, sticky='nswe')

        # geometry
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)
        self.rowconfigure(0,weight=1)
    def get_values(self):
        return {
            'special_lengths': self.special_length.get_values(),
            'exceptions': self.typical.get_values()
        }

class Typical(ttk.LabelFrame):
    def __init__(self, parent):
        ttk.LabelFrame.__init__(self, parent, text='Typical Arrangement')
        registry = Registry()
        registry.registery(self, 'typical')
        
        self.table = Excel(self)
        
        # geometry

        self.table.grid(row=1,column=0, columnspan=2, sticky='ewns')
        for child in self.winfo_children(): 
            child.grid_configure(padx=15, pady=10)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1,weight=1)
        self.rowconfigure(1, weight=1)
    
    def set_strip_names(self, strip_names: List):
        self.table.set_labels(strip_names)

    def get_values(self):
        exceptions_dict  = self.table.get_values()
        exceptions = []
        for (strip_name, level) in exceptions_dict:
            exceptions.append({
                'strip_name': strip_name,
                'level': str.lower(level),
                'method': 'COUNT',
                'value': exceptions_dict[(strip_name, level)]['number'],
                'diameter': exceptions_dict[(strip_name, level)]['diameter'],
            })
        return exceptions


class SpecialLength(ttk.LabelFrame):
    def __init__(self, parent):
        ttk.LabelFrame.__init__(self, parent, text='Special Lengths')
        # Router.__init__(self, 'special-lengths')
        column_names = (
            'Bottom',
            'Top',
            'Bottom',
            'Top',
            '90\u00B0',
            '135\u00B0',
        )
        
        entries = {
            'ld': {
                'bottom': {},
                'top': {},
            },
            'overlap': {
                'bottom': {},
                'top': {},
            },
            'bend': {
                'B90': {},
                'B135': {},
            }
        }
        self.entries = entries
        for item in entries:
            if item == 'bend':
                upper_bound = 100
            else:
                upper_bound = 400
            for subitem in entries[item]:
                for rebar in REBAR_LIST:
                    entries[item][subitem][rebar] = IntEntry(self, upper_bound)
        
        self.material_var = tk.StringVar(self)
        self.material_var.set(f"fc: {''.ljust(10)}, f'y:{''.ljust(10)}")
        material_label = ttk.Label(self, textvariable=self.material_var)
        ld_label = ttk.Label(self, text='Ld(cm)')
        overlap_label = ttk.Label(self, text='Overlap(cm)')
        bend_label = ttk.Label(self, text='Bend(cm)')

        check_var = tk.BooleanVar(self, False)
        self.check_var = check_var
        check = ttk.Checkbutton(self, text='Automatic', 
                command=lambda: self.event_generate('<<check-changed>>'), variable=check_var,
                onvalue=True, offvalue=False
            )
        reset_button = ttk.Button(self, command=lambda: self.event_generate('<<reset-pressed>>'), text='Reset')

        # geometry
        material_label.grid(row=0, column=1, columnspan=6, padx=10, pady=10, sticky='w')
        ld_label.grid(row=1, column=1, columnspan=2, pady=10)
        overlap_label.grid(row=1, column=3, columnspan=2, pady=10)
        bend_label.grid(row=1, column=5, columnspan=2, pady=10)
        for i, column in enumerate(column_names):
            ttk.Label(self, text=column).grid(row=2, column=i+1, pady=2)
        
        for i, rebar in enumerate(REBAR_LIST):
            ttk.Label(self, text=str(rebar)).grid(row=i+3, column=0, padx=10, sticky='e')
        
        for i,rebar in enumerate(REBAR_LIST):
            j = 0
            for item in entries:
                for subitem in entries[item]:
                    self.entries[item][subitem][rebar].grid(row=i+3, column=j+1, pady=2)
                    if j%2 == 0:
                        self.entries[item][subitem][rebar].grid(padx=(10,2))
                    else:
                        self.entries[item][subitem][rebar].grid(padx=(2,10))
                    j += 1
        
        reset_button.grid(row=len(REBAR_LIST)+3, column=len(column_names)-1, columnspan=2, padx=10, pady=10, sticky='e')
        check.grid(row=len(REBAR_LIST)+3, column=1, columnspan=2, sticky='w', padx=8, pady=10)

        for i in range(len(REBAR_LIST)+4):
            self.rowconfigure(i,weight=1)
        for j in range(len(column_names)+1):
            self.columnconfigure(j,weight=1)
            
    def get_checked(self):
        return self.check_var.get()
    
    def get_values(self) -> Dict[str, Dict[int, int]]:
        output = {
            'diameters': REBAR_LIST
        }
        for item in self.entries:
            output[item] = {}
            for subitem in self.entries[item]:
                output[item][subitem] = []
                for rebar in self.entries[item][subitem]:
                    output[item][subitem].append(self.entries[item][subitem][rebar].get_value()/100)
        return output

    def set_values(self, values: Dict[str, Dict[str,Dict[int, int]]]) -> None:
        for item in values:
            for subitem in values[item]:
                for rebar in values[item][subitem]:
                    self.entries[item][subitem][rebar].set_value(round(values[item][subitem][rebar]*100)) 
    
    def set_columns_state(self, state: str):
        for item,subitem in (('ld', 'top'), ('overlap', 'bottom'), ('overlap', 'top')):
            for rebar in REBAR_LIST:
                self.entries[item][subitem][rebar]['state'] = state
    
    def set_material(self, fy:float, fc:float) -> None:
        self.material_var.set(f"fc: {str(round(fc)).ljust(10)}(tonf/m^2),\t f'y:{str(round(fy)).ljust(10)}(tonf/m^2)")