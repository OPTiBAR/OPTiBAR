import tkinter as tk
from urllib.parse import urljoin
from uuid import UUID
from src.setting import DOMAIN
from tkinter.messagebox import showerror

URL_DICT = {
    'client_version': 'application/version/',
    'client_download': 'application/download/',
    'price': 'payment/price/',
    'pay': 'payment/pay/',
    'coupon': 'payment/coupon/{coupon_id}/',
    'profile': 'accounts/users/me/',
    'signup': 'accounts/signup/',
    'login': 'accounts/login/',
    'logout': 'accounts/logout/',
    'password_reset': 'accounts/password/reset/',
    'password_reset_verified': 'accounts/password/reset/verified/',
    'passwor_change': 'accounts/password/change/',
    'projects': 'foundation/projects/',
    'calculation_orders': 'foundation/projects/{project_id}/orders/calculation/',
    'calculation_orders_id': 'foundation/projects/{project_id}/orders/calculation/{order_id}/',
    'analysis_orders': 'foundation/projects/{project_id}/orders/analysis/',
    'analysis_orders_id': 'foundation/projects/{project_id}/orders/analysis/{order_id}/',
    'report_bug': 'foundation/orders/{order_id}/reports/',
}

# DOMAIN = DOMAIN + 'api/'

def get_url(id: str, **kwargs) -> str:
    return urljoin(DOMAIN, URL_DICT[id].format(**kwargs))

def get_header(token_var: tk.StringVar):
    if token_var.get() == '':
        headers = dict()
    else:
        headers = {'Authorization': 'Token ' + token_var.get()}
    return headers

def connection_error():
    showerror(title='Internet connection', message='It seems that there is some problem in your internet connection. please check your connection and try again. connecting or disconnecting the proxy may be helpful.')