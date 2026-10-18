import tkinter as tk
from typing import Dict
from gui.view.body.results import ResultNote, Diagram
import texttable


class Result():
    def __init__(self, root: tk.Tk, result_note: ResultNote, result_data: Dict) -> None:
        self.root = root
        self.result_data = result_data
        self.files = result_note.files
        self.log = result_note.log

        self.files.bind('<<diagram-button-pressed>>', self.draw_diagram)
        result_data['is_available'].trace_add('write', self.result_data_changed)

        # initialize
        result_data['is_available'].set(False)

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

    def result_data_changed(self, *args):
        if self.result_data['is_available'].get() == False:
            self.__refresh()
        else:
            if self.result_data['data']['calc_type'] == 'calculation':
                self.write_calc_log()
            elif self.result_data['data']['calc_type'] == 'analysis':
                self.files.set_diagram_button_state('!disabled')
                self.write_analysis_log()
            else:
                raise ValueError('type of result is not valid')

    def write_calc_log(self):
        output = self.result_data['data']['result_data']
        log = self.log

        if 'errors' in output:
            log.write_error(f"The minimum feasible total number of length types is {output['errors']['min_feasible_num']}")
            return

        # mass summary
        log.write_info('Mass Summary', indent=0)
        rebar = output['data']['summary']['rebar']
        table = texttable.Texttable(max_width=0) # auto adjustable width
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
        if 'warnings' in output:
            warning_data = output['warnings']
            if 'min_gap' in warning_data:
                log.write_warning("Min Gap Warning")
                table = texttable.Texttable(max_width=0) # auto adjustable width
                data = [['#', 'Strip', 'Elevation', 'Gap(cm)', 'Min Gap(cm)']]
                for i,mesh_data in enumerate(warning_data['min_gap']):
                    data.append([i+1, mesh_data['strip_name'], mesh_data['level'], "{:.1f}".format(mesh_data['detail']['gap']*100), "{:.1f}".format(mesh_data['detail']['min_gap']*100)])
                table.add_rows(data)
                log.write_warning(table.draw() + '\n')
            if 'min_ratio' in warning_data:
                log.write_warning("Ratio Warning (0.0018)")
                table = texttable.Texttable(max_width=0) # auto adjustable width
                data = [['#', 'Strip', 'Elevation', 'Number', 'Min number']]
                for i,mesh_data in enumerate(warning_data['min_ratio']):
                    data.append([i+1, mesh_data['strip_name'], mesh_data['level'], mesh_data['detail']['num'], mesh_data['detail']['min_num']])
                table.add_rows(data)
                log.write_warning(table.draw() + '\n')
            if 'max_gap' in warning_data:
                log.write_warning("Max Gap Warning")
                table = texttable.Texttable(max_width=0) # auto adjustable width
                data = [['#', 'Strip', 'Elevation', 'Gap', 'Max Gap']]
                for i,mesh_data in enumerate(warning_data['max_gap']):
                    data.append([i+1, mesh_data['strip_name'], mesh_data['level'], mesh_data['detail']['gap'], mesh_data['detail']['max_gap']])
                table.add_rows(data)
                log.write_warning(table.draw() + '\n')
            if 'excess_stack' in warning_data:
                log.write_warning("Excess Stack number")
                table = texttable.Texttable(max_width=0) # auto adjustable width
                data = [['#', 'Strip', 'Elevation', 'Excess List']]
                for i,mesh_data in enumerate(warning_data['excess_stack']):
                    data.append([i+1, mesh_data['strip_name'], mesh_data['level'], ', '.join(map(str,mesh_data['excess_list']))])
                table.add_rows(data)
                log.write_warning(table.draw() + '\n')

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
        self.files.set_diagram_button_state('disabled')
