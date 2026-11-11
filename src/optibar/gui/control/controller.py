import tkinter as tk
from optibar.gui.view.root import Root
from optibar.gui.control.menu.menu import MenuBar
from optibar.gui.control.body.log import ReportLog
from optibar.gui.control.body.upload import Upload
from optibar.gui.control.body.calculation import Calc
from optibar.gui.control.body.results import Result


class Controller():
    def __init__(self, root: Root):
        self.root = root

        # initialize
        result_data = {
            'is_available': tk.BooleanVar(root, False),
            'stale': tk.BooleanVar(root, False), # the settings changed after the calculation
            'data': None,
        }
        project_data = {
            'is_available': tk.BooleanVar(root, False),
            'data': None,
        }

        # the report of the results pane shows the input file and the results
        report = ReportLog(root.results.log)
        MenuBar(root)
        Upload(root.file_bar, report, project_data)
        Calc(root.settings, project_data, result_data)
        Result(root, root.results, result_data, report)
