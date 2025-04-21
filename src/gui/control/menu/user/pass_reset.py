from src.view.menu.user.pass_reset import PassResetWindow, VerifyWindow
import requests
from tkinter.messagebox import showinfo
from src.control.utils.urls import get_url, connection_error
from src.control.utils.threading import tr_request, Monitor
from src.control.utils.validators import password_validator

class PassReset():
    def __init__(self, root) -> None:
        self.root = root
    
    def open_password_reset(self,e):
        self.password_reset_window = PassResetWindow(self.root)
        
    def send_password_reset(self, *args):
        def handle(response: requests.Response):
            if self.password_reset_window.is_live():
                self.password_reset_window.set_button_state('!disabled')
                if response is not None:
                    if  response.status_code == 201:
                        self.password_reset_window.close()
                        showinfo('Password Reset', 'a code sent to your email address. use it to reset your password.')
                        self.open_verify()
                    else:
                        if response.status_code == 400:
                            if 'email' in response.json():
                                self.password_reset_window.set_status('Email: ' + response.json()['email'][0])
                            else:
                                self.password_reset_window.set_status(response.json()['detail'])
                        else:
                            raise ValueError(f'unhandled status code {response.status_code}')
                else:
                    # added because of too much delay in response from the server
                    # -------
                    showinfo('Password Reset', 'a code sent to your email address. use it to reset your password.')
                    self.open_verify()
                    return
                    # -------
                    connection_error()
        
        self.password_reset_window.set_button_state('disabled')
        thread = tr_request(method = 'post', url=get_url('password_reset'), json=self.password_reset_window.get_values())
        Monitor(self.root).run(thread, handle)

    def open_verify(self):
        self.verify_window = VerifyWindow(self.root)
    
    def send_verify(self, *args):
        def handle(response: requests.Response):
            if self.verify_window.is_live():
                self.verify_window.set_button_state('!disabled')
                if response is not None:
                    if  response.status_code == 200:
                        self.verify_window.close()
                        showinfo('Verify', 'Your password changed. please login with the new password.')
                        self.open_login()
                    else:
                        if response.status_code == 400:
                            if 'password' in response.json():
                                self.verify_window.set_status('Password: ' + response.json()['password'][0])
                            else:
                                self.verify_window.set_status(response.json()['detail'])
                        else:
                            raise ValueError(f'unhandled status code {response.status_code}')
                else:
                    connection_error()

        data = self.verify_window.get_values()
        if data['password1'] != data['password2']:
            self.verify_window.set_status('please repeat the password.')
            return
        validation = password_validator(data['password1'])
        if not validation['is_valid']:
            self.verify_window.set_status(validation['message'])
            return
        else:
            self.verify_window.set_status('')
        data['password'] = data['password1']
        del data['password1']
        del data['password2']
        self.verify_window.set_button_state('disabled')
        thread = tr_request(method = 'post', url=get_url('password_reset_verified'), json=data)
        Monitor(self.root).run(thread, handle)