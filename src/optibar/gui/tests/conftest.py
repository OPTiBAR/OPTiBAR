import pathlib
import time
import tkinter as tk
import pytest

import optibar.gui.control.body.upload as upload_module
import optibar.gui.control.body.calculation as calculation_module
import optibar.gui.control.body.results as results_module
import optibar.gui.view.body.upload as file_bar_module
import optibar.gui.view.utils.common as common_module
from optibar.gui.view.root import Root
from optibar.gui.control.controller import Controller
from optibar.core.parser.parse import has_access_driver

DATA_PATH = pathlib.Path(__file__).parents[2].joinpath('core', 'tests', 'parser', 'data_files')
SAMPLE_FILE = DATA_PATH.joinpath('tonf_m.accdb')

requires_driver = pytest.mark.skipif(not has_access_driver(), reason='Microsoft Access ODBC driver is not installed')


class App():
    """the real window and controllers, with dialogs recorded instead of shown"""
    def __init__(self, monkeypatch, tmp_path: pathlib.Path) -> None:
        self.dialogs = []
        self.save_paths = []
        self.open_paths = []
        record = lambda kind: (lambda title, message, **kwargs: self.dialogs.append((kind, title, message)))
        for module in (upload_module, calculation_module, results_module):
            for kind in ('showinfo', 'showerror'):
                if hasattr(module, kind):
                    monkeypatch.setattr(module, kind, record(kind))
        monkeypatch.setattr(results_module, 'asksaveasfilename', lambda **kwargs: str(self.save_paths.pop(0)) if self.save_paths else '')
        monkeypatch.setattr(file_bar_module, 'askopenfilename', lambda **kwargs: str(self.open_paths.pop(0)) if self.open_paths else '')
        monkeypatch.setattr(common_module.webbrowser, 'open', lambda url: self.dialogs.append(('browser', url, '')))
        self.tmp_path = tmp_path
        self.root = self._create_root()
        # exceptions in tk callbacks are printed and swallowed by tkinter; record them as errors
        self.root.report_callback_exception = lambda kind, value, tb: self.dialogs.append(('exception', kind.__name__, str(value)))
        Controller(self.root)
        self.root.update()
        self.file_bar = self.root.file_bar
        self.settings = self.root.settings
        self.results = self.root.results

    @staticmethod
    def _create_root() -> Root:
        # on Windows, Tcl sometimes can't read its own library files (init.tcl, tk.tcl) for a
        # moment, likely while a virus scanner holds them; creating a window per test hits this
        for attempt in range(5):
            try:
                return Root()
            except tk.TclError as e:
                error = e
                time.sleep(0.5 * (attempt + 1))
        pytest.skip(f'Tk could not start: {error}')

    @property
    def request(self):
        return self.settings.request

    def errors(self):
        return [d for d in self.dialogs if d[0] in ('showerror', 'exception')]

    def update(self, seconds: float = 0) -> None:
        end = time.time() + seconds
        while True:
            self.root.update()
            if time.time() >= end:
                return
            time.sleep(0.05)

    def wait_until(self, condition, timeout: float = 120) -> None:
        end = time.time() + timeout
        while not condition():
            if time.time() > end:
                raise TimeoutError(self.request.status_var.get())
            self.update(0.05)

    def log_text(self, log=None) -> str:
        """the text of the report, or of the given log"""
        return (log or self.results.log).text.get('1.0', 'end').strip()

    def load(self, path: pathlib.Path = SAMPLE_FILE) -> None:
        self.file_bar.path_var.set(str(path))
        self.file_bar.event_generate('<<load-button-pressed>>')
        self.update()

    def set_calc_type(self, calc_type: str) -> None:
        self.settings.calc_type.type_var.set(calc_type)
        self.settings.calc_type.event_generate('<<calc-type-changed>>')

    def calculate(self) -> None:
        self.request.event_generate('<<calc-pressed>>')
        self.update()
        self.wait_until(lambda: self.request.get_button_label() == 'Calculate')

    def press(self, widget, event: str, save_path: pathlib.Path = None) -> None:
        if save_path is not None:
            self.save_paths.append(save_path)
        widget.event_generate(event)
        self.update()

    def destroy(self) -> None:
        if self.request.get_button_label() == 'Stop':
            self.request.event_generate('<<calc-pressed>>') # stops the running engine process
        self.root.destroy()


@pytest.fixture
def make_app(monkeypatch, tmp_path):
    apps = []
    def factory() -> App:
        app = App(monkeypatch, tmp_path)
        apps.append(app)
        return app
    yield factory
    for app in apps:
        app.destroy()


@pytest.fixture
def app(make_app) -> App:
    return make_app()


@pytest.fixture
def loaded_app(app) -> App:
    if not has_access_driver():
        pytest.skip('Microsoft Access ODBC driver is not installed')
    app.load()
    return app
