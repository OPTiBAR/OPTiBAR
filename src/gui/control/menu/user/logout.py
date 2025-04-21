import requests
from tkinter.messagebox import showinfo, askyesno, showerror
from src.control.utils.urls import get_url, get_header, connection_error
from src.control.utils.threading import tr_request, Monitor

class Logout():
    def __init__(self, root, token_var) -> None:
        self.root = root
        self.token_var = token_var

    def send(self, *args):
        def handle(response: requests.Response):
            # showinfo('Logout', 'loged out successfuly.')
            self.token_var.set('')
            if response is not None:
                if  response.status_code == 200:
                    showinfo('Logout', 'loged out successfuly.')
                    # self.token_var.set('')
                    # pass
                else:
                    if response.status_code == 403:
                        showerror('Logout error', response.json()['detail'])
            else:
                connection_error()
            
        if askyesno('Logout', 'Are you sure you want to logout?'):
            thread = tr_request(method='get', url=get_url('logout'), headers=get_header(self.token_var))
            Monitor(self.root).run(thread, handle)