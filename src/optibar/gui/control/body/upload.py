from pathlib import Path
from typing import Dict
from optibar.gui.view.body.upload import FileBar
from optibar.gui.control.body.log import ReportLog
from optibar.core.parser.parse import V16Parser, has_access_driver
from optibar.core.parser.errors import TableMissingError, DriverMissingError


class Upload():
    """loads the input file; its messages go to the input section of the report and the status badge"""
    def __init__(self, file_bar: FileBar, report: ReportLog, project_data: Dict) -> None:
        self.project_data = project_data
        self.browser = file_bar
        self.report = report
        self.path_var = self.browser.path_var

        # add trace and bind and initialize
        self.path_var.trace_add('write', self.path_var_changed)
        self.path_var.set('')
        self.browser.bind('<<load-button-pressed>>', self.load_file)
        self.browser.bind('<<status-clicked>>', lambda e: self.report.show_input())
        root = file_bar.winfo_toplevel()
        root.bind('<<open-file>>', lambda e: self.browser.browse_fun())
        root.bind('<<reload-file>>', lambda e: self.load_file() if self.path_var.get() else None)

        # access files can't be read without the ODBC driver, say so before the user tries
        if not has_access_driver():
            self._failed(DriverMissingError())

    def path_var_changed(self, *args):
        if self.path_var.get() == '':
            self.browser.set_load_button_state('disabled')
            self.browser.set_status('No file loaded')
        else:
            self.browser.set_load_button_state('!disabled')

    def _failed(self, error: Exception) -> None:
        """reports an input file that can't be used; the calculation is disabled until another file is loaded"""
        if isinstance(error, DriverMissingError):
            lines = [('ERROR', error.message), ('INFO', 'Download it from:'), ('LINK', error.url)]
            status = '✗ Access ODBC driver missing'
        elif isinstance(error, TableMissingError):
            lines = [('ERROR', error.message), ('INFO', 'Export the model from SAFE again, with this table.')]
            status = '✗ Not loaded: a table is missing'
        else:
            lines = [('ERROR', 'There is some unknown error in parsing the access file.')]
            status = '✗ Not loaded: the file could not be read'
        self.browser.set_status(status, 'error')
        self.report.set_input(lines)
        self.project_data['data'] = None
        self.project_data['is_available'].set(False)

    def load_file(self, *args):
        self.browser.set_status('Loading…', 'busy')
        self.browser.update_idletasks()
        file_path = self.path_var.get()
        parser = None
        try:
            parser = V16Parser(file_path)
            input_data = parser.get_foundation()
            concrete_set = parser.get_concrete_set()
            steel_set = parser.get_steel_set()
        except Exception as e:
            self._failed(e)
            return
        finally:
            if parser is not None:
                parser.close()

        lines = [
            ('SUCCESS', 'File Parsed Successfully.'),
            ('INFO', f"{Path(file_path).name}: {len(input_data['strips'])} strips"),
        ]
        warnings = []
        if len(concrete_set) > 1:
            warnings.append("You are using more than one concrete material. The output may not be reliable.")
        if len(steel_set) > 1:
            warnings.append("You are using more than one steel material. The output may not be reliable.")
        lines += [('WARNING', warning) for warning in warnings]
        if warnings:
            self.browser.set_status(f"⚠ Loaded with {len(warnings)} warning{'s' if len(warnings) > 1 else ''}", 'warning')
        else:
            self.browser.set_status('✓ Loaded', 'success')
        self.report.set_input(lines)

        # update project_data
        self.project_data['data'] = {
            'file_path': file_path,
            'input_data': input_data,
            'strip_names': [strip['name'] for strip in input_data['strips']],
            'materials': {'fc': next(iter(concrete_set)), 'fy': next(iter(steel_set))},
        }
        # set even when it was True already: a reloaded file clears the results
        self.project_data['is_available'].set(True)
