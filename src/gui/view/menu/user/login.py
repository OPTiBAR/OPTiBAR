import tkinter as tk
from tkinter import ttk

from src.view.utils.common import Popup

class LoginWindow(Popup):
    def __init__(self, root) -> None:
        Popup.__init__(self, root, title='Login')
        self.root = root
        self.bind('<Return>', self.login_fun)

        # variables
        self.email_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        self.status_var = tk.StringVar()

        # Entry
        user_entry = ttk.Entry(self.main, textvariable=self.email_var, width=30)
        pass_entry = ttk.Entry(self.main, textvariable=self.pass_var, show="*")
        user_entry.focus()
        
        #labels
        user_label = ttk.Label(self.main, text='Email')
        pass_label = ttk.Label(self.main, text='Password')
        status_label = ttk.Label(self.main, textvariable=self.status_var)
        status_label['style'] = 'error.TLabel'

        login_button = ttk.Button(self.main, text="Log in", command=self.login_fun)
        self.button = login_button

        # geometry
        user_label.grid(row=0, column=0, sticky='w')
        user_entry.grid(row=0, column=1, sticky='w')
        pass_label.grid(row=1, column=0, sticky='w')
        pass_entry.grid(row=1, column=1, sticky='w')
        status_label.grid(row=2, column=0, columnspan=2)
        login_button.grid(row=3, column=0, columnspan=2)
        for child in self.main.winfo_children(): 
            child.grid_configure(padx=10, pady=10)

    def get_values(self) -> str:
        return {
            'email': self.email_var.get(),
            'password': self.pass_var.get(),
        }
    
    def set_status(self, value: str) -> None:
        self.status_var.set(value)
    
    def set_button_state(self, state: str) -> None:
        if state == 'disabled':
            self.button.state(['disabled'])
        elif state == '!disabled':
            self.button.state(['!disabled'])
        else:
            raise Exception("state value should be disabled or !disabled")
    
    def login_fun(self, *args):
        self.root.event_generate("<<send-login>>")
    