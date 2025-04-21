from src.view.utils.router import Router
from src.view.menu.help import About, Contacts
from tkinter.messagebox import showinfo, askyesno
from src.control.utils.urls import get_url
from src.control.utils.threading import tr_request, Monitor
from pathlib import Path
from packaging import version
from src.setting import VERSION
import requests
import webbrowser
import os


class HelpMenu():
    def __init__(self, root: Router) -> None:
        self.root = root
        root.bind('<<open-doc>>', self.open_doc_fun)
        root.bind('<<about>>', self.about_fun)
        root.bind('<<contacts>>', self.contacts_fun)
        root.bind('<<menu-check-update>>', self.menu_check_update)
        root.bind('<<startup-check-update>>', self.startup_check_update)
        self.monitor = Monitor(root)
    
    def open_doc_fun(self, e):
        # os.startfile(os.path.abspath("./data/doc/optibar.pdf"))
        path = (Path(__file__).parent.parent.parent.parent).joinpath('data', 'doc', 'optibar.pdf').absolute()
        os.startfile(path)
    
    def about_fun(self, e):
        About(self.root)

    def contacts_fun(self, e):
        Contacts(self.root)
    
    def _check_update(self, updated_response):
        def handle_check(response: requests.Response):
            if response is not None:
                last_version = response.json()['version']
                if version.parse(VERSION) < version.parse(last_version):
                    update_software = askyesno('Update', 'There is a newer version of the software. do you want to download it?')
                    if update_software:
                        webbrowser.open(get_url('client_download'))
                else:
                    if updated_response:
                        showinfo('Software Version', 'Your already have the last version of the software.')
        
        thread = tr_request(method='get', url=get_url('client_version'))
        self.monitor.run(thread, handle_check)

    def menu_check_update(self, e):
        self._check_update(True)
    
    def startup_check_update(self, e):
        self._check_update(False)