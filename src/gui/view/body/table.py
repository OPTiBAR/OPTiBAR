import tkinter as tk
from tkinter import ttk
from typing import List
import tkinter.messagebox as messagebox
from src.view.utils.common import IntCombo
from src.setting import REBAR_LIST
    
        
class Excel(ttk.LabelFrame):
    def __init__(self,parent):
        super().__init__(parent, text='Strips')
        
        # variables
        self.selected_strip_name_var = tk.StringVar()
        self.selected_level_var = tk.StringVar()
        self.number_var = tk.StringVar()
        
        # widgets
        tree = ttk.Treeview(self, columns=['strip', 'level', 'number', 'diameter'], height=5, selectmode='browse')
        tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree = tree

        tree['show'] = 'headings'
        verscrlbar = ttk.Scrollbar(self, orient ="vertical", command = tree.yview)

        
        # https://stackoverflow.com/a/60949800
        style = ttk.Style()
        def fixed_map(option):
            # Returns the style map for 'option' with any styles starting with
            # ("!disabled", "!selected", ...) filtered out

            # style.map() returns an empty list for missing options, so this should
            # be future-safe
            return [elm for elm in style.map("Treeview", query_opt=option)
                    if elm[:2] != ("!disabled", "!selected")]
        style.map(
            "Treeview", 
            foreground=fixed_map("foreground"),
            background=fixed_map("background")
        )
        
        tree.tag_configure('oddrow', background='#EEEEEE')
        tree.configure(yscrollcommand = verscrlbar.set)
        tree.column('strip', anchor='center', width=50)
        tree.column('level', anchor='center', width=50)
        tree.column('number', anchor='center', width=50)
        tree.column('diameter', anchor='center', width=50)
        tree.heading('strip', text='Strip')
        tree.heading('level', text='Level')
        tree.heading('number', text='Number')
        tree.heading('diameter', text='Diameter')
        tree.bind("<Double-1>", self.on_select)
        tree.bind("<Return>", self.on_select)

        self.number_label = ttk.Label(self, text='Number', anchor='w')
        self.diameter_label = ttk.Label(self, text='Diameter', anchor='w')
        self.number_entry = ttk.Entry(self,width=10,  textvariable=self.number_var)
        self.diameter_combo = IntCombo(self, REBAR_LIST)
        self.diameter_combo.set_value(20)
        self.set_button = ttk.Button(self, text='Set', command=self.on_enter)
        self.delete_button = ttk.Button(self, text='Erase', command=self.on_delete)
        self.number_entry.bind("<Return>", self.on_enter)
        self.tree.bind("<Delete>", self.on_delete)

        
        # geometry
        tree.grid(row=0, column=0,columnspan=4, sticky='nswe', pady=10, padx=(10,0))
        verscrlbar.grid(column=4,row=0,sticky='nsw', pady=10, padx=(0,10))
        self.number_label.grid(row=1,column=0, sticky='nsw', padx=(10,2), pady=10)
        self.number_entry.grid(row=1,column=1,  sticky='nsw', pady=10, padx=(2,10))
        self.diameter_label.grid(row=1,column=2,  sticky='nse', pady=10, padx=(10,2))
        self.diameter_combo.grid(row=1,column=3,  sticky='nsw', pady=10, padx=(2,10))
        self.delete_button.grid(row=2,column=2,  sticky='nsw', pady=10, padx=10)
        self.set_button.grid(row=2,column=3,  sticky='nsw', pady=10, padx=10)
        
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1,weight=1)
        self.columnconfigure(2, weight=0)
        self.columnconfigure(3,weight=1)
        self.rowconfigure(0, weight=1)
        
    def set_labels(self, labels: List[str]):
        labels = sorted(labels)
        self.value_dict = {}
        self.selected_strip_name_var.set('')
        self.labels = labels
        tree = self.tree
        for row in tree.get_children():
            tree.delete(row)
        i = 0
        for label in labels:
            for level in ('Top', 'Bottom'):
                if i%2 == 0:
                    tree.insert("", "end", values=(label,level),tags = ('oddrow',))
                else:
                    tree.insert("", "end", values=(label,level))
                i += 1
    
    def on_select(self, e):
        item = self.tree.selection()[0]
        self.selected_strip_name_var.set(self.tree.item(item,"values")[0])
        self.selected_level_var.set(self.tree.item(item, "values")[1])
        # self.number_entry.focus()
    
    def validate_entry(self):
        try:
            value = int(self.number_var.get())
            if value < 0:
                messagebox.showerror(title='Positive number', message= 'The number of rebars should be a non-negative number.')
                return False
        except:
            messagebox.showerror(title='Integer number', message= 'The number should be an Integer.')
            return False
        return True
        
        
    def _set_values(self, number, diameter):
        tree = self.tree
        strip_name = self.selected_strip_name_var.get()
        level = self.selected_level_var.get()
        if (strip_name in self.labels):
            if number=='' and diameter=='':
                del self.value_dict[(strip_name, level)]
            else:
                self.value_dict[(strip_name, level)] = {'number':number, 'diameter': diameter}
            for i,row in enumerate(self.tree.get_children()):
                values = tree.item(row)['values']
                if (strip_name == values[0] and level == values[1]):
                    tree.delete(row)
                    if i%2 == 0 :
                        inserted_id = tree.insert("", i, values=(strip_name, level, number, diameter),tags = ('oddrow',))
                    else:
                        inserted_id = tree.insert("", i, values=(strip_name, level, number, diameter))
                    
                    tree.focus(inserted_id)
                    tree.selection_set(inserted_id)
                    break

    def on_delete(self, e=None):
        new_number = ''
        new_diameter = ''
        self._set_values(new_number, new_diameter)

    def on_enter(self, e=None):
        if not self.validate_entry():
            return None
        new_number = int(self.number_var.get())
        new_diameter = self.diameter_combo.get_value()
        self._set_values(new_number, new_diameter)       

    def get_values(self):
        return self.value_dict
