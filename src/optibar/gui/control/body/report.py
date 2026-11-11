"""builds the text report of a result, shown in the results log and saved as the summary file."""
from typing import Dict, List, Optional, Sequence, Tuple
from optibar.core.optimization.cut import pattern_text

# each line is (tag, text), one line of text per item; the tags are styled by LogWindow:
#   INFO, SUCCESS, WARNING, ERROR   plain messages
#   HEADING, WARNING_HEADING        section titles
#   TABLE_HEAD, RULE, ROW, ROW_ALT, TOTAL   the lines of a table
Report = List[Tuple[str, str]]

COLUMN_GAP = '   '
DASH = '–'


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _cell(value, decimals: int) -> str:
    if isinstance(value, float):
        return f'{value:.{decimals}f}'
    return str(value)


def table(head: Sequence[str], rows: Sequence[Sequence], total: Optional[Sequence] = None, decimals: int = 3) -> Report:
    """a table without grid lines: bold header, a rule under it, striped rows and an optional total row.
    Numeric columns (numbers and dashes only) are right-aligned; floats get the given decimals."""
    body = [[_cell(v, decimals) for v in row] for row in rows]
    total_cells = [_cell(v, decimals) for v in total] if total is not None else None
    all_rows = [list(head)] + body + ([total_cells] if total_cells else [])
    widths = [max(len(row[i]) for row in all_rows) for i in range(len(head))]
    numeric = [
        all(_is_number(row[i]) or row[i] in ('-', DASH) for row in list(rows) + ([total] if total else []))
        and any(_is_number(row[i]) for row in list(rows) + ([total] if total else []))
        for i in range(len(head))
    ]

    def line(cells: Sequence[str]) -> str:
        return COLUMN_GAP.join(
            cell.rjust(widths[i]) if numeric[i] else cell.ljust(widths[i]) for i, cell in enumerate(cells))

    rule = '─' * (sum(widths) + len(COLUMN_GAP) * (len(widths) - 1))
    report = [('TABLE_HEAD', line(head)), ('RULE', rule)]
    for i, row in enumerate(body):
        report.append(('ROW_ALT' if i % 2 else 'ROW', line(row)))
    if total_cells:
        report += [('RULE', rule), ('TOTAL', line(total_cells))]
    report.append(('INFO', ''))
    return report


def _heading(title: str) -> Report:
    return [('HEADING', title), ('INFO', '')]


def _warning_table(title: str, head: Sequence[str], rows: Sequence[Sequence], decimals: int = 1) -> Report:
    return [('WARNING_HEADING', '⚠ ' + title), ('INFO', '')] + table(head, rows, decimals=decimals)


def calc_report(output: Dict) -> Report:
    if 'errors' in output:
        return [('ERROR', f"The minimum feasible total number of length types is {output['errors']['min_feasible_num']}")]

    report = _heading('Mass Summary')
    # masses can come as int 0, show them like the others
    rebar = {kind: ({level: float(v) for level, v in value.items()} if isinstance(value, dict) else float(value))
             for kind, value in output['data']['summary']['rebar'].items()}
    level_sum = lambda level: sum(rebar[kind][level] for kind in ('typical', 'thermal', 'additional'))
    report += table(
        ["Type of Rebars", "Top (t)", "Bottom (t)", "Total (t)"],
        [
            ["Typical", rebar['typical']['top'], rebar['typical']['bottom'], rebar['typical']['top'] + rebar['typical']['bottom']],
            ["Thermal", rebar['thermal']['top'], rebar['thermal']['bottom'], rebar['thermal']['top'] + rebar['thermal']['bottom']],
            ["Additional", rebar['additional']['top'], rebar['additional']['bottom'], rebar['additional']['top'] + rebar['additional']['bottom']],
            ["Shear", DASH, DASH, rebar['shear']],
        ],
        total=["Total", level_sum('top'), level_sum('bottom'), level_sum('top') + level_sum('bottom') + rebar['shear']],
    )
    report += cutting_report(output['data'].get('cut', []))

    # warnings
    warning_data = output.get('warnings', {})
    if 'min_gap' in warning_data:
        rows = [[i + 1, w['strip_name'], w['level'], w['detail']['gap'] * 100, w['detail']['min_gap'] * 100]
                for i, w in enumerate(warning_data['min_gap'])]
        report += _warning_table("Min Gap Warning", ['#', 'Strip', 'Level', 'Gap (cm)', 'Min gap (cm)'], rows)
    if 'min_ratio' in warning_data:
        rows = [[i + 1, w['strip_name'], w['level'], w['detail']['num'], w['detail']['min_num']]
                for i, w in enumerate(warning_data['min_ratio'])]
        report += _warning_table("Ratio Warning (0.0018)", ['#', 'Strip', 'Level', 'Bars', 'Min bars'], rows)
    if 'max_gap' in warning_data:
        rows = [[i + 1, w['strip_name'], w['level'], w['detail']['gap'] * 100, w['detail']['max_gap'] * 100]
                for i, w in enumerate(warning_data['max_gap'])]
        report += _warning_table("Max Gap Warning", ['#', 'Strip', 'Level', 'Gap (cm)', 'Max gap (cm)'], rows)
    if 'excess_stack' in warning_data:
        rows = [[i + 1, w['strip_name'], w['level'], ', '.join(map(str, w['excess_list']))]
                for i, w in enumerate(warning_data['excess_stack'])]
        report += _warning_table("Excess Stack Number", ['#', 'Strip', 'Level', 'Length types used'], rows)
    return report


def cutting_report(plans: List[Dict], overview: bool = True, detailed: bool = False) -> Report:
    """bars and waste of the cutting plan per diameter; with detailed, every pattern too"""
    if not plans:
        return []
    report = []
    if overview:
        stock = plans[0]['stock_length']
        report += _heading('Cutting Plans')
        report += table(
            ["Diameter (mm)", f"Bars ({stock:g} m)", "Waste (m)", "Waste (%)", "Patterns"],
            [[plan['diameter'], plan['bars'], float(plan['waste']), 100 * plan['waste_ratio'], len(plan['patterns'])] for plan in plans],
            decimals=1,
        )
    if detailed:
        for plan in plans:
            report += _heading(f"Cutting Plan, diameter {plan['diameter']}")
            report += table(
                ['#', 'Bars', 'Pieces (m), position in the piece lists', 'Waste (m)'],
                [[i, pattern['number'], pattern_text(pattern), f"{pattern['waste']:g}"]
                 for i, pattern in enumerate(plan['patterns'], start=1)],
            )
    return report


def analysis_report(results: List[Dict]) -> Report:
    data = diagram_data(results)
    rows = []
    for stack_num in sorted(data.keys()):
        for total_num in sorted(data[stack_num].keys()):
            masses = {kind: float(mass) for kind, mass in data[stack_num][total_num].items()}
            rows.append([
                len(rows) + 1, stack_num, total_num,
                masses['thermal'], masses['typical'], masses['additional'],
                masses['thermal'] + masses['typical'] + masses['additional'],
            ])
    return _heading("Mass Report") + table(
        ["#", 'Stack', 'Total', 'Thermal (t)', 'Typical (t)', 'Additional (t)', 'Total (t)'], rows)


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
        ['Diameter typical / additional / thermal / shear (mm)', ' / '.join(str(config['diameter'][k]) for k in ('typical', 'additional', 'thermal', 'shear'))],
        ['Typical interval (m)', str(config['typical_arrangement']['value'])],
        ['Side cover (m)', str(config['side_cover'])],
        ['Elimination additional / shear (m)', f"{config['elimination']['additional']} / {config['elimination']['shear']}"],
        ['Number of length types, total', type_value(type_number['total'])],
        ['Number of length types, stack', type_value(type_number['stack'])],
        ['Number of shear types', type_value(type_number['shear'])],
    ]
    return _heading('Settings') + table(['Setting', 'Value'], rows)
