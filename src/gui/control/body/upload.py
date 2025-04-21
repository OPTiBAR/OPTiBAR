import tkinter as tk
from tkinter.messagebox import showerror, showinfo
from typing import Dict
from src.view.utils.router import Router
from ..utils.threading import tr_request, Monitor
import requests
from ..utils.urls import connection_error, get_header, get_url
from src.control.parser.parse import V16Parser
from src.control.parser.errors import TableMissingError


class Upload():
    def __init__(self, root: Router, token_var: tk.StringVar, project_data: Dict) -> None:
        self.token_var = token_var
        self.project_data = project_data
        self.root = root
        self.upload_note = root.get_child('notebook').get_child('upload')
        self.browser = self.upload_note.get_child('browser')
        self.log = self.upload_note.get_child('log')
        self.path_var = self.browser.path_var
        self.monitor = Monitor(root)
        
        # add trace and bind and initialize
        self.path_var.trace_add('write', self.path_var_changed)
        self.path_var.set('')
        self.browser.bind('<<upload-button-pressed>>', self.upload_file)
    

    def path_var_changed(self, *args):
        if self.path_var.get() == '':
            self.browser.set_upload_button_state('disabled')
            self.browser.set_status('')
        else:
            self.browser.set_upload_button_state('!disabled')
            self.browser.set_status('Idle')
    
    def upload_file(self, *args):
        def set_buttons_state(state):
            self.browser.set_upload_button_state(state)
            self.browser.set_browse_button_state(state)

        def handle_upload(response: requests.Response):
            set_buttons_state('!disabled')
            if response is not None:
                if  response.status_code in (200, 201):
                    self.browser.set_status('Done')
                    # update project_data
                    project_data = self.project_data
                    project_data['data'] = {
                        'project_id' : response.json()['id'],
                        'strip_names' : list(map(lambda strip: strip['name'], input_data['strips'])),
                        'materials': {'fc':list(parser.get_concrete_set())[0], 'fy':list(parser.get_steel_set())[0]},
                    }
                    project_data['is_available'].set(True)

                    # log
                    self.log.write_success('File Uploaded Successfully.')
                    showinfo('Upload', 'Project Uploaded successfuly. go to the 2. Calculation tab to perform the calculation.')
                elif response.status_code == 401:
                    self.browser.set_status('Upload Failed')
                    showerror('Login Required', 'Please Login before uploading the project.')
                elif response.status_code == 403:
                    showerror('Service Level', response.json()['detail'])
                else:
                    raise ValueError(f'unhandled status code {response.status_code}')
            else:
                self.browser.set_status('Upload Failed')
                connection_error()
        
        self.log.clear()
        set_buttons_state('disabled')
        self.browser.set_status('Parsing Database File')
        input_data = None
        try:
            parser = V16Parser(self.path_var.get())
            input_data = parser.get_foundation()
            self.log.write_success('File Parsed Successfully.')
            if len(parser.get_concrete_set()) > 1:
                self.log.write_warning("You are using more than one concrete material. The output may not be reliable.")
            if len(parser.get_steel_set()) > 1:
                self.log.write_warning("You are using more than one steel material. The output may not be reliable.")
        except TableMissingError as e:
            self.log.write_error(e.message)
            showerror('Missing Table', e.message)
        except Exception as e:
            self.log.write_error('There is some unknown error in parsing the access file. please contact the technical team.')
            showerror('Unknown Error', 'There is some unknown error in parsing the access file. please contact the technical team.')
        finally:
            parser.__del__()

        if input_data is None:
            set_buttons_state('!disabled')
        else:
            self.browser.set_status('Uploading')
            thread = tr_request(method='post', url=get_url('projects'), json={'input_data':input_data}, headers=get_header(self.token_var))
            self.monitor.run(thread, handle_upload)

        
        
        


    





