import tkinter as tk
from typing import Dict
from src.view.utils.common import LogWindow
from src.view.utils.router import Router
from src.view.body.results import BugPopup, Diagram
from tkinter.messagebox import showinfo
from pathlib import Path
import subprocess
# from src.control.utils.mprocessing import Subprocess
from src.control.utils.urls import connection_error, get_header, get_url
from src.view.utils.router import Router
from src.control.utils.threading import tr_request, Monitor
from tkinter.messagebox import showinfo, showerror
from src.setting import STORAGE_PATH
import requests
import json
import texttable

TEMP_STORAGE_PATH = STORAGE_PATH.joinpath('temp')

class Result():
    def __init__(self, root: Router, token_var: tk.StringVar, result_data: Dict, acad_path: tk.StringVar) -> None:
        self.result_data = result_data
        self.acad_path = acad_path
        result_data['is_available'].trace_add('write', self.result_data_changed)
        result_note = root.get_child('notebook').get_child('results')
        self.files = result_note.get_child('files')
        self.bug = result_note.get_child('bug')
        self.log:LogWindow  = result_note.get_child('log')
        self.root = root
        self.token_var = token_var

        self.files.bind('<<diagram-button-pressed>>', self.draw_diagram)
        self.files.bind('<<dwg-button-pressed>>', self.draw_dwg)
        self.files.bind('<<language-changed>>', self.generate_drawing_files)
        self.bug.bind('<<report-bug-pressed>>', self.bug_fun)
        root.bind('<<bug-send-pressed>>', self.bug_send)

        # initialize
        result_data['is_available'].set(False)

        if not TEMP_STORAGE_PATH.is_dir():
            TEMP_STORAGE_PATH.mkdir()
    
    def bug_fun(self, *args):
        self.bug_popup = BugPopup(self.root)

    def bug_send(self, *args):
        def send_request():
            data = {'description':self.bug_popup.get_report()}
            url = get_url('report_bug', order_id = self.result_data['data']['order_id'])
            thread = tr_request(method='post', url=url, json=data, headers=get_header(self.token_var))
            Monitor(self.root).run(thread, handle)
        
        def handle(response: requests.Response):
            if response is not None:
                if  response.status_code == 201:
                    showinfo('Report', 'Report sent successfuly. It will be investigated by the thechnical team.')
                    self.bug_popup.close()
                else:
                    if response.status_code in (403,404):
                        showerror(f'Error {response.status_code}', response.json()['detail'])
                    else:
                        raise ValueError(f'unhandled status code {response.status_code}')
            else:
                connection_error()
        send_request()


    def draw_diagram(self, *args):
        diagram_type = self.files.get_diagram_type()
        diagram = Diagram(self.root)
        data = self.get_diagram_data()
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

    def generate_drawing_files(self, *args):
        # dll_folder_path = Path('.').joinpath('bin')
        dll_folder_path = (Path(__file__).parent.parent.parent.parent).joinpath('bin').absolute()
        dll_path = dll_folder_path.joinpath('AU.dll')
        scr_path = TEMP_STORAGE_PATH.joinpath('acript.scr')
        plot_path = TEMP_STORAGE_PATH.joinpath('plot.json')
        # make json file
        result = self.result_data['data']['result_data']['data']
        if self.files.get_language() == 'english':
            result['language'] = 'En'
        elif self.files.get_language() == 'persian':
            result['language'] = 'Fa'
        else:
            raise ValueError('language is not valid.')
        with open(plot_path, 'w') as f:
            json.dump(result, f)
        # make script file
        with open(scr_path, 'w') as f:
            f.write('_TRUSTEDPATHS' + '\n')
            f.write(f'{str(dll_folder_path.absolute())}' + '\n')
            f.write('MEASUREMENT\n')
            f.write('1\n')
            f.write('NETLOAD' + '\n')
            f.write(f'"{str(dll_path.absolute())}"' + '\n')
            f.write(f'OPTIBAR' + '\n')
        # run command
    
    def draw_dwg(self, *args):
        if self.acad_path.get() == '':
            showerror('Autocad Path', "We couldn't find the autocad .exe file automatically. please set it from Setting menu.")
            return None # early exit
        scr_path = TEMP_STORAGE_PATH.joinpath('acript.scr')
        subprocess.Popen(f'"{self.acad_path.get()}" /b {scr_path.absolute()}', shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    
    def result_data_changed(self, *args):
        if self.result_data['is_available'].get() == False:
            self.__refresh()
        else:
            # self.files.set_buttons_state(name='excel', state='!disabled')
            self.bug.set_button_state(state='!disabled')
            if self.result_data['data']['calc_type'] == 'calculation':
                self.write_calc_log()
                if len(self.result_data['data']['result_data']['data'].keys()) > 2:
                    self.files.set_buttons_state(name='dwg', state='!disabled')
                    self.generate_drawing_files()
                else:
                    showinfo('Mass Limit',  'Total mass of the rebars is more than your service level limit. please upgrade your service level to access DWG file.')
            elif self.result_data['data']['calc_type'] == 'analysis':
                self.files.set_buttons_state(name='diagram', state='!disabled')
                self.write_analysis_log()
            else:
                raise ValueError('type of result is not valid')
            
    def write_calc_log(self):
        result = self.result_data['data']['result_data']['data']
        log = self.log

        if 'errors' in self.result_data['data']['result_data']:
            error_data = self.result_data['data']['result_data']['errors']
            self.log.write_error(f"The minimum feasible total number of length types is {error_data['min_feasible_num']}")
        # additional rebar
        else:
            # mass summary
            log.write_info('Mass Summary', indent=0)
            # additional
            rebar = result['summary']['rebar']
            # table 
            table = texttable.Texttable(max_width=0) # auto adjustable width
            # tableObj.set_cols_align(["l", "l", "r", "c"])
            table.add_rows([
                ["Type of Rebars", "Top(ton)", "Bottom(ton)", "Total(ton)"],
                ["Typical", rebar['typical']['top'], rebar['typical']['bottom'], rebar['typical']['top'] + rebar['typical']['bottom']],
                ["Thermal", rebar['thermal']['top'], rebar['thermal']['bottom'], rebar['thermal']['top'] + rebar['thermal']['bottom']],
                ["Additional", rebar['additional']['top'], rebar['additional']['bottom'], rebar['additional']['top'] + rebar['additional']['bottom']],
                ["Shear", '-', '-', rebar['shear']],
                [
                    "Total",
                    rebar['typical']['top'] + rebar['thermal']['top'] + rebar['additional']['top'],
                    rebar['typical']['bottom'] + rebar['thermal']['bottom'] + rebar['additional']['bottom'],
                    rebar['typical']['top'] + rebar['typical']['bottom'] + rebar['thermal']['top'] + rebar['thermal']['bottom'] + rebar['additional']['top'] + rebar['additional']['bottom'] + rebar['shear'],
                ]
            ])
            log.write_info(table.draw() + '\n')

            # warnings
            if 'warnings' in self.result_data['data']['result_data']:
                warning_data = self.result_data['data']['result_data']['warnings']
                if 'min_gap' in warning_data:
                    self.log.write_warning("Min Gap Warning")
                    table = texttable.Texttable(max_width=0) # auto adjustable width
                    data = [['#', 'Strip', 'Elevation', 'Gap(cm)', 'Min Gap(cm)']]
                    for i,mesh_data in enumerate(warning_data['min_gap']):
                        data.append([i+1, mesh_data['strip_name'], mesh_data['level'], "{:.1f}".format(mesh_data['detail']['gap']*100), "{:.1f}".format(mesh_data['detail']['min_gap']*100)])
                    table.add_rows(data)
                    self.log.write_warning(table.draw() + '\n')
                if 'min_ratio' in warning_data:
                    self.log.write_warning("Ratio Warning (0.0018)")
                    table = texttable.Texttable(max_width=0) # auto adjustable width
                    data = [['#', 'Strip', 'Elevation', 'Number', 'Min number']]
                    for i,mesh_data in enumerate(warning_data['min_ratio']):
                        data.append([i+1, mesh_data['strip_name'], mesh_data['level'], mesh_data['detail']['num'], mesh_data['detail']['min_num']])
                    table.add_rows(data)
                    self.log.write_warning(table.draw() + '\n')
                if 'max_gap' in warning_data:
                    self.log.write_warning("Max Gap Warning")
                    table = texttable.Texttable(max_width=0) # auto adjustable width
                    data = [['#', 'Strip', 'Elevation', 'Gap', 'Max Gap']]
                    for i,mesh_data in enumerate(warning_data['max_gap']):
                        data.append([i+1, mesh_data['strip_name'], mesh_data['level'], mesh_data['detail']['gap'], mesh_data['detail']['max_gap']])
                    table.add_rows(data)
                    self.log.write_warning(table.draw() + '\n')
                if 'excess_stack' in warning_data:
                    self.log.write_warning("Excess Stack number")
                    table = texttable.Texttable(max_width=0) # auto adjustable width
                    data = [['#', 'Strip', 'Elevation', 'Excess List']]
                    for i,mesh_data in enumerate(warning_data['excess_stack']):
                        data.append([i+1, mesh_data['strip_name'], mesh_data['level'], ', '.join(map(str,mesh_data['excess_list']))])
                    table.add_rows(data)
                    self.log.write_warning(table.draw() + '\n')
            
            


    def write_analysis_log(self):
        log = self.log
        log.write_info("Mass Report")
        data = self.get_diagram_data()
        rows = [["#", 'stack', 'total', 'Thermal(ton)', 'Typical(ton)', 'Additional(ton)', 'Total(ton)'],]
        i = 1
        for stack_num in sorted(data.keys()):
            for total_num in sorted(data[stack_num].keys()):
                rows.append([
                    i,
                    stack_num,
                    total_num,
                    data[stack_num][total_num]['thermal'],
                    data[stack_num][total_num]['typical'],
                    data[stack_num][total_num]['additional'],
                    data[stack_num][total_num]['thermal']+data[stack_num][total_num]['typical']+data[stack_num][total_num]['additional'],
                ])
                i += 1
        table = texttable.Texttable(max_width=0)
        table.add_rows(rows)
        log.write_info(table.draw())
    
    def get_diagram_data(self) -> Dict:
        """returns data needed to plot analysis data

        Returns:
            Dict: data needed to plot analysis results
        """
        output = {}
        results = self.result_data['data']['result_data']
        for r in results:
            if r != {}:
                stack_num = r['technical_spec']['length_type']['stack']
                total_num = r['technical_spec']['length_type']['total']
                rebar = r['summary']['rebar']
                additional = rebar['additional']['top'] + rebar['additional']['bottom']
                typical = rebar['typical']['top'] + rebar['typical']['bottom']
                thermal = rebar['thermal']['top'] + rebar['thermal']['bottom']
                data = {
                    'additional': additional,
                    'typical': typical,
                    'thermal': thermal
                }
                if stack_num not in output:
                    output[stack_num] = {}
                output[stack_num][total_num] = data
                    
        return output

    def __refresh(self):
        self.log.clear()
        self.files.set_buttons_state(name='dwg', state='disabled')
        self.files.set_buttons_state(name='diagram', state='disabled')
        self.bug.set_button_state(state='disabled')
    
