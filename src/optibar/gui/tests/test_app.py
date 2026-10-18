import json
import pathlib
import ezdxf
import pytest
from pypdf import PdfReader
import optibar.gui.control.body.upload as upload_module
from optibar.core.parser.parse import has_access_driver

# not imported from conftest: core/tests/parser has a conftest too, and only one is importable by that name
DATA_PATH = pathlib.Path(__file__).parents[2].joinpath('core', 'tests', 'parser', 'data_files')
requires_driver = pytest.mark.skipif(not has_access_driver(), reason='Microsoft Access ODBC driver is not installed')


def test_startup(app):
    assert 'disabled' in app.request.calculate_button.state()
    assert app.request.status_var.get() == 'Status: Waiting for input file ...'
    for name in ('save', 'pdf', 'dxf', 'diagram'):
        assert 'disabled' in getattr(app.notebook.results.files, name + '_button').state()


def test_startup_warns_when_driver_missing(monkeypatch, make_app):
    monkeypatch.setattr(upload_module, 'has_access_driver', lambda: False)
    app = make_app()
    log = app.log_text(app.notebook.upload.log)
    assert 'Access ODBC driver is not installed' in log
    assert 'https://www.microsoft.com/' in log


def test_load_with_driver_missing_offers_download(monkeypatch, app):
    monkeypatch.setattr('optibar.core.parser.parse.has_access_driver', lambda: False)
    app.answer_yes = True
    app.load()
    assert app.notebook.upload.browser.status_var.get() == 'Status: Failed'
    assert [d[0] for d in app.dialogs] == ['askyesno', 'browser']
    assert 'disabled' in app.request.calculate_button.state()


@requires_driver
def test_load_file(loaded_app):
    assert 'File Parsed Successfully.' in loaded_app.log_text(loaded_app.notebook.upload.log)
    assert loaded_app.request.status_var.get() == 'Status: Ready'
    assert 'disabled' not in loaded_app.request.calculate_button.state()
    assert loaded_app.notebook.calc.setting.advanced.special_length.get_values()['ld']['bottom'][0] > 0
    assert loaded_app.errors() == []


@requires_driver
def test_load_mdb(app):
    app.load(DATA_PATH.joinpath('tonf_m.mdb'))
    assert app.request.status_var.get() == 'Status: Ready'


@requires_driver
def test_load_errors(app):
    app.load(DATA_PATH.joinpath('missing_table', 'program_control.accdb'))
    assert app.errors()[-1][1] == 'Missing Table'
    app.load(DATA_PATH.joinpath('does_not_exist.accdb'))
    assert app.errors()[-1][1] == 'Unknown Error'
    assert 'disabled' in app.request.calculate_button.state()


def run_calculation(app):
    app.set_calc_type('calculation')
    app.calculate()
    assert app.request.status_var.get() == 'Status: Finished'


def run_analysis(app):
    app.set_calc_type('analysis')
    analysis = app.notebook.calc.setting.basic.type_num_analysis
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
    log = app.log_text(app.notebook.results.log)
    assert 'Mass Summary' in log
    files = app.notebook.results.files
    assert 'disabled' not in files.save_button.state()
    assert 'disabled' not in files.pdf_button.state()
    assert 'disabled' not in files.dxf_button.state()
    assert 'disabled' in files.diagram_button.state()
    assert app.errors() == []


@requires_driver
def test_save_calculation_results(loaded_app):
    app = loaded_app
    run_calculation(app)
    path = app.tmp_path.joinpath('result.json')
    app.press(app.notebook.results.files, '<<save-button-pressed>>', path)
    saved = json.loads(path.read_text(encoding='utf-8'))
    assert saved['calc_type'] == 'calculation'
    assert saved['input_file'].endswith('tonf_m.accdb')
    assert saved['config']['diameter']['typical'] == 18
    assert 'summary' in saved['result']['data']
    summary = app.tmp_path.joinpath('result_summary.txt').read_text(encoding='utf-8')
    assert 'Settings' in summary and 'Mass Summary' in summary and 'tonf_m.accdb' in summary
    assert app.errors() == []


@requires_driver
def test_save_pdf(loaded_app):
    app = loaded_app
    run_calculation(app)
    path = app.tmp_path.joinpath('drawing.pdf')
    app.press(app.notebook.results.files, '<<pdf-button-pressed>>', path)
    strips = len(app.notebook.calc.setting.advanced.typical.table.tree.get_children()) // 2
    assert len(PdfReader(path).pages) > strips
    assert app.errors() == []


@requires_driver
def test_save_dxf(loaded_app):
    app = loaded_app
    run_calculation(app)
    path = app.tmp_path.joinpath('drawing.dxf')
    app.press(app.notebook.results.files, '<<dxf-button-pressed>>', path)
    doc = ezdxf.readfile(path)
    assert doc.audit().errors == []
    assert 'Top Additional Rebars Of X Direction' in [e.text for e in doc.modelspace().query('MTEXT')]
    assert app.errors() == []


@requires_driver
def test_save_cancelled(loaded_app):
    app = loaded_app
    run_calculation(app)
    app.press(app.notebook.results.files, '<<save-button-pressed>>') # dialog returns '' when cancelled
    assert list(app.tmp_path.iterdir()) == []
    assert app.errors() == []


@requires_driver
def test_analysis(loaded_app):
    app = loaded_app
    progress = []
    app.request.status_var.trace_add('write', lambda *args: progress.append(app.request.status_var.get()))
    run_analysis(app)
    assert any('of 4 combinations done' in status for status in progress)
    log = app.log_text(app.notebook.results.log)
    assert 'Mass Report' in log
    files = app.notebook.results.files
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
    assert app.log_text(app.notebook.results.log) == ''
    assert 'disabled' in app.notebook.results.files.save_button.state()


@requires_driver
def test_progress_bar(loaded_app):
    app = loaded_app
    progress = app.request.progress # shown = placed in the grid; the tab itself may be hidden
    assert not progress.grid_info()
    app.request.event_generate('<<calc-pressed>>')
    app.update(0.2)
    assert progress.grid_info()
    app.wait_until(lambda: app.request.get_button_label() == 'Calculate')
    app.update()
    assert not progress.grid_info()

    values = []
    app.set_calc_type('analysis')
    analysis = app.notebook.calc.setting.basic.type_num_analysis
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
    log = app.notebook.results.log.text
    assert log.cget('background') == PALETTES['light']['text_bg']
    app.root.menu.view.dark_var.set(True)
    app.root.event_generate('<<toggle-theme>>')
    app.update()
    assert log.cget('background') == PALETTES['dark']['text_bg']
    assert log.tag_cget('INFO', 'foreground') == PALETTES['dark']['text_fg']
    tree = app.notebook.calc.setting.advanced.typical.table.tree
    assert str(tree.tag_configure('oddrow', 'background')) == PALETTES['dark']['stripe']
    # results still work and the diagram follows the theme
    run_analysis(app)
    windows = len(app.root.winfo_children())
    app.press(app.notebook.results.files, '<<diagram-button-pressed>>')
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
    assert app.log_text(app.notebook.results.log) == ''
    assert 'disabled' in app.notebook.results.files.save_button.state()
