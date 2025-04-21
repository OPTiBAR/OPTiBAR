from src.view.menu.user.signup import SignupWindow
import requests
from tkinter.messagebox import showinfo
from src.control.utils.urls import get_url, connection_error
from src.control.utils.threading import tr_request, Monitor
from src.control.utils.validators import password_validator, phone_validator

class Signup():
    def __init__(self, root) -> None:
        self.root = root
    
    def open(self, *args):
        self.window = SignupWindow(self.root)

    def send(self, *args):
        def handle(response: requests.Response):
            if self.window.is_live():
                self.window.set_button_state('!disabled')
                if response is not None:
                    self.window.set_button_state('!disabled')
                    if  response.status_code == 201:
                        self.window.close()
                        showinfo('Sign up', 'signed up successfuly. please check your email inbox(spam) and confirm your email address using the sent link.')
                    else:
                        if response.status_code == 400:
                            errors = []
                            if 'email' in response.json():
                                errors.append('email: ' + response.json()['email'][0])
                            if 'password' in response.json():
                                errors.append('password: ' + response.json()['password'][0])
                            if 'detail' in response.json():
                                errors.append(response.json()['detail'])
                            self.window.set_status('\n'.join(errors))
                        else:
                            raise ValueError(f'unhandled status code {response.status_code}')
                else:
                    # added because of too much delay in response from the server
                    # -------
                    self.window.close()
                    showinfo('Sign up', 'signed up successfuly. please check your email inbox(spam) and confirm your email address using the sent link.')
                    return
                    # -------
                    connection_error()

        data = self.window.get_values()
        if data['password1'] != data['password2']:
            self.window.set_status('please repeat the password.')
            return
        pass_validation = password_validator(data['password1'])
        phone_validation = phone_validator(data['phone_num'])
        if not phone_validation['is_valid']:
            self.window.set_status(phone_validation['message'])
            return
        elif not pass_validation['is_valid']:
            self.window.set_status(pass_validation['message'])
            return
        else:
            self.window.set_status('')
        
        data['password'] = data['password1']
        del data['password1']
        del data['password2']

        self.window.set_button_state('disabled')
        thread = tr_request(method='post', url=get_url('signup'), json=data, headers=None)
        Monitor(self.root).run(thread, handle)