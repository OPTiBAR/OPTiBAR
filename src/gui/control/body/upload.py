import tkinter as tk
from tkinter.messagebox import showerror, showinfo
from typing import Dict
from gui.view.body.upload import UploadNote
from core.parser.parse import V16Parser
from core.parser.errors import TableMissingError


class Upload():
    def __init__(self, upload_note: UploadNote, project_data: Dict) -> None:
        self.project_data = project_data
        self.browser = upload_note.browser
        self.log = upload_note.log
        self.path_var = self.browser.path_var

        # add trace and bind and initialize
        self.path_var.trace_add('write', self.path_var_changed)
        self.path_var.set('')
        self.browser.bind('<<load-button-pressed>>', self.load_file)


    def path_var_changed(self, *args):
        if self.path_var.get() == '':
            self.browser.set_load_button_state('disabled')
            self.browser.set_status('')
        else:
            self.browser.set_load_button_state('!disabled')
            self.browser.set_status('Idle')

    def load_file(self, *args):
        self.log.clear()
        self.browser.set_status('Parsing Database File')
        self.browser.update_idletasks()
        parser = None
        try:
            parser = V16Parser(self.path_var.get())
            input_data = parser.get_foundation()
            concrete_set = parser.get_concrete_set()
            steel_set = parser.get_steel_set()
        except TableMissingError as e:
            self.browser.set_status('Failed')
            self.log.write_error(e.message)
            showerror('Missing Table', e.message)
            return
        except Exception:
            self.browser.set_status('Failed')
            message = 'There is some unknown error in parsing the access file.'
            self.log.write_error(message)
            showerror('Unknown Error', message)
            return
        finally:
            if parser is not None:
                parser.close()

        self.log.write_success('File Parsed Successfully.')
        if len(concrete_set) > 1:
            self.log.write_warning("You are using more than one concrete material. The output may not be reliable.")
        if len(steel_set) > 1:
            self.log.write_warning("You are using more than one steel material. The output may not be reliable.")
        self.browser.set_status('Done')

        # update project_data
        self.project_data['data'] = {
            'input_data': input_data,
            'strip_names': [strip['name'] for strip in input_data['strips']],
            'materials': {'fc': next(iter(concrete_set)), 'fy': next(iter(steel_set))},
        }
        self.project_data['is_available'].set(True)
        showinfo('Input File', 'Project loaded successfully. Go to the 2. Calculation tab to perform the calculation.')
