import tkinter as tk
from tkinter import ttk

from src.view.utils.common import Popup

class PassResetWindow(Popup):
    def __init__(self, root) -> None:
        Popup.__init__(self, root, title='Sign up')
        self.root = root
        self.bind('<Return>', self.pass_reset_fun)
        main = self.main

        # variables
        self.email_var = tk.StringVar()
        self.status_var = tk.StringVar()

        # Entry
        email_entry = ttk.Entry(main, textvariable=self.email_var)
        email_entry.focus()
        
        #labels
        email_label = ttk.Label(main, text='Email')
        status_label = ttk.Label(main, textvariable=self.status_var)
        status_label['style'] = 'error.TLabel'

        send_button = ttk.Button(main, text="Send", command=self.pass_reset_fun)
        self.button = send_button

        # geometry
        main.grid(sticky='nsew')
        email_label.grid(row=0, column=0, sticky='w')
        email_entry.grid(row=0, column=1, sticky='w')
        status_label.grid(row=2, column=0, columnspan=2)
        send_button.grid(row=3, column=0, columnspan=2)
        for child in main.winfo_children(): 
            child.grid_configure(padx=10, pady=10)

    def get_values(self) -> str:
        return {
            'email': self.email_var.get(),
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

    def pass_reset_fun(self, *args):
        self.root.event_generate("<<send-password-reset>>")

class VerifyWindow(Popup):
    def __init__(self, root) -> None:
        Popup.__init__(self, root, title='Verify Email')
        self.root = root
        self.bind('<Return>', self.verify_fun)
        main = self.main

        # variables
        self.code_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        self.pass_confirm_var = tk.StringVar()
        self.status_var = tk.StringVar()

        # Entry
        code_entry = ttk.Entry(main, textvariable=self.code_var)
        pass_entry = ttk.Entry(main, textvariable=self.pass_var, show="*")
        pass_confirm_entry = ttk.Entry(main, textvariable=self.pass_confirm_var, show="*")
        code_entry.focus()
        
        #labels
        code_label = ttk.Label(main, text='Code')
        pass_label = ttk.Label(main, text='Password')
        pass_confirm_label = ttk.Label(main, text='Confirm Password')
        status_label = ttk.Label(main, textvariable=self.status_var)
        status_label['style'] = 'error.TLabel'

        verify_button = ttk.Button(main, text="Verify", command=self.verify_fun)
        self.button = verify_button

        # geometry
        main.grid(sticky='nsew')
        code_label.grid(row=1, column=0, sticky='w')
        code_entry.grid(row=1, column=1, sticky='w')
        pass_label.grid(row=2, column=0, sticky='w')
        pass_entry.grid(row=2, column=1, sticky='w')
        pass_confirm_label.grid(row=3, column=0, sticky='w')
        pass_confirm_entry.grid(row=3, column=1, sticky='w')
        status_label.grid(row=4, column=0, columnspan=2)
        verify_button.grid(row=5, column=0, columnspan=2)
        for child in main.winfo_children(): 
            child.grid_configure(padx=10, pady=10)

    def get_values(self) -> str:
        return {
            'code': self.code_var.get(),
            'password1': self.pass_var.get(),
            'password2': self.pass_confirm_var.get(),
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

    def verify_fun(self, *args):
        self.root.event_generate("<<send-verify>>")