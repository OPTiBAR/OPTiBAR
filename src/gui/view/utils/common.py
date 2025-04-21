from functools import update_wrapper
import tkinter as tk
from tkinter import ttk
from typing import List
from .router import Router
import tkinter.messagebox as messagebox

INDENT = 4

class LogWindow(ttk.LabelFrame, Router):
    def __init__(self, parent):
        ttk.LabelFrame.__init__(self, parent, text='Report')
        Router.__init__(self, 'log')

        text = tk.Text(self, wrap= "none", width=40)
        # text['state'] = 'disabled'
        self.text = text
        yscroll = ttk.Scrollbar(self, orient = 'vertical', command = text.yview)
        xscroll = ttk.Scrollbar(self, orient = 'horizontal', command = text.xview)
        text['yscrollcommand'] = yscroll.set
        text['xscrollcommand'] = xscroll.set
        text.grid(column = 0, row = 0, sticky = 'nwes', pady=(20,0), padx=(20,0))
        xscroll.grid(column = 0, row = 1, sticky = 'we', padx=(20,0), pady=(0,20))
        yscroll.grid(column = 1, row = 0, sticky = 'ns', padx=(0,20), pady=(20,0))
        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(1, weight = 0)
        self.grid_rowconfigure(1, weight = 0)

        # tag configuration
        text.tag_configure('ERROR', foreground='red')
        text.tag_configure('WARNING', foreground='#9B870C')
        text.tag_configure('SUCCESS', foreground='green')
        text.tag_configure('INFO', foreground='black')
    
    def clear(self) -> None:
        self.text['state'] = 'normal'
        self.text.delete('1.0', 'end')
        self.text['state'] = 'disabled'
    
    def write_success(self, data_str: str, indent:int=0) -> None:
        self._write(data_str, 'SUCCESS', indent)

    def write_info(self, data_str: str, indent: int = 0) -> None:
        self._write(data_str, 'INFO', indent)

    def write_error(self, data_str: str, indent:int = 0) -> None:
        self._write(data_str, 'ERROR', indent)

    def write_warning(self, data_str: str, indent:int = 0) -> None:
        self._write(data_str, 'WARNING', indent)

    def _write(self, data_str: str, tag:str, indent: int):
        self.text['state'] = 'normal'
        info_str = indent * INDENT * ' ' + data_str
        self.text.insert('end', info_str+'\n', tag)
        self.text['state'] = 'disabled'


class Popup():
    def __init__(self,root,title) -> None:
        # it needs that root should be registered
        window = tk.Toplevel(root)
        window.title(title)
        self._window = window
        main = ttk.Frame(self._window)
        main.grid(sticky='nsew')
        self.main = main
        window.grid_columnconfigure(0, weight=1)
        window.grid_rowconfigure(0, weight=1)


        # the position of top left corner of the popup relative to the root window
        x = root.winfo_x()
        width = root.winfo_width()
        y = root.winfo_y()
        height = root.winfo_height()
        window.geometry("+%d+%d" % (x + width * .4, y + height * .2))

        window.protocol("WM_DELETE_WINDOW", self.close) # intercept close button
        window.transient(root) # dialog window is related to main
        window.wait_visibility() # can't grab until window appears, so we wait
        window.grab_set() # ensure all input goes to our window
        # window.wait_window()

    def close(self):
        self._window.grab_release()
        self._window.destroy()

    def is_live(self):
        try:
            self._window.winfo_name()
            return True
        except:
            return False

    def bind(self, event, fun):
        self._window.bind(event, fun)

class IntCombo(ttk.Combobox):
    def __init__(self, parent, values):
        super().__init__(parent, width=10)
        self.int_var = tk.IntVar()
        self['textvariable'] = self.int_var
        self.state(["readonly"])
        self.set_values(values)

    def set_values(self, values: List[int]) -> None:
        self['values'] = list(values)

    def get_value(self) -> int:
        return self.int_var.get()
    
    def set_value(self, value: int) -> None:
        return self.int_var.set(value)

class IntEntry(ttk.Entry):
    def __init__(self, parent, upper_bound:float = float('inf')):
        super().__init__(parent, width=10,  validate="focusout", validatecommand=self.validate_entry)
        self.upper_bound = upper_bound
        self.str_var = tk.StringVar()
        self['textvariable'] = self.str_var
        self.last_valid = ''
    
    def set_value(self, value: str) -> None:
        self.str_var.set(value)
        self.last_valid = value
    
    def get_value(self) -> int:
        return int(self.str_var.get())
    
    def set_state(self, state: str) -> None:
        if state == 'disabled':
            pass
        elif state == '!disabled':
            pass
        else:
            raise ValueError('state value is not valid')
    
    def _valid(self, value: str) -> bool:
        try:
            int_value = int(value)
            if 0 < int_value < self.upper_bound:
                return True
            else:
                return False
        except:
            return False
    
    def validate_entry(self):
        value = self.str_var.get()
        if self._valid(value):
            self.set_value(str(int(value)))
            return True
        else:
            self.set_value(self.last_valid)
            return False
            

        
