import webbrowser
from tkinter.messagebox import showerror, showinfo, askyesno
from typing import Dict
from optibar.gui.view.body.upload import UploadNote
from optibar.core.parser.parse import V16Parser, has_access_driver
from optibar.core.parser.errors import TableMissingError, DriverMissingError


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

        # access files can't be read without the ODBC driver, say so before the user tries
        if not has_access_driver():
            error = DriverMissingError()
            self.log.write_error(error.message)
            self.log.write_info('Download: ' + error.url)


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
        file_path = self.path_var.get()
        parser = None
        try:
            parser = V16Parser(file_path)
            input_data = parser.get_foundation()
            concrete_set = parser.get_concrete_set()
            steel_set = parser.get_steel_set()
        except DriverMissingError as e:
            self.browser.set_status('Failed')
            self.log.write_error(e.message)
            self.log.write_info('Download: ' + e.url)
            if askyesno('Access Driver Missing', e.message + '\n\nOpen the download page?'):
                webbrowser.open(e.url)
            return
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
            'file_path': file_path,
            'input_data': input_data,
            'strip_names': [strip['name'] for strip in input_data['strips']],
            'materials': {'fc': next(iter(concrete_set)), 'fy': next(iter(steel_set))},
        }
        self.project_data['is_available'].set(True)
        showinfo('Input File', 'Project loaded successfully. Go to the 2. Calculation tab to perform the calculation.')
