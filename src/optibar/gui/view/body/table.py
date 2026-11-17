import tkinter as tk
from tkinter import ttk
from typing import List
import tkinter.messagebox as messagebox
from optibar.gui.view.utils.common import IntCombo
from optibar.gui.view.utils.styles import palette
from optibar.gui.setting import REBAR_LIST


class Excel(ttk.Frame):
    def __init__(self,parent):
        super().__init__(parent)

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

        self._apply_colors()
        self.bind('<<ThemeChanged>>', self._apply_colors)
        tree.configure(yscrollcommand = verscrlbar.set)
        tree.column('strip', anchor='center', width=80)
        tree.column('level', anchor='center', width=80)
        tree.column('number', anchor='center', width=80)
        tree.column('diameter', anchor='center', width=80)
        tree.heading('strip', text='Strip')
        tree.heading('level', text='Level')
        tree.heading('number', text='Number')
        tree.heading('diameter', text='Ø (mm)')
        tree.bind("<Double-1>", self.on_select)
        tree.bind("<Return>", self.on_select)

        form = ttk.Frame(self)
        self.number_label = ttk.Label(form, text='Number', anchor='w')
        self.diameter_label = ttk.Label(form, text='Ø', anchor='w')
        self.number_entry = ttk.Entry(form, width=6,  textvariable=self.number_var)
        self.diameter_combo = IntCombo(form, REBAR_LIST)
        self.diameter_combo.configure(width=5)
        self.diameter_combo.set_value(20)
        self.set_button = ttk.Button(form, text='Set', command=self.on_enter, style='Accent.TButton')
        self.delete_button = ttk.Button(form, text='Clear', command=self.on_delete)
        self.number_entry.bind("<Return>", self.on_enter)
        self.tree.bind("<Delete>", self.on_delete)


        # geometry
        tree.grid(row=0, column=0, sticky='nswe')
        verscrlbar.grid(row=0, column=1, sticky='ns', padx=(4, 0))
        form.grid(row=1, column=0, columnspan=2, sticky='we', pady=(12, 0))
        self.number_label.grid(row=0, column=0, sticky='w', padx=(0, 8))
        self.number_entry.grid(row=0, column=1, sticky='w', padx=(0, 16))
        self.diameter_label.grid(row=0, column=2, sticky='w', padx=(0, 8))
        self.diameter_combo.grid(row=0, column=3, sticky='w')
        ttk.Label(form, text='mm', style='Unit.TLabel').grid(row=0, column=4, sticky='w', padx=(6, 0))
        self.delete_button.grid(row=0, column=6, sticky='e', padx=(0, 8))
        self.set_button.grid(row=0, column=7, sticky='e')
        form.columnconfigure(5, weight=1)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def _apply_colors(self, *args) -> None:
        self.tree.tag_configure('oddrow', background=palette()['stripe'])

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
                self.value_dict.pop((strip_name, level), None) # erasing a row without a value is fine
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
