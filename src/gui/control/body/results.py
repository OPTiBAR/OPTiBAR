import json
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter.filedialog import asksaveasfilename
from tkinter.messagebox import showinfo, showerror
from typing import Dict
from gui.view.body.results import ResultNote, Diagram
from gui.setting import VERSION
from core.sketch.sketch import Sketch
from core.sketch.dxf import DxfDrawing
from .report import calc_report, analysis_report, diagram_data, settings_report


class Result():
    def __init__(self, root: tk.Tk, result_note: ResultNote, result_data: Dict) -> None:
        self.root = root
        self.result_data = result_data
        self.files = result_note.files
        self.log = result_note.log

        self.files.bind('<<diagram-button-pressed>>', self.draw_diagram)
        self.files.bind('<<save-button-pressed>>', self.save_results)
        self.files.bind('<<pdf-button-pressed>>', lambda *args: self.save_drawing('pdf'))
        self.files.bind('<<dxf-button-pressed>>', lambda *args: self.save_drawing('dxf'))
        result_data['is_available'].trace_add('write', self.result_data_changed)

        # initialize
        result_data['is_available'].set(False)

    def draw_diagram(self, *args):
        diagram_type = self.files.get_diagram_type()
        diagram = Diagram(self.root)
        data = diagram_data(self.result_data['data']['result_data'])
        mass_dict = {}
        for stack_num in sorted(data.keys()):
            mass_dict[stack_num] = {
                'total_num': [],
                'mass': [],
            }
            for total_num in sorted(data[stack_num].keys()):
                mass_dict[stack_num]['total_num'].append(total_num)
                if diagram_type == 'additional':
                    mass_dict[stack_num]['mass'].append(data[stack_num][total_num]['additional'])
                elif diagram_type == 'total':
                    mass = data[stack_num][total_num]['additional']
                    mass += data[stack_num][total_num]['typical']
                    mass += data[stack_num][total_num]['thermal']
                    mass_dict[stack_num]['mass'].append(mass)
                else:
                    raise ValueError('diagram type is not valid.')
        if diagram_type == 'total':
            title = 'Total Mass'
        elif diagram_type == 'additional':
            title = 'Additional Rebar Mass'
        else:
            raise ValueError('diagram type is not valid.')
        diagram.plot(mass_dict, title)

    def result_data_changed(self, *args):
        if self.result_data['is_available'].get() == False:
            self.__refresh()
            return
        data = self.result_data['data']
        self.files.set_button_state('save', '!disabled')
        self.log.write_lines(self._report())
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
        data = self.result_data['data']
        summary_path = path.with_name(path.stem + '_summary.txt')
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({
                    'optibar_version': VERSION,
                    'created': datetime.now().isoformat(timespec='seconds'),
                    'input_file': data.get('input_file'),
                    'calc_type': data['calc_type'],
                    'config': data.get('config'),
                    'result': data['result_data'],
                }, f, indent=2)
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(self._summary_text())
        except OSError as e:
            showerror('Save Results', f'The results could not be saved.\n\n{e}')
            return
        showinfo('Save Results', f'Saved:\n{path}\n{summary_path}')

    def _summary_text(self) -> str:
        data = self.result_data['data']
        lines = [
            f"OPTiBAR {VERSION} {data['calc_type']} results",
            f"Created: {datetime.now().isoformat(sep=' ', timespec='seconds')}",
            f"Input file: {data.get('input_file') or '-'}",
            '',
        ]
        report = (settings_report(data['config']) if data.get('config') else []) + self._report()
        for tag, text in report:
            lines.append(f'{tag}: {text}' if tag in ('WARNING', 'ERROR') and '\n' not in text else text)
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
        self.log.clear()
        for name in ('save', 'pdf', 'dxf', 'diagram'):
            self.files.set_button_state(name, 'disabled')
