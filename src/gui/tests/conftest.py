import pathlib
import time
import tkinter as tk
import pytest

import gui.control.body.upload as upload_module
import gui.control.body.calculation as calculation_module
import gui.control.body.results as results_module
from gui.view.root import Root
from gui.control.controller import Controller
from core.parser.parse import has_access_driver

DATA_PATH = pathlib.Path(__file__).parents[2].joinpath('core', 'tests', 'parser', 'data_files')
SAMPLE_FILE = DATA_PATH.joinpath('tonf_m.accdb')

requires_driver = pytest.mark.skipif(not has_access_driver(), reason='Microsoft Access ODBC driver is not installed')


class App():
    """the real window and controllers, with dialogs recorded instead of shown"""
    def __init__(self, monkeypatch, tmp_path: pathlib.Path) -> None:
        self.dialogs = []
        self.save_paths = []
        self.answer_yes = False
        record = lambda kind: (lambda title, message, **kwargs: self.dialogs.append((kind, title, message)))
        for module in (upload_module, calculation_module, results_module):
            for kind in ('showinfo', 'showerror'):
                if hasattr(module, kind):
                    monkeypatch.setattr(module, kind, record(kind))
        monkeypatch.setattr(upload_module, 'askyesno', lambda title, message: self.dialogs.append(('askyesno', title, message)) or self.answer_yes)
        monkeypatch.setattr(results_module, 'asksaveasfilename', lambda **kwargs: str(self.save_paths.pop(0)) if self.save_paths else '')
        monkeypatch.setattr(upload_module.webbrowser, 'open', lambda url: self.dialogs.append(('browser', url, '')))
        self.tmp_path = tmp_path
        self.root = self._create_root()
        Controller(self.root)
        self.root.update()
        self.notebook = self.root.notebook

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
        return self.notebook.calc.request

    def errors(self):
        return [d for d in self.dialogs if d[0] == 'showerror']

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

    def log_text(self, log) -> str:
        return log.text.get('1.0', 'end').strip()

    def load(self, path: pathlib.Path = SAMPLE_FILE) -> None:
        self.notebook.upload.browser.path_var.set(str(path))
        self.notebook.upload.browser.event_generate('<<load-button-pressed>>')
        self.update()

    def set_calc_type(self, calc_type: str) -> None:
        self.notebook.calc.calc_type.type_var.set(calc_type)
        self.notebook.calc.calc_type.event_generate('<<calc-type-changed>>')

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
