import json
import pathlib
import ezdxf
import pytest
from pypdf import PdfReader
import optibar.gui.control.body.upload as upload_module
from optibar.core.parser.parse import has_access_driver

# not imported from conftest: core/tests/parser has a conftest too, and only one is importable by that name
DATA_PATH = pathlib.Path(__file__).parents[2].joinpath('core', 'tests', 'parser', 'data_files')
SAMPLE_FILE = DATA_PATH.joinpath('tonf_m.accdb')
requires_driver = pytest.mark.skipif(not has_access_driver(), reason='Microsoft Access ODBC driver is not installed')


def test_startup(app):
    assert 'disabled' in app.request.calculate_button.state()
    assert app.request.status_var.get() == 'Status: Waiting for input file ...'
    assert 'disabled' in app.file_bar.load_button.state()
    for name in ('save', 'pdf', 'dxf', 'diagram'):
        assert 'disabled' in getattr(app.results.files, name + '_button').state()
    assert not app.results.stale_label.winfo_ismapped()
    if has_access_driver():
        assert app.file_bar.status_var.get() == 'No file loaded'
        assert 'open the Access file exported from SAFE' in app.log_text()


def test_startup_warns_when_driver_missing(monkeypatch, make_app):
    monkeypatch.setattr(upload_module, 'has_access_driver', lambda: False)
    app = make_app()
    log = app.log_text()
    assert 'Access ODBC driver is not installed' in log
    assert 'https://www.microsoft.com/' in log
    assert app.file_bar.status_var.get() == '✗ Access ODBC driver missing'


def test_load_with_driver_missing_links_the_download(monkeypatch, app):
    monkeypatch.setattr('optibar.core.parser.parse.has_access_driver', lambda: False)
    app.load()
    assert app.file_bar.status_var.get() == '✗ Access ODBC driver missing'
    assert 'disabled' in app.request.calculate_button.state()
    # no dialog: the report has the error and a link that opens the download page
    text = app.results.log.text
    start, end = text.tag_ranges('LINK')[:2]
    url = text.get(start, end)
    assert url.startswith('https://www.microsoft.com/')
    x, y, _, _ = text.bbox(start)
    # tag bindings follow the mouse: move over the link, then click
    text.event_generate('<Motion>', x=x + 2, y=y + 2)
    text.event_generate('<Button-1>', x=x + 2, y=y + 2)
    app.update()
    assert app.dialogs == [('browser', url, '')]


@requires_driver
def test_load_file(loaded_app):
    app = loaded_app
    assert 'File Parsed Successfully.' in app.log_text()
    assert app.file_bar.status_var.get() == '✓ Loaded'
    assert app.request.status_var.get() == 'Status: Ready'
    assert 'disabled' not in app.request.calculate_button.state()
    assert 'disabled' not in app.file_bar.load_button.state()
    assert app.settings.setting.advanced.special_length.get_values()['ld']['bottom'][0] > 0
    assert app.dialogs == [] # no pop-ups while loading


@requires_driver
def test_load_mdb(app):
    app.load(DATA_PATH.joinpath('tonf_m.mdb'))
    assert app.request.status_var.get() == 'Status: Ready'


@requires_driver
def test_load_errors(loaded_app):
    app = loaded_app
    app.load(DATA_PATH.joinpath('missing_table', 'program_control.accdb'))
    assert app.file_bar.status_var.get() == '✗ Not loaded: a table is missing'
    assert 'table' in app.log_text().lower()
    # a failed load replaces the loaded project, the calculation needs a new file
    assert 'disabled' in app.request.calculate_button.state()
    assert app.request.status_var.get() == 'Status: Waiting for input file ...'
    app.load(DATA_PATH.joinpath('does_not_exist.accdb'))
    assert app.file_bar.status_var.get() == '✗ Not loaded: the file could not be read'
    assert 'unknown error in parsing' in app.log_text()
    assert app.dialogs == []


@requires_driver
def test_open_and_reload(app):
    app.open_paths.append(SAMPLE_FILE)
    app.root.event_generate('<<open-file>>') # File > Open and Ctrl+O
    app.update()
    assert app.file_bar.path_var.get() == str(SAMPLE_FILE)
    assert app.file_bar.status_var.get() == '✓ Loaded'
    run_calculation(app)
    app.root.event_generate('<<reload-file>>') # File > Reload and F5
    app.update()
    assert app.file_bar.status_var.get() == '✓ Loaded'
    assert 'Mass Summary' not in app.log_text() # a reloaded file clears the results
    # cancelling the file dialog keeps the loaded file
    app.root.event_generate('<<open-file>>')
    app.update()
    assert app.file_bar.path_var.get() == str(SAMPLE_FILE)


def run_calculation(app):
    app.set_calc_type('calculation')
    app.calculate()
    assert app.request.status_var.get() == 'Status: Finished'


def run_analysis(app):
    app.set_calc_type('analysis')
    analysis = app.settings.setting.basic.type_num_analysis
    analysis.total_frame.combo_from.set_value(10)
    analysis.total_frame.combo_to.set_value(11)
    analysis.stack_frame.combo_from.set_value(2)
    analysis.stack_frame.combo_to.set_value(3)
    app.calculate()
    assert app.request.status_var.get() == 'Status: Finished'


@requires_driver
def test_calculation(loaded_app):
    app = loaded_app
    app.request.event_generate('<<calc-pressed>>')
    app.update()
    assert app.request.get_button_label() == 'Stop'
    app.wait_until(lambda: app.request.get_button_label() == 'Calculate')
    log = app.log_text()
    assert 'File Parsed Successfully.' in log # the input file stays at the top of the report
    assert 'Mass Summary' in log
    assert 'Cutting Plans' in log
    files = app.results.files
    assert 'disabled' not in files.save_button.state()
    assert 'disabled' not in files.pdf_button.state()
    assert 'disabled' not in files.dxf_button.state()
    assert 'disabled' in files.diagram_button.state()
    assert app.dialogs == [] # no pop-ups after the calculation


@requires_driver
def test_stale_results(loaded_app):
    app = loaded_app
    run_calculation(app)
    app.update(1)
    assert not app.results.stale_label.winfo_ismapped()
    stack = app.settings.setting.basic.type_num_calc.stack_combo
    stack.set_value(stack.get_value() + 1)
    app.wait_until(lambda: app.results.stale_label.winfo_ismapped(), timeout=5)
    assert 'Mass Summary' in app.log_text() # the old results stay readable
    stack.set_value(stack.get_value() - 1) # back to the settings of the results
    app.wait_until(lambda: not app.results.stale_label.winfo_ismapped(), timeout=5)
    stack.set_value(stack.get_value() + 1)
    app.wait_until(lambda: app.results.stale_label.winfo_ismapped(), timeout=5)
    run_calculation(app)
    app.update()
    assert not app.results.stale_label.winfo_ismapped()


@requires_driver
def test_save_calculation_results(loaded_app):
    app = loaded_app
    run_calculation(app)
    path = app.tmp_path.joinpath('result.json')
    app.press(app.results.files, '<<save-button-pressed>>', path)
    saved = json.loads(path.read_text(encoding='utf-8'))
    assert saved['calc_type'] == 'calculation'
    assert saved['input_file'].endswith('tonf_m.accdb')
    assert saved['config']['diameter']['typical'] == 18
    assert 'summary' in saved['result']['data']
    summary = app.tmp_path.joinpath('result_summary.txt').read_text(encoding='utf-8')
    assert 'Settings' in summary and 'Mass Summary' in summary and 'tonf_m.accdb' in summary
    assert 'Cutting Plan, diameter' in summary
    assert saved['result']['data']['cut'] # the plans are saved with the result
    assert app.errors() == []


@requires_driver
def test_save_pdf(loaded_app):
    app = loaded_app
    run_calculation(app)
    path = app.tmp_path.joinpath('drawing.pdf')
    app.press(app.results.files, '<<pdf-button-pressed>>', path)
    strips = len(app.settings.setting.advanced.typical.table.tree.get_children()) // 2
    assert len(PdfReader(path).pages) > strips
    assert app.errors() == []


@requires_driver
def test_save_dxf(loaded_app):
    app = loaded_app
    run_calculation(app)
    path = app.tmp_path.joinpath('drawing.dxf')
    app.press(app.results.files, '<<dxf-button-pressed>>', path)
    doc = ezdxf.readfile(path)
    assert doc.audit().errors == []
    assert 'Top Additional Rebars Of X Direction' in [e.text for e in doc.modelspace().query('MTEXT')]
    assert app.errors() == []


@requires_driver
def test_save_cancelled(loaded_app):
    app = loaded_app
    run_calculation(app)
    app.press(app.results.files, '<<save-button-pressed>>') # dialog returns '' when cancelled
    assert list(app.tmp_path.iterdir()) == []
    assert app.errors() == []


@requires_driver
def test_analysis(loaded_app):
    app = loaded_app
    progress = []
    app.request.status_var.trace_add('write', lambda *args: progress.append(app.request.status_var.get()))
    run_analysis(app)
    assert any('of 4 combinations done' in status for status in progress)
    assert 'Mass Report' in app.log_text()
    files = app.results.files
    assert 'disabled' not in files.diagram_button.state()
    assert 'disabled' in files.pdf_button.state()
    assert 'disabled' in files.dxf_button.state()
    windows = len(app.root.winfo_children())
    app.press(files, '<<diagram-button-pressed>>')
    assert len(app.root.winfo_children()) == windows + 1
    path = app.tmp_path.joinpath('analysis.json')
    app.press(files, '<<save-button-pressed>>', path)
    assert len(json.loads(path.read_text(encoding='utf-8'))['result']) == 4
    assert 'Mass Report' in app.tmp_path.joinpath('analysis_summary.txt').read_text(encoding='utf-8')
    assert app.errors() == []


@requires_driver
def test_stop(loaded_app):
    app = loaded_app
    app.request.event_generate('<<calc-pressed>>')
    app.update()
    app.request.event_generate('<<calc-pressed>>')
    app.update()
    assert app.request.status_var.get() == 'Status: Stopped'
    assert app.request.get_button_label() == 'Calculate'
    app.update(2)
    assert 'Mass Summary' not in app.log_text()
    assert 'File Parsed Successfully.' in app.log_text()
    assert 'disabled' in app.results.files.save_button.state()


@requires_driver
def test_progress_bar(loaded_app):
    app = loaded_app
    progress = app.request.progress # shown = placed in the grid
    assert not progress.grid_info()
    app.request.event_generate('<<calc-pressed>>')
    app.update(0.2)
    assert progress.grid_info()
    app.wait_until(lambda: app.request.get_button_label() == 'Calculate')
    app.update()
    assert not progress.grid_info()

    values = []
    app.set_calc_type('analysis')
    analysis = app.settings.setting.basic.type_num_analysis
    analysis.total_frame.combo_from.set_value(10)
    analysis.total_frame.combo_to.set_value(11)
    analysis.stack_frame.combo_from.set_value(2)
    analysis.stack_frame.combo_to.set_value(2)
    app.request.status_var.trace_add('write', lambda *args: values.append((float(progress['value']), float(progress['maximum']))))
    app.calculate()
    assert (2.0, 2.0) in values # determinate once the analysis reports progress
    assert not progress.grid_info()


@requires_driver
def test_dark_theme(loaded_app):
    from optibar.gui.view.utils.styles import PALETTES
    app = loaded_app
    log = app.results.log.text
    assert log.cget('background') == PALETTES['light']['text_bg']
    app.root.menu.view.dark_var.set(True)
    app.root.event_generate('<<toggle-theme>>')
    app.update()
    assert log.cget('background') == PALETTES['dark']['text_bg']
    assert log.tag_cget('INFO', 'foreground') == PALETTES['dark']['text_fg']
    tree = app.settings.setting.advanced.typical.table.tree
    assert str(tree.tag_configure('oddrow', 'background')) == PALETTES['dark']['stripe']
    # results still work and the diagram follows the theme
    run_analysis(app)
    windows = len(app.root.winfo_children())
    app.press(app.results.files, '<<diagram-button-pressed>>')
    assert len(app.root.winfo_children()) == windows + 1
    app.root.menu.view.dark_var.set(False)
    app.root.event_generate('<<toggle-theme>>')
    app.update()
    assert log.cget('background') == PALETTES['light']['text_bg']
    assert app.errors() == []


@requires_driver
def test_new_file_clears_results(loaded_app):
    app = loaded_app
    run_calculation(app)
    app.load()
    assert 'Mass Summary' not in app.log_text()
    assert 'File Parsed Successfully.' in app.log_text()
    assert 'disabled' in app.results.files.save_button.state()
