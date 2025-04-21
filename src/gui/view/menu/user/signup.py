import tkinter as tk
from tkinter import ttk

from src.view.utils.common import Popup

class SignupWindow(Popup):
    def __init__(self, root) -> None:
        Popup.__init__(self, root, title='Sign up')
        self.root = root
        self.bind('<Return>', self.signup_fun)
        main = self.main

        # variables
        self.first_name_var = tk.StringVar()
        self.last_name_var = tk.StringVar() 
        self.email_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        self.pass_confirm_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.phone_var = tk.StringVar()

        # Entry
        user_entry = ttk.Entry(main, textvariable=self.email_var, width=30)
        first_name_entry = ttk.Entry(main, textvariable=self.first_name_var)
        last_name_entry = ttk.Entry(main, textvariable=self.last_name_var)
        phone_entry = ttk.Entry(main, textvariable=self.phone_var)
        pass_entry = ttk.Entry(main, textvariable=self.pass_var, show="*")
        pass_confirm_entry = ttk.Entry(main, textvariable=self.pass_confirm_var, show="*")
        user_entry.focus()
        
        #labels
        user_label = ttk.Label(main, text='Email')
        first_name_label = ttk.Label(main, text='First Name')
        last_name_label = ttk.Label(main, text='Last Name')
        phone_label = ttk.Label(main, text='Phone')
        pass_label = ttk.Label(main, text='Password')
        pass_confirm_label = ttk.Label(main, text='Confirm Password')
        status_label = ttk.Label(main, textvariable=self.status_var)
        status_label['style'] = 'error.TLabel'

        signup_button = ttk.Button(main, text="Sign up", command=self.signup_fun)
        self.button = signup_button

        # geometry
        user_label.grid(row=0, column=0, sticky='w')
        user_entry.grid(row=0, column=1, sticky='w')
        first_name_label.grid(row=1, column=0, sticky='w')
        first_name_entry.grid(row=1, column=1, sticky='w')
        last_name_label.grid(row=2, column=0, sticky='w')
        last_name_entry.grid(row=2, column=1, sticky='w')
        phone_label.grid(row=3, column=0, sticky='w')
        phone_entry.grid(row=3, column=1, sticky='w')
        pass_label.grid(row=4, column=0, sticky='w')
        pass_entry.grid(row=4, column=1, sticky='w')
        pass_confirm_label.grid(row=5, column=0, sticky='w')
        pass_confirm_entry.grid(row=5, column=1, sticky='w')
        status_label.grid(row=6, column=0, columnspan=2)
        signup_button.grid(row=7, column=0, columnspan=2)
        for child in self.main.winfo_children(): 
            child.grid_configure(padx=10, pady=10)

    def get_values(self) -> str:
        return {
            'email': self.email_var.get(),
            'first_name': self.first_name_var.get(),
            'last_name': self.last_name_var.get(),
            'password1': self.pass_var.get(),
            'password2': self.pass_confirm_var.get(),
            'phone_num': self.phone_var.get(),
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
    
    def signup_fun(self, *args):
        self.root.event_generate("<<send-signup>>")