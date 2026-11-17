from optibar.gui.view.body.table import Excel
from optibar.gui.view.body.tooltip import ToolTip
import tkinter as tk
from tkinter import ttk
from optibar.gui.view.utils.common import IntEntry
from typing import List, Dict
from optibar.gui.setting import REBAR_LIST

class Setting():
    """the advanced settings, as two pages of the settings notebook: Special Lengths and Strips"""
    def __init__(self, notebook: ttk.Notebook):
        self.special_length = SpecialLength(notebook)
        self.typical = Typical(notebook)
        notebook.add(self.special_length, text='Special Lengths')
        notebook.add(self.typical, text='Strips')

    def get_values(self):
        return {
            'special_lengths': self.special_length.get_values(),
            'exceptions': self.typical.get_values()
        }

class Typical(ttk.Frame):
    """the Strips page: the typical rebars of single strips and levels, by number and diameter"""
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent, padding=(2, 12, 2, 4))

        title = ttk.Label(self, text='Typical rebars by strip', style='TLabelframe.Label')
        # a fixed width: wrapping to the page would widen the page, and the hint again
        hint = ttk.Label(self, style='Muted.TLabel', justify='left', wraplength=440,
            text='Select a strip and level, then set the number and diameter of its typical rebars. '
                 'They replace the interval of the Basic page for that strip and level.')
        self.table = Excel(self)

        # geometry
        title.grid(row=0, column=0, sticky='w')
        hint.grid(row=1, column=0, sticky='w', pady=(2, 10))
        self.table.grid(row=2, column=0, sticky='ewns')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

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


class SpecialLength(ttk.Frame):
    """the Special Lengths page: the development length, overlap and bend of each bar diameter"""
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent, padding=(2, 12, 2, 4))
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
                    entries[item][subitem][rebar].configure(width=5)

        self.material_var = tk.StringVar(self)
        self.material_var.set('Concrete and steel: open a file first')
        title = ttk.Label(self, text='Lengths by bar diameter (cm)', style='TLabelframe.Label')
        material_label = ttk.Label(self, textvariable=self.material_var, style='Muted.TLabel')
        ld_label = ttk.Label(self, text='Ld', style='TLabelframe.Label')
        overlap_label = ttk.Label(self, text='Overlap', style='TLabelframe.Label')
        bend_label = ttk.Label(self, text='Bend', style='TLabelframe.Label')

        check_var = tk.BooleanVar(self, False)
        self.check_var = check_var
        check = ttk.Checkbutton(self, text='Automatic', cursor='question_arrow',
                command=lambda: self.event_generate('<<check-changed>>'), variable=check_var,
                onvalue=True, offvalue=False
            )
        ToolTip(check, 'The top Ld and the overlaps follow from the bottom Ld; only the bottom Ld and the bends stay editable.')
        reset_button = ttk.Button(self, command=lambda: self.event_generate('<<reset-pressed>>'), text='Reset to code values')

        # geometry
        title.grid(row=0, column=0, columnspan=7, sticky='w')
        material_label.grid(row=1, column=0, columnspan=7, sticky='w', pady=(2, 10))
        ld_label.grid(row=2, column=1, columnspan=2, sticky='w', padx=(10, 0), pady=(0, 2))
        overlap_label.grid(row=2, column=3, columnspan=2, sticky='w', padx=(10, 0), pady=(0, 2))
        bend_label.grid(row=2, column=5, columnspan=2, sticky='w', padx=(10, 0), pady=(0, 2))
        ttk.Label(self, text='Ø mm', style='Muted.TLabel').grid(row=3, column=0, padx=(0, 6), pady=(0, 4), sticky='e')
        for i, column in enumerate(column_names):
            ttk.Label(self, text=column, style='Muted.TLabel').grid(row=3, column=i+1, sticky='w',
                padx=(10, 2) if i % 2 == 0 else (2, 10), pady=(0, 4))

        for i, rebar in enumerate(REBAR_LIST):
            ttk.Label(self, text=str(rebar)).grid(row=i+4, column=0, padx=(0, 6), sticky='e')
        
        for i,rebar in enumerate(REBAR_LIST):
            j = 0
            for item in entries:
                for subitem in entries[item]:
                    self.entries[item][subitem][rebar].grid(row=i+4, column=j+1, pady=2)
                    if j%2 == 0:
                        self.entries[item][subitem][rebar].grid(padx=(10,2))
                    else:
                        self.entries[item][subitem][rebar].grid(padx=(2,10))
                    j += 1

        check.grid(row=len(REBAR_LIST)+4, column=1, columnspan=3, sticky='w', padx=8, pady=(12, 0))
        reset_button.grid(row=len(REBAR_LIST)+4, column=4, columnspan=3, padx=(0, 10), pady=(12, 0), sticky='e')
        # the diameter column keeps its width; the entry columns share the rest
        self.columnconfigure(0, weight=0)
        for j in range(1, len(column_names)+1):
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
        self.material_var.set(f"Concrete f'c {round(fc)} tonf/m²  ·  Steel fy {round(fy)} tonf/m²")