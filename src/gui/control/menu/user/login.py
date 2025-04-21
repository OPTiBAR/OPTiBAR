from src.view.menu.user.login import LoginWindow
import requests
from tkinter.messagebox import showinfo
from src.control.utils.urls import get_url, connection_error
from src.control.utils.threading import tr_request, Monitor

class Login():
    def __init__(self, root, token_var) -> None:
        self.root = root
        self.token_var = token_var
    
    def open(self,*args):
        self.window = LoginWindow(self.root)

    def send(self, *args):
        def handle(response: requests.Response):
            if self.window.is_live():
                self.window.set_button_state('!disabled')
                if response is not None:
                    if  response.status_code == 200:
                        self.token_var.set(response.json()['token'])
                        self.window.close()
                        showinfo('Login', 'loged in successfuly.')
                    else:
                        if response.status_code == 400:
                            errors = []
                            if 'email' in response.json():
                                errors.append('Email: ' + response.json()['email'][0])
                            if 'password' in response.json():
                                errors.append('Password: ' + response.json()['password'][0])
                            self.window.set_status('\n'.join(errors))
                        elif response.status_code == 401:
                            self.window.set_status(response.json()['detail'])
                        else:
                            raise ValueError(f'unhandled status code {response.status_code}')
                else:
                    connection_error()
        
        self.window.set_button_state('disabled')
        thread = tr_request(method = 'post', url=get_url('login'), json=self.window.get_values())
        Monitor(self.root).run(thread, handle)