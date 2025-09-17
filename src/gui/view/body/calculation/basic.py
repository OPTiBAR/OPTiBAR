from src.view.body.tooltip import CreateToolTip
from ...utils.registery import Registry
import tkinter as tk
from tkinter import ttk
from src.view.utils.common import IntCombo, IntEntry
from src.setting import REBAR_LIST
from typing import Dict, List, Tuple

class Typical(ttk.LabelFrame):
    def __init__(self, parent):
        ttk.LabelFrame.__init__(self, parent, text='Typical Arrangement')
        registry = Registry()
        registry.registery(self, 'typical')

        # widgets
        entry_label = ttk.Label(self, text='Interval(cm)'+ u' \u24BE')
        CreateToolTip(entry_label, 'interval')
        self.entry = IntEntry(self, 100)
        self.entry.set_value('20')
        entry_label.grid(row=0, column=0, sticky='w')
        self.entry.grid(row=0, column=1, sticky='w')

        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)
        self.rowconfigure(0, weight=1)
        for child in self.winfo_children(): 
            child.grid_configure(padx=20, pady=10)

    def get_values(self):
        return {
            "method": "INTERVAL",
            "value": self.entry.get_value()/100,
        }

class Setting(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        registry = Registry()
        registry.registery(self, 'basic')
        self.diameter = Diameter(self)
        self.type_num_calc = TypeNumCalc(self)
        self.type_num_analysis = TypeNumAnalysis(self)
        self.elimination = Elimination(self)
        self.typical = Typical(self)
        self.cover = Cover(self)
        self.add_child(self.typical)

        # geometry
        self.diameter.grid(row=0, column=0, rowspan=3, sticky='nwes',padx=(20,10), pady=10)
        self.elimination.grid(row=2, column=1, sticky='news',padx=10, pady=10)
        self.typical.grid(row=0, column=1,sticky='ewns',padx=10, pady=10)
        self.cover.grid(row=1, column=1,sticky='ewns',padx=10, pady=10)
        self.set_calc_layout()
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)
        self.columnconfigure(2,weight=1)
        self.rowconfigure(0,weight=1)
        self.rowconfigure(1,weight=1)
        self.rowconfigure(2,weight=1)

    def set_analysis_layout(self):
        self.type_num_calc.grid_remove()
        self.type_num_analysis.grid(row=0, column=2, rowspan=3, sticky='ewns', padx=(10,20), pady=10)

    def set_calc_layout(self):
        self.type_num_analysis.grid_remove()
        self.type_num_calc.grid(row=0, column=2, rowspan=3, sticky='ewn', padx=(10,20), pady=10)
    
    def get_values(self):
        output = {
            'diameter': self.diameter.get_values(),
            'elimination': self.elimination.get_values(),
            'side_cover': self.cover.get_value(),
            'typical_arrangement': self.typical.get_values(),
        }
        # non empty dict boolean value is True
        if self.type_num_calc.grid_info():
            output['type_number'] = self.type_num_calc.get_values()
        elif self.type_num_analysis.grid_info():
            output['type_number'] = self.type_num_analysis.get_values()
        else:
            raise Exception('It should not happen!! please investigate.')
        return output

class Elimination(ttk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text='Elimination')
        # variables
        self.additional_var = tk.DoubleVar()
        self.additional_var.set(0.2)
        self.shear_var = tk.DoubleVar()
        self.shear_var.set(2)
        
        # additional_entry = ttk.Entry(self, textvariable=self.additional_var, validate='focusout', validatecommand=check_num_wrapper)
        additional_spinbox = ttk.Spinbox(self, width=10,from_=0, to=2.0, increment=0.1, textvariable=self.additional_var)
        additional_spinbox.state(['readonly'])
        shear_spinbox = ttk.Spinbox(self, width=10, from_=0, to=5, increment=0.5, textvariable=self.shear_var)
        shear_spinbox.state(['readonly'])
        additional_label = ttk.Label(self, text='Additional(m)'+ u' \u24BE')
        CreateToolTip(additional_label, 'elim-additional')
        shear_label = ttk.Label(self, text='Shear(m)'+ u' \u24BE')
        CreateToolTip(shear_label, 'elim-shear')

        # geometry
        additional_label.grid(row=0, column=0, sticky='w')
        additional_spinbox.grid(row=0, column=1, sticky='w')
        shear_label.grid(row=1, column=0, sticky='w')
        shear_spinbox.grid(row=1, column=1, sticky='w')
        for child in self.winfo_children(): 
            child.grid_configure(padx=20, pady=20)
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0,weight=1)
        self.rowconfigure(1,weight=1)

    def get_values(self) -> Dict[str, float]:
        return {
            'additional': self.additional_var.get(),
            'shear': self.shear_var.get(),
        }


class Cover(ttk.LabelFrame):
    def __init__(self, parent):
        ttk.LabelFrame.__init__(self, parent, text='Cover')
        registry = Registry()
        registry.registery(self, 'cover')
        entry = IntEntry(self, 20)
        self.entry = entry
        label = ttk.Label(self, text='Side Cover(cm)' + u' \u24BE')
        CreateToolTip(label, 'side-cover')
        label.grid(row=0, column=0, sticky='w')
        entry.grid(row=0,column=1, sticky='w')
        entry.set_value('5')
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)
        self.rowconfigure(0,weight=1)

        for child in self.winfo_children(): 
            child.grid_configure(padx=20, pady=10)
    def get_value(self):
        return self.entry.get_value()/100


class Diameter(ttk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text='Diameter')
        values = REBAR_LIST

        self.typical_combo = IntCombo(self, values)
        self.typical_combo.set_value(18)
        self.additional_combo = IntCombo(self, values)
        self.additional_combo.set_value(25)
        self.thermal_combo = IntCombo(self, values)
        self.thermal_combo.set_value(12)
        self.shear_combo = IntCombo(self, values)
        self.shear_combo.set_value(14)

        typical_label = ttk.Label(self, text='Typical'+ u' \u24BE')
        CreateToolTip(typical_label, 'typical')
        additional_label = ttk.Label(self, text='Additional'+ u' \u24BE')
        CreateToolTip(additional_label, 'additional')
        thermal_label = ttk.Label(self, text='Thermal'+ u' \u24BE')
        CreateToolTip(thermal_label, 'thermal')
        shear_label = ttk.Label(self, text='Shear'+ u' \u24BE')
        CreateToolTip(shear_label, 'shear')

        # geometry
        typical_label.grid(row=0, column=0, sticky='w')
        self.typical_combo.grid(row=0, column=1, sticky='w')
        
        additional_label.grid(row=1, column=0, sticky='w')
        self.additional_combo.grid(row=1, column=1, sticky='w')

        thermal_label.grid(row=2, column=0, sticky='w')
        self.thermal_combo.grid(row=2, column=1, sticky='w')

        shear_label.grid(row=3, column=0, sticky='w')
        self.shear_combo.grid(row=3, column=1, sticky='w')
        
        for child in self.winfo_children(): 
            child.grid_configure(padx=20, pady=10)
        
        for i in range(4):
            self.rowconfigure(i, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
    
    def get_values(self) -> Dict[str, int]:
        return {
            'typical': self.typical_combo.get_value(),
            'additional': self.additional_combo.get_value(),
            'thermal': self.thermal_combo.get_value(),
            'shear': self.shear_combo.get_value(),
        }
    
class TypeNumCalc(ttk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text='Number of Types')
        self.total_combo = IntCombo(self, range(10,41))
        self.stack_combo = IntCombo(self, range(1,6))
        self.shear_combo = IntCombo(self, range(1,6))

        self.total_combo.set_value(20)
        self.stack_combo.set_value(2)
        self.shear_combo.set_value(4)

        total_label = ttk.Label(self, text='Total'+ u' \u24BE')
        CreateToolTip(total_label, 'total')
        stack_label = ttk.Label(self, text='Stack'+ u' \u24BE')
        CreateToolTip(stack_label, 'stack')
        shear_label = ttk.Label(self, text='Shear'+ u' \u24BE')
        CreateToolTip(shear_label, 'type-shear')

        # geometry
        total_label.grid(row=0, column=0, sticky='w')
        self.total_combo.grid(row=0, column=1, sticky='w')

        stack_label.grid(row=1, column=0, sticky='w')
        self.stack_combo.grid(row=1, column=1, sticky='w')

        shear_label.grid(row=2, column=0, sticky='w')
        self.shear_combo.grid(row=2, column=1, sticky='w')

        for child in self.winfo_children(): 
            child.grid_configure(padx=20, pady=20)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0,weight=1)
        self.rowconfigure(1,weight=1)
        self.rowconfigure(2,weight=1)

    def get_values(self) -> Dict[str,int]:
        return {
            'total': self.total_combo.get_value(),
            'stack': self.stack_combo.get_value(),
            'shear': self.shear_combo.get_value(),
        }

class TypeNumAnalysis(ttk.LabelFrame):
    class Range(ttk.LabelFrame):
        def __init__(self, parent, title: str, allowable_diff: int, allowable_range: List[int], initial_values: Tuple[int,int]):
            super().__init__(parent, text=title)
            self.allowable_diff = allowable_diff
            self.combo_from = IntCombo(self, allowable_range)
            self.combo_to = IntCombo(self, allowable_range)
            self.combo_from.set_value(initial_values[0])
            self.combo_to.set_value(initial_values[1])
            self.combo_from.bind('<<ComboboxSelected>>', self.from_fun)
            self.combo_to.bind('<<ComboboxSelected>>', self.to_fun)
            from_label = ttk.Label(self, text='From')
            to_label = ttk.Label(self, text='To')
            

            from_label.grid(row=0, column=0, sticky='w')
            self.combo_from.grid(row=0, column=1, sticky='w')
            to_label.grid(row=1, column=0, sticky='w')
            self.combo_to.grid(row=1, column=1, sticky='w')
            self.columnconfigure(0, weight=1)
            self.columnconfigure(1, weight=1)
            self.rowconfigure(0, weight=1)
            self.rowconfigure(1, weight=1)

            for child in self.winfo_children():
                child.grid_configure(padx=20, pady=20)

        def from_fun(self, e):
            if self.combo_from.get_value() > self.combo_to.get_value():
                self.combo_to.set_value(self.combo_from.get_value())
            if self.combo_from.get_value() < self.combo_to.get_value() - self.allowable_diff:
                self.combo_to.set_value(self.combo_from.get_value() + self.allowable_diff)

        def to_fun(self, e):
            if self.combo_to.get_value() < self.combo_from.get_value():
                self.combo_from.set_value(self.combo_to.get_value())
            if self.combo_to.get_value() > self.combo_from.get_value() + self.allowable_diff:
                self.combo_from.set_value(self.combo_to.get_value() - self.allowable_diff)
        def get_values(self):
            return {
                'from': self.combo_from.get_value(),
                'to': self.combo_to.get_value(),
            }

    def __init__(self, parent):
        super().__init__(parent, text='Number of Types')

        self.total_frame = self.Range(self, title = 'Total', allowable_diff=10, allowable_range= range(10,41), initial_values=(10,20))
        self.stack_frame = self.Range(self, title = 'Stack', allowable_diff=2, allowable_range= range(1,6), initial_values=(2,4))

        self.shear_combo = IntCombo(self, range(1,6))
        self.shear_combo.set_value(4)
        shear_label = ttk.Label(self, text='Shear')

        # geometry
        self.total_frame.grid(row=0, column=0, columnspan=2, sticky='nswe')
        self.stack_frame.grid(row=1, column=0, columnspan=2,  sticky='nsew')

        shear_label.grid(row=2, column=0, sticky='w')
        self.shear_combo.grid(row=2, column=1, sticky='w')

        for child in self.winfo_children():
            child.grid_configure(padx=20, pady=10)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0,weight=1)
        self.rowconfigure(1,weight=1)
        self.rowconfigure(2,weight=1)

    def get_values(self) -> Dict[str,int]:
        return {
            'total': self.total_frame.get_values(),
            'stack': self.stack_frame.get_values(),
            'shear': self.shear_combo.get_value(),
        }


