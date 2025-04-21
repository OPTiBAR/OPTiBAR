from tkinter import ttk
import tkinter as tk
from typing import Dict, List, Text, Union
import jdatetime
from datetime import datetime, timezone
# import pytz
from copy import deepcopy
from src.view.utils.common import Popup
    

class DashboardWindow(Popup):
    def __init__(self, root) -> None:
        Popup.__init__(self, root, title='Dashboard')
        self.root = root
        main = self.main

        notebook = ttk.Notebook(main)
        notebook.grid(sticky='ewns')
        main.columnconfigure(0, weight=1)
        main.rowconfigure(0, weight=1)

        profile = Profile(notebook)
        payment = Payment(notebook, root)

        profile.grid(sticky='ewns')
        payment.grid(sticky='ewns')

        notebook.add(profile, text='Profile')
        notebook.add(payment, text='Payment')

        self.profile = profile
        self.payment = payment
        

class Payment(ttk.Frame):
    def __init__(self, parent, root) -> None:
        ttk.Frame.__init__(self,parent)

        self.choice_frame = ttk.LabelFrame(self, text='Choices')
        self.choice_frame.grid(row=0, column=0, columnspan=2, sticky='ensw')

        # self.status_var = tk.StringVar()
        # status = ttk.Label(self, textvariable=self.status_var)
        # status.grid(row=2, column=0)

        pay_button = ttk.Button(self, text='pay', command=lambda: root.event_generate("<<pay-pressed>>"))
        pay_button.grid(row=2, column=0, columnspan=2)
        self.pay_button = pay_button

        self.choice_var = tk.StringVar()

        self.coupon_var = tk.StringVar()
        coupon_entry = ttk.Entry(self, textvariable=self.coupon_var)
        coupon_button = ttk.Button(self, text='check', command=lambda: root.event_generate("<<coupon-pressed>>"))
        coupon_entry.grid(row=1, column=0)
        coupon_button.grid(row=1, column=1)
        self.coupon_button = coupon_button

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)


        for child in self.winfo_children(): 
            child.grid_configure(padx=10, pady=10)

    def set_original_choices(self, choices):
        # keep original data
        self.choices = choices
    
    def set_values(self, choices: List[Dict[str, Union[str,int]]]):
        """sets the choices for payment

        Args:
            choices (List[Dict[str, Union[str,int]]]): a list of dicts, each dict should have keys: name, price, val
        """

        # remove all choices
        # for child in self.choice_frame.winfo_children():
        #     child.remove_grid()
        # initialize
        ttk.Label(self.choice_frame, text='(ماه)مدت دوره').grid(row=0, column=0)
        ttk.Label(self.choice_frame, text='Price(تومان)').grid(row=0, column=1)

        self.choice_var.set(choices[0]['duration'])
        self.choice_frame.columnconfigure(0,weight=1)
        self.choice_frame.columnconfigure(1,weight=1)
        for i, choice in enumerate(choices):
            ttk.Radiobutton(self.choice_frame, variable=self.choice_var, text=choice['duration'], value=choice['duration']).grid(row=i+1, column=0)
            ttk.Label(self.choice_frame, text="{:,.0f}".format(choice['price']/10)).grid(row=i+1, column=1)
            self.choice_frame.rowconfigure(i,weight=1)
        
        for child in self.choice_frame.winfo_children(): 
            child.grid_configure(padx=10, pady=10)

    def get_discounted_prices(self, discount_percentage):
        choices = deepcopy(self.choices)
        for choice in choices:
            choice['price'] *= (1-discount_percentage/100)
        return choices

    def get_choice(self):
        return self.choice_var.get()
    
    def get_coupon(self):
        return self.coupon_var.get()
    
    def set_status(self, value: str) -> None:
        self.status_var.set(value)
    
    def set_pay_button_state(self, state: str) -> None:
        if state == 'disabled':
            self.pay_button.state(['disabled'])
        elif state == '!disabled':
            self.pay_button.state(['!disabled'])
        else:
            raise Exception("state value should be disabled or !disabled")
    
    def set_coupon_button_state(self, state: str) -> None:
        if state == 'disabled':
            self.coupon_button.state(['disabled'])
        elif state == '!disabled':
            self.coupon_button.state(['!disabled'])
        else:
            raise Exception("state value should be disabled or !disabled")


class Profile(ttk.Frame):
    def __init__(self, parent) -> None:
        ttk.Frame.__init__(self,parent)

        # variables
        self.first_name_var = tk.StringVar()
        self.first_name_var.set(' ' * 20)
        self.last_name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.service_level_var = tk.StringVar()
        self.expire_date_var = tk.StringVar()
        
        #labels
        first_name_label = ttk.Label(self, text='First Name')
        last_name_label = ttk.Label(self, text='Last Name')
        email_label = ttk.Label(self, text='Email')
        service_level_label = ttk.Label(self, text='Service Level')
        expire_date_label = ttk.Label(self, text='Expire')

        first_name = ttk.Label(self, textvariable=self.first_name_var)
        last_name = ttk.Label(self, textvariable=self.last_name_var)
        email = ttk.Label(self, textvariable=self.email_var)
        service_level = ttk.Label(self, textvariable=self.service_level_var)
        expire_date = ttk.Label(self, textvariable=self.expire_date_var)


        # geometry
        first_name_label.grid(row=0, column=0, sticky='w')
        first_name.grid(row=0, column=1, sticky='w')
        last_name_label.grid(row=1, column=0, sticky='w')
        last_name.grid(row=1, column=1, sticky='w')
        email_label.grid(row=2, column=0, sticky='w')
        email.grid(row=2, column=1, sticky='w')
        service_level_label.grid(row=3, column=0, sticky='w')
        service_level.grid(row=3, column=1, sticky='w')
        expire_date_label.grid(row=4, column=0, sticky='w')
        expire_date.grid(row=4, column=1, sticky='w')

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(4, weight=1)
        
        for child in self.winfo_children(): 
            child.grid_configure(padx=15, pady=15)
    
    def set_values(self, values: Dict) -> None:
        self.first_name_var.set(values['first_name'])
        self.last_name_var.set(values['last_name'])
        self.email_var.set(values['email'])
        self.service_level_var.set(values['service_level'])
        if values['expire'] is not None:
            ex = datetime.strptime(values['expire'], '%Y-%m-%dT%H:%M:%SZ')
            # utctz = pytz.timezone('UTC')
            # irantx = pytz.timezone('Asia/Tehran')
            # ex = utctz.localize(ex)
            
            tzinfo = datetime.now().astimezone().tzinfo
            ex = ex.astimezone(tzinfo)
            self.expire_date_var.set(str(jdatetime.date.fromgregorian(day=ex.day, month=ex.month, year=ex.year)) + '  ' + str(ex.strftime('%H:%M')))

