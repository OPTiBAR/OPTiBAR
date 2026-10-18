"""builds the text report of a result, shown in the results log and saved as the summary file."""
from typing import Dict, List, Tuple
import texttable
from optibar.core.optimization.cut import pattern_text

# each line is (tag, text); tags match the LogWindow styles: INFO, WARNING, ERROR, SUCCESS
Report = List[Tuple[str, str]]


def calc_report(output: Dict) -> Report:
    if 'errors' in output:
        return [('ERROR', f"The minimum feasible total number of length types is {output['errors']['min_feasible_num']}")]

    report = []
    # mass summary
    report.append(('INFO', 'Mass Summary'))
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
    report.append(('INFO', table.draw() + '\n'))
    report.extend(cutting_report(output['data'].get('cut', [])))

    # warnings
    warning_data = output.get('warnings', {})
    if 'min_gap' in warning_data:
        data = [['#', 'Strip', 'Elevation', 'Gap(cm)', 'Min Gap(cm)']]
        for i,mesh_data in enumerate(warning_data['min_gap']):
            data.append([i+1, mesh_data['strip_name'], mesh_data['level'], "{:.1f}".format(mesh_data['detail']['gap']*100), "{:.1f}".format(mesh_data['detail']['min_gap']*100)])
        report.extend(_warning_table("Min Gap Warning", data))
    if 'min_ratio' in warning_data:
        data = [['#', 'Strip', 'Elevation', 'Number', 'Min number']]
        for i,mesh_data in enumerate(warning_data['min_ratio']):
            data.append([i+1, mesh_data['strip_name'], mesh_data['level'], mesh_data['detail']['num'], mesh_data['detail']['min_num']])
        report.extend(_warning_table("Ratio Warning (0.0018)", data))
    if 'max_gap' in warning_data:
        data = [['#', 'Strip', 'Elevation', 'Gap', 'Max Gap']]
        for i,mesh_data in enumerate(warning_data['max_gap']):
            data.append([i+1, mesh_data['strip_name'], mesh_data['level'], mesh_data['detail']['gap'], mesh_data['detail']['max_gap']])
        report.extend(_warning_table("Max Gap Warning", data))
    if 'excess_stack' in warning_data:
        data = [['#', 'Strip', 'Elevation', 'Excess List']]
        for i,mesh_data in enumerate(warning_data['excess_stack']):
            data.append([i+1, mesh_data['strip_name'], mesh_data['level'], ', '.join(map(str,mesh_data['excess_list']))])
        report.extend(_warning_table("Excess Stack number", data))
    return report


def cutting_report(plans: List[Dict], detailed: bool = False) -> Report:
    """bars and waste of the cutting plan per diameter; with detailed, every pattern too"""
    if not plans:
        return []
    stock = plans[0]['stock_length']
    table = texttable.Texttable(max_width=0)
    table.set_cols_dtype(['t', 'i', 'f', 't', 'i'])
    table.set_precision(2)
    table.add_rows([[f"Diameter(mm)", f"Bars({stock:g}m)", "Waste(m)", "Waste(%)", "Patterns"]] + [
        [plan['diameter'], plan['bars'], plan['waste'], f"{100 * plan['waste_ratio']:.1f}", len(plan['patterns'])]
        for plan in plans
    ])
    report = [('INFO', 'Cutting Plans'), ('INFO', table.draw() + '\n')]
    if detailed:
        for plan in plans:
            report.append(('INFO', f"Cutting Plan, diameter {plan['diameter']}"))
            table = texttable.Texttable(max_width=0)
            table.set_cols_dtype(['i', 'i', 't', 't'])
            rows = [['#', 'Bars', 'Pieces (m), position in the piece lists', 'Waste(m)']]
            for i, pattern in enumerate(plan['patterns'], start=1):
                rows.append([i, pattern['number'], pattern_text(pattern), f"{pattern['waste']:g}"])
            table.add_rows(rows)
            report.append(('INFO', table.draw() + '\n'))
    return report


def _warning_table(title: str, rows: List[List]) -> Report:
    table = texttable.Texttable(max_width=0) # auto adjustable width
    table.add_rows(rows)
    return [('WARNING', title), ('WARNING', table.draw() + '\n')]


def analysis_report(results: List[Dict]) -> Report:
    data = diagram_data(results)
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
    return [('INFO', "Mass Report"), ('INFO', table.draw())]


def diagram_data(results: List[Dict]) -> Dict:
    """returns the rebar masses of each analysis run, keyed by stack and total number of types"""
    output = {}
    for r in results:
        if r != {}:
            stack_num = r['technical_spec']['length_type']['stack']
            total_num = r['technical_spec']['length_type']['total']
            rebar = r['summary']['rebar']
            if stack_num not in output:
                output[stack_num] = {}
            output[stack_num][total_num] = {
                'additional': rebar['additional']['top'] + rebar['additional']['bottom'],
                'typical': rebar['typical']['top'] + rebar['typical']['bottom'],
                'thermal': rebar['thermal']['top'] + rebar['thermal']['bottom'],
            }
    return output


def settings_report(config: Dict) -> Report:
    """the main calculation settings, for the head of the summary file"""
    type_number = config['type_number']
    def type_value(value):
        return f"{value['from']} to {value['to']}" if isinstance(value, dict) else str(value)
    rows = [
        ['Setting', 'Value'],
        ['Diameter typical / additional / thermal / shear', ' / '.join(str(config['diameter'][k]) for k in ('typical', 'additional', 'thermal', 'shear'))],
        ['Typical interval (m)', config['typical_arrangement']['value']],
        ['Side cover (m)', config['side_cover']],
        ['Elimination additional / shear (m)', f"{config['elimination']['additional']} / {config['elimination']['shear']}"],
        ['Number of length types, total', type_value(type_number['total'])],
        ['Number of length types, stack', type_value(type_number['stack'])],
        ['Number of shear types', type_value(type_number['shear'])],
    ]
    table = texttable.Texttable(max_width=0)
    table.add_rows(rows)
    return [('INFO', 'Settings'), ('INFO', table.draw() + '\n')]
