import json
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter.filedialog import asksaveasfilename
from tkinter.messagebox import showinfo, showerror
from typing import Dict
from optibar.gui.view.body.results import ResultsPane, Diagram, Stat
from optibar.gui.control.body.log import ReportLog
from optibar.gui.setting import VERSION
from optibar.core.sketch.sketch import Sketch
from optibar.core.sketch.dxf import DxfDrawing
from optibar.core.export import FORMATS, export
from .report import calc_report, analysis_report, diagram_data, settings_report, cutting_report, calc_summary, analysis_summary


class Result():
    def __init__(self, root: tk.Tk, result_note: ResultsPane, result_data: Dict, report: ReportLog) -> None:
        self.root = root
        self.result_data = result_data
        self.pane = result_note
        self.files = result_note.files
        self.report = report

        self.files.bind('<<diagram-button-pressed>>', self.draw_diagram)
        self.files.bind('<<save-button-pressed>>', self.save_results)
        self.files.bind('<<export-button-pressed>>', self.export_results)
        self.files.bind('<<pdf-button-pressed>>', lambda *args: self.save_drawing('pdf'))
        self.files.bind('<<dxf-button-pressed>>', lambda *args: self.save_drawing('dxf'))
        result_data['is_available'].trace_add('write', self.result_data_changed)
        result_data['stale'].trace_add('write', lambda *args: self.pane.set_stale(result_data['stale'].get()))

        # initialize
        result_data['is_available'].set(False)

    def draw_diagram(self, *args):
        """the mass of the analysis runs, total or additional, as the diagram window switches"""
        data = diagram_data(self.result_data['data']['result_data'])
        def masses(kinds):
            return {
                stack_num: {
                    'total_num': sorted(data[stack_num]),
                    'mass': [sum(data[stack_num][total_num][kind] for kind in kinds) for total_num in sorted(data[stack_num])],
                }
                for stack_num in sorted(data)
            }
        Diagram(self.root, {
            'Total': ('Total Mass', masses(('additional', 'typical', 'thermal'))),
            'Additional': ('Additional Rebar Mass', masses(('additional',))),
        })

    def result_data_changed(self, *args):
        if self.result_data['is_available'].get() == False:
            self.__refresh()
            return
        data = self.result_data['data']
        self.files.set_button_state('save', '!disabled')
        self.files.set_button_state('export', '!disabled')
        self.report.set_results(self._report())
        summary = calc_summary if data['calc_type'] == 'calculation' else analysis_summary
        self.pane.summary.show([Stat(*stat) for stat in summary(data['result_data'])])
        if data['calc_type'] == 'calculation':
            if 'data' in data['result_data']:
                self.files.set_button_state('pdf', '!disabled')
                self.files.set_button_state('dxf', '!disabled')
        elif data['calc_type'] == 'analysis':
            self.files.set_button_state('diagram', '!disabled')
        else:
            raise ValueError('type of result is not valid')

    def _report(self):
        data = self.result_data['data']
        if data['calc_type'] == 'calculation':
            return calc_report(data['result_data'])
        return analysis_report(data['result_data'])

    def _default_name(self) -> str:
        input_file = self.result_data['data'].get('input_file')
        stem = Path(input_file).stem if input_file else 'optibar'
        return f"{stem}_{self.result_data['data']['calc_type']}"

    def save_results(self, *args):
        """saves the full result as json and a readable summary next to it (<name>_summary.txt)"""
        path = asksaveasfilename(
            title='Save Results',
            initialfile=self._default_name() + '.json',
            defaultextension='.json',
            filetypes=[('JSON', '*.json')],
        )
        if not path:
            return
        path = Path(path)
        summary_path = path.with_name(path.stem + '_summary.txt')
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self._saved(), f, indent=2)
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(self._summary_text())
        except OSError as e:
            showerror('Save Results', f'The results could not be saved.\n\n{e}')
            return
        showinfo('Save Results', f'Saved:\n{path}\n{summary_path}')

    def _saved(self) -> Dict:
        """the result as Save Results writes it, and as the export prepares it"""
        data = self.result_data['data']
        return {
            'optibar_version': VERSION,
            'created': datetime.now().isoformat(timespec='seconds'),
            'input_file': data.get('input_file'),
            'calc_type': data['calc_type'],
            'config': data.get('config'),
            'result': data['result_data'],
        }

    def export_results(self, *args):
        """exports the result as tables: an Excel workbook, CSV files in a zip or JSON, by the extension"""
        path = asksaveasfilename(
            title='Export Results',
            initialfile=self._default_name() + '.xlsx',
            defaultextension='.xlsx',
            filetypes=[(format.name, f'*{format.extension}') for format in FORMATS.values()],
        )
        if not path:
            return
        path = Path(path)
        if path.suffix.lower() not in FORMATS:
            showerror('Export Results', f"Choose a file ending in {', '.join(FORMATS)}.")
            return
        try:
            export(self._saved(), path)
        except OSError as e:
            # e.g. the workbook is open in Excel
            showerror('Export Results', f'The results could not be exported.\n\n{e}')
            return
        showinfo('Export Results', f'Saved:\n{path}')

    def _summary_text(self) -> str:
        data = self.result_data['data']
        lines = [
            f"OPTiBAR {VERSION} {data['calc_type']} results",
            f"Created: {datetime.now().isoformat(sep=' ', timespec='seconds')}",
            f"Input file: {data.get('input_file') or '-'}",
            '',
        ]
        report = (settings_report(data['config']) if data.get('config') else []) + self._report()
        if data['calc_type'] == 'calculation' and 'data' in data['result_data']:
            # the overview is in the report above; the file also gets every pattern
            plans = data['result_data']['data'].get('cut', [])
            report += cutting_report(plans, overview=False, detailed=True)
        for tag, text in report:
            text = text.rstrip() # table cells are padded for the striped rows of the log
            lines.append(f'{tag}: {text}' if tag in ('WARNING', 'ERROR') else text)
        return '\n'.join(lines) + '\n'

    def save_drawing(self, kind: str):
        """saves the calculation as a pdf sketch or a dxf detailing map"""
        title, drawing = {'pdf': ('PDF Drawing', Sketch), 'dxf': ('DXF Drawing', DxfDrawing)}[kind]
        path = asksaveasfilename(
            title=f'Save {title}',
            initialfile=f'{self._default_name()}.{kind}',
            defaultextension=f'.{kind}',
            filetypes=[(kind.upper(), f'*.{kind}')],
        )
        if not path:
            return
        self.root.config(cursor='watch')
        self.root.update_idletasks()
        try:
            drawing(self.result_data['data']['result_data']['data']).save(path)
        except Exception as e:
            # e.g. the file is open in another program; cairo and ezdxf raise their own error types
            showerror(title, f'The drawing could not be saved.\n\n{e}')
            return
        finally:
            self.root.config(cursor='')
        showinfo(title, f'Saved:\n{path}')

    def __refresh(self):
        self.result_data['stale'].set(False)
        self.report.set_results([])
        self.pane.summary.clear()
        for name in ('save', 'export', 'pdf', 'dxf', 'diagram'):
            self.files.set_button_state(name, 'disabled')
