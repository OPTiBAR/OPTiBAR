from typing import Dict, Union
from src.control.menu.menu import MenuBar
from src.control.body.calculation import Calc
from src.control.body.results import Result
from src.control.body.upload import Upload
from src.view.utils.router import Router
from subprocess import check_output
from src.setting import STORAGE_PATH

DATA_STORAGE_PATH = STORAGE_PATH.joinpath('cache.pkl')

import pathlib
import pickle
import tkinter as tk

class Controller():
    def __init__(self, root: Router):
        self.root = root
        if not STORAGE_PATH.is_dir():
            STORAGE_PATH.mkdir()
        
        # initialize
        system_data = {
            'acad_path': tk.StringVar(root, '')
        }
        user_data = {
            'token': tk.StringVar(root, '')
        }
        result_data = {
            'is_available': tk.BooleanVar(root, False),
            'data': None,
        }
        project_data = {
            'is_available': tk.BooleanVar(root, False),
            'data': None,
        }
        
        MenuBar(root, user_data['token'], system_data['acad_path'])
        Upload(root, user_data['token'], project_data)
        Calc(root, user_data['token'], project_data, result_data)
        Result(root, user_data['token'], result_data, system_data['acad_path'])

        # check for update at startup
        root.event_generate("<<startup-check-update>>")

        # should come at the end to trigger the initialization process in subcontrollers
        storage = OfflineStorage(user_data, system_data)
        user_data['token'].trace_add('write', storage.save)
        


class OfflineStorage():
    def __init__(self, user_data, system_data) -> None:
        self.user_data = user_data
        self.system_data = system_data
        if not DATA_STORAGE_PATH.is_file():
            self.create_file()
        data = self.load()
        self.user_data['token'].set(data['token'])
        if pathlib.Path(data['acad_path']).is_file():
            self.system_data['acad_path'].set(data['acad_path'])
        else:
            self.system_data['acad_path'].set(self.find_acad_path())
        
    
    def find_acad_path(self) -> Union[pathlib.Path, None]:
        """find the path of acad.exe in the clients system
        Returns:
            Union[pathlib.Path, None]: 
        """
        try:
            path = check_output('where /r  "C:\\program files\\Autodesk" acad.exe').decode().split('\r\n')[0]
            return pathlib.Path(path).absolute()
        except Exception as e:
            return ''
            
    
    def create_file(self) -> None:
        data = {
            'token': '',
            'acad_path': ''
        }
        f = open(DATA_STORAGE_PATH, 'wb')
        pickle.dump(data,f)

    def load(self) -> Dict:
        try:
            f = open(DATA_STORAGE_PATH, 'rb')
            data = pickle.load(f)
            return data
        finally:
            f.close()
    
    def save(self, *args):
        data = {
            'token': self.user_data['token'].get(),
            'acad_path': self.system_data['acad_path'].get(),
        }
        try:
            f = open(DATA_STORAGE_PATH, 'wb')
            pickle.dump(data,f)
        finally:
            f.close()

