from src.view.utils.router import Router
import tkinter as tk

from .login import Login
from .logout import Logout
from .signup import Signup
from .dashboard import Dashboard
from .pass_reset import PassReset


class UserMenu():
    def __init__(self, root: Router, token_var: tk.StringVar) -> None:
        self.root = root
        self.token_var = token_var
        
        login = Login(root, token_var)
        root.bind('<<login-pressed>>', login.open)
        root.bind('<<send-login>>', login.send)
        
        logout = Logout(root, token_var)
        root.bind('<<logout-pressed>>', logout.send)

        signup = Signup(root)
        root.bind('<<signup-pressed>>', signup.open)
        root.bind('<<send-signup>>', signup.send)

        dashboard = Dashboard(root, token_var)
        root.bind('<<dashboard-pressed>>', dashboard.open)
        root.bind('<<pay-pressed>>', dashboard.send_pay)
        root.bind('<<coupon-pressed>>', dashboard.send_coupon)

        pass_reset = PassReset(root)
        root.bind('<<password-reset-pressed>>', pass_reset.open_password_reset)
        root.bind('<<send-password-reset>>', pass_reset.send_password_reset)
        root.bind('<<send-verify>>', pass_reset.send_verify)

        self.user_menu = self.root.get_child('menu').get_child('user')
        self.token_var.trace_add('write', self.change_layout)


    def change_layout(self, *args):
        if not self.token_var.get():
            self.user_menu.set_anonymous_layout()
        else:
            self.user_menu.set_loged_in_layout()