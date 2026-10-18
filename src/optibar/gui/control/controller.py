import tkinter as tk
from optibar.gui.view.root import Root
from optibar.gui.control.menu.menu import MenuBar
from optibar.gui.control.body.upload import Upload
from optibar.gui.control.body.calculation import Calc
from optibar.gui.control.body.results import Result


class Controller():
    def __init__(self, root: Root):
        self.root = root

        # initialize
        result_data = {
            'is_available': tk.BooleanVar(root, False),
            'data': None,
        }
        project_data = {
            'is_available': tk.BooleanVar(root, False),
            'data': None,
        }

        notebook = root.notebook
        MenuBar(root)
        Upload(notebook.upload, project_data)
        Calc(notebook.calc, project_data, result_data)
        Result(root, notebook.results, result_data)
