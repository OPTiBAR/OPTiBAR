from src.view.menu.user.dashboard import DashboardWindow
import requests
from tkinter.messagebox import showerror, showinfo
from src.control.utils.urls import get_url, get_header, connection_error
from src.control.utils.threading import tr_request, Monitor
import webbrowser

class Dashboard():
    def __init__(self, root, token_var) -> None:
        self.root = root
        self.token_var = token_var
        self.monitor = Monitor(root)

    def open(self,*args):
        def handle_profile(response: requests.Response):
            if self.window.is_live():
                if response is not None:
                    if  response.status_code == 200:
                        self.window.profile.set_values(response.json())
                    else:
                        if response.status_code == 401:
                            print('You are not authorized.')
                        else:
                            raise ValueError(f'unhandled status code {response.status_code}')
                else:
                    connection_error()

        def handle_price(response: requests.Response):
            if self.window.is_live():
                if response is not None:
                    if response.status_code == 200:
                        self.window.payment.set_original_choices(response.json())
                        self.window.payment.set_values(response.json())
                    else:
                        raise ValueError(f'unhandled status code {response.status_code}')
                else:
                    connection_error()
                    
        
        self.window =DashboardWindow(self.root)
        profile_thread = tr_request(method='get', url=get_url('profile'), headers=get_header(self.token_var))
        price_thread = tr_request(method='get', url=get_url('price'), headers=get_header(self.token_var))
        self.monitor.run(profile_thread, handle_profile)
        self.monitor.run(price_thread, handle_price)
    
    def send_pay(self, *args):
        def handle(response: requests.Response):
            if self.window.is_live():
                self.window.payment.set_pay_button_state('!disabled')
                if response is not None:
                    if response.status_code == 200:
                        url = response.json()['url']
                        webbrowser.open(url)
                    elif response.status_code == 400:
                        showerror('Payment problem', response.json()['detail'])
                    else:
                        raise ValueError(f'unhandled status code {response.status_code}')
                else:
                    connection_error()
        data = {
            'months': int(self.window.payment.get_choice()),
            'service_level': 'GOLD',
            'coupon': self.window.payment.get_coupon(),
        }
        pay_thread = tr_request(method='post', url=get_url('pay'), headers=get_header(self.token_var), json=data)
        self.window.payment.set_pay_button_state('disabled')
        self.monitor.run(pay_thread, handle)
    
    def send_coupon(self, *args):
        def handle(response: requests.Response):
            if self.window.is_live():
                self.window.payment.set_coupon_button_state('!disabled')
                if response is not None:
                    if response.status_code == 200:
                        percentage = response.json()['percentage']
                        choices = self.window.payment.get_discounted_prices(percentage)
                        self.window.payment.set_values(choices)
                        showinfo('Valid Coupon', 'The coupon is valid and {}% discount is considered in the prices.'.format(percentage))
                    elif response.status_code == 404:
                        choices = self.window.payment.get_discounted_prices(0)
                        self.window.payment.set_values(choices)
                        showerror('Invalid Coupon', 'given coupon is not valid.')
                    else:
                        raise ValueError(f'unhandled status code {response.status_code}')
                else:
                    connection_error()
        data = {
            'name': self.window.payment.get_coupon(),
        }
        pay_thread = tr_request(method='post', url=get_url('coupon', coupon_id=self.window.payment.get_coupon()), headers=get_header(self.token_var), json=data)
        self.window.payment.set_coupon_button_state('disabled')
        self.monitor.run(pay_thread, handle)


    


    