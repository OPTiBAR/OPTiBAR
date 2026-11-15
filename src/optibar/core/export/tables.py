"""prepares a result for export: format-neutral tables of plain values, built once, written by the writers.

The input is the saved result, the dictionary that Save Results writes to its JSON file:
{"optibar_version", "created", "input_file", "calc_type", "config", "result"}. So the tables can be made
right after a calculation, or later from a results file.

Values are numbers, strings, booleans or None (an empty cell), never formatted text, so a spreadsheet
can sum and sort them. Units are in the columns, not in the values. Lengths are in m, masses of piece
lists in kg and of summaries in t, as in the drawing and the report.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from optibar.core.optimization.cut import LABEL_PREFIX, WASTE_LABEL, pattern_text
from optibar.core.setting import STEEL_DENSITY

SHAPES = {'no_side': 'straight', 'one_side': 'bent at one end', 'two_side': 'bent at both ends'}
REBAR_TYPES = (('typical', 'Typical Rebars'), ('thermal', 'Thermal Rebars'), ('additional', 'Additional Rebars'))


@dataclass
class Column:
    name: str
    unit: Optional[str] = None

    @property
    def label(self) -> str:
        """the header of the column: the name with its unit"""
        return f'{self.name} ({self.unit})' if self.unit else self.name


@dataclass
class Table:
    name: str
    columns: List[Column]
    rows: List[List[Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        names = [c.name for c in self.columns]
        if len(set(names)) != len(names):
            raise ValueError(f'the columns of {self.name} need distinct names: {names}')

    def records(self) -> List[Dict[str, Any]]:
        """the rows as dictionaries keyed by column name"""
        return [dict(zip((c.name for c in self.columns), row)) for row in self.rows]


@dataclass
class Tables:
    """a prepared result: what it is (meta) and its tables, in the order to show them"""
    meta: Dict[str, Any]
    tables: List[Table]

    def __getitem__(self, name: str) -> Table:
        return next(t for t in self.tables if t.name == name)

    def names(self) -> List[str]:
        return [t.name for t in self.tables]


def columns(*specs) -> List[Column]:
    """columns from names, or (name, unit) pairs"""
    return [Column(*spec) if isinstance(spec, tuple) else Column(spec) for spec in specs]


def bar_mass_kg(diameter_mm: float, length: float, number: int) -> float:
    """mass of a number of bars in kg, with the density the engine uses"""
    area = math.pi * diameter_mm ** 2 / 4 / 1e6 # m²
    return area * length * number * STEEL_DENSITY * 1000


def prepare(saved: Dict) -> Tables:
    """the tables of a saved result: a computation, an infeasible computation or an analysis"""
    meta = {
        'OPTiBAR version': saved.get('optibar_version'),
        'Created': saved.get('created'),
        'Input file': saved.get('input_file'),
        'Type': saved['calc_type'],
    }
    tables = [_settings(saved.get('config') or {})]
    result = saved['result']
    if saved['calc_type'] == 'analysis':
        tables.append(_analysis(result, saved.get('config') or {}))
    elif 'errors' in result:
        tables.append(_errors(result['errors']))
    else:
        tables += _calculation(result['data'], result.get('warnings', {}))
    return Tables(meta, tables)


# --- settings ---------------------------------------------------------------------------------

# the unit of a setting and the settings under it; the first match counts, so more specific keys come first.
# The value of a typical arrangement (or of an exception to it) is a spacing in m only for the INTERVAL
# method, see _settings.
SETTING_UNITS = {
    'diameter': 'mm', 'side_cover': 'm', 'elimination': 'm',
    'special_lengths.diameters': 'mm', 'special_lengths': 'm',
}


def _flatten(config: Dict, prefix: str = '') -> Iterable[tuple]:
    for key, value in config.items():
        name = f'{prefix}{key}'
        if isinstance(value, dict):
            yield from _flatten(value, name + '.')
        elif isinstance(value, (list, tuple)):
            if value and isinstance(value[0], dict): # e.g. the exceptions of the typical arrangement
                yield from _flatten({str(i): item for i, item in enumerate(value, start=1)}, name + '.')
            else:
                yield name, ', '.join(map(str, value))
        elif value is None or isinstance(value, (int, float, str, bool)):
            yield name, value
        else:
            yield name, str(value)


def _settings(config: Dict) -> Table:
    table = Table('Settings', columns('Setting', 'Value', 'Unit'))
    settings = dict(_flatten(config))
    for name, value in settings.items():
        unit = next((u for key, u in SETTING_UNITS.items() if name == key or name.startswith(key + '.')), None)
        if name.startswith('typical_arrangement.'):
            group = name.rsplit('.', 1)[0]
            if name.endswith('.value') and settings.get(f'{group}.method') == 'INTERVAL':
                unit = 'm'
            elif name.endswith('.diameter'):
                unit = 'mm'
        table.rows.append([name, value, unit])
    return table


# --- computation ------------------------------------------------------------------------------

def _calculation(data: Dict, warnings: Dict) -> List[Table]:
    return [
        _mass_summary(data['summary']),
        *(_piece_list(title, data['pieces'].get(kind, []), LABEL_PREFIX[kind]) for kind, title in REBAR_TYPES),
        _shear_piece_list(data['pieces'].get('shear', [])),
        _shear_types(data.get('shear_types', [])),
        _cutting_plans(data.get('cut', [])),
        _cutting_patterns(data.get('cut', [])),
        _bars(data['strips']),
        _shear_zones(data['strips']),
        _specifications(data['technical_spec'], data['summary']),
        _rebar_specifications(data['technical_spec']['rebars']),
        _warnings(warnings),
    ]


def _mass_summary(summary: Dict) -> Table:
    rebar = summary['rebar']
    table = Table('Mass Summary', columns('Type', ('Top', 't'), ('Bottom', 't'), ('Total', 't')))
    for kind in ('typical', 'thermal', 'additional'):
        top, bottom = float(rebar[kind]['top']), float(rebar[kind]['bottom'])
        table.rows.append([kind.capitalize(), top, bottom, round(top + bottom, 3)])
    table.rows.append(['Shear', None, None, float(rebar['shear'])])
    top = sum(row[1] for row in table.rows[:3])
    bottom = sum(row[2] for row in table.rows[:3])
    table.rows.append(['Total', round(top, 3), round(bottom, 3), round(top + bottom + float(rebar['shear']), 3)])
    return table


def _piece_list(title: str, pieces: List[Dict], prefix: str) -> Table:
    """one row per piece and bend shape, numbered like the piece lists of the drawing (T1, A3, ...)"""
    table = Table(title, columns('Position', ('Diameter', 'mm'), 'Shape', 'Number', ('Length', 'm'), ('Weight', 'kg')))
    for piece in pieces:
        for shape in SHAPES:
            number = piece['bend'][shape]
            if number:
                position = f'{prefix}{len(table.rows) + 1}'
                weight = round(bar_mass_kg(piece['diameter'], piece['length'], number), 1)
                table.rows.append([position, piece['diameter'], SHAPES[shape], number, piece['length'], weight])
    return table


def _shear_piece_list(pieces: List[Dict]) -> Table:
    table = Table('Shear Rebars', columns('Position', ('Diameter', 'mm'), 'Number', ('Length', 'm'), ('Weight', 'kg')))
    for row, piece in enumerate(pieces, start=1):
        weight = round(bar_mass_kg(piece['diameter'], piece['length'], piece['number']), 1)
        table.rows.append([f"{LABEL_PREFIX['shear']}{row}", piece['diameter'], piece['number'], piece['length'], weight])
    return table


def _shear_types(shear_types: List[Dict]) -> Table:
    table = Table('Shear Types', columns('Type', ('Diameter', 'mm'), 'Legs', ('Spacing', 'm')))
    for shear_type in shear_types:
        table.rows.append([int(shear_type['id']), shear_type['diameter'], shear_type['number'], shear_type['interval']])
    return table


def _cutting_plans(plans: List[Dict]) -> Table:
    table = Table('Cutting Plans', columns(
        ('Diameter', 'mm'), ('Stock length', 'm'), 'Bars', 'Optimal', 'Lower bound', ('Waste', 'm'), ('Waste share', '%'), 'Patterns'))
    for plan in plans:
        table.rows.append([
            plan['diameter'], plan['stock_length'], plan['bars'], plan.get('optimal'), plan.get('lower_bound'),
            round(float(plan['waste']), 2), round(100 * plan['waste_ratio'], 1), len(plan['patterns']),
        ])
    return table


def _cutting_patterns(plans: List[Dict]) -> Table:
    """one row per pattern; the pieces are grouped, with their position in the piece lists"""
    table = Table('Cutting Patterns', columns(
        ('Diameter', 'mm'), 'Pattern', 'Bars', 'Pieces', ('Used', 'm'), ('Waste', 'm')))
    for plan in plans:
        for number, pattern in enumerate(plan['patterns'], start=1):
            used = sum(p['length'] for p in pattern['pieces'] if p['label'] != [WASTE_LABEL])
            table.rows.append([plan['diameter'], number, pattern['number'], pattern_text(pattern), round(used, 2), pattern['waste']])
    return table


def _bars(strips: List[Dict]) -> Table:
    """every bar along every strip: typical rebars, and additional ones by row; a bar longer than the
    stock length is spliced from several pieces, one row each"""
    table = Table('Bars', columns(
        'Strip', 'Level', 'Kind', 'Row', 'Piece', 'Number', ('Diameter', 'mm'),
        ('Start', 'm'), ('End', 'm'), ('Length', 'm'), ('Bend at start', 'm'), ('Bend at end', 'm'), 'Spliced'))

    def add(strip, level, kind, row, piece, bunch, spliced):
        if bunch['number'] == 0:
            return
        start, end = bunch['stations']
        table.rows.append([
            strip['name'], level, kind, row, piece, bunch['number'], bunch['diameter'],
            round(start, 3), round(end, 3), round(end - start, 3), bunch['bends'][0], bunch['bends'][1], spliced,
        ])

    for strip in strips:
        mesh = strip['mesh']
        for level in ('top', 'bottom'):
            for bunch in mesh['typical'][level]:
                add(strip, level, 'typical', None, None, bunch, False)
            for row_number, row in enumerate(mesh['additional'][level], start=1):
                for piece in row:
                    for k, bunch in enumerate(piece, start=1):
                        add(strip, level, 'additional', row_number, k, bunch, len(piece) > 1)
    return table


def _shear_zones(strips: List[Dict]) -> Table:
    table = Table('Shear Zones', columns('Strip', 'Type', ('Start', 'm'), ('End', 'm'), ('Length', 'm')))
    for strip in strips:
        for zone in strip['shear_zones']:
            start, end = zone['period']
            table.rows.append([strip['name'], int(zone['id']), round(start, 3), round(end, 3), round(end - start, 3)])
    return table


def _specifications(spec: Dict, summary: Dict) -> Table:
    """materials, covers, numbers of length types and the concrete volume"""
    table = Table('Specifications', columns('Item', 'Value', 'Unit'))
    material, covers = spec['material'], spec['covers']
    table.rows += [
        ["Concrete strength f'c", round(material['fc'] / 10, 1), 'kg/cm²'],
        ['Steel yield strength fy', round(material['fy'] / 10, 1), 'kg/cm²'],
        ['Side cover', covers['side'], 'm'],
        ['Top cover', covers['top'], 'm'],
        ['Bottom cover', covers['bottom'], 'm'],
        ['Length types per stack', spec['length_type']['stack'], None],
        ['Length types in total', spec['length_type']['total'], None],
        ['Concrete volume', summary['concrete'], 'm³'],
    ]
    return table


def _rebar_specifications(rebars: List[Dict]) -> Table:
    table = Table('Rebar Specifications', columns(
        ('Diameter', 'mm'), ('Bend 90°', 'm'), ('Bend 135°', 'm'), ('Ld top', 'm'), ('Ld bottom', 'm'),
        ('Overlap top', 'm'), ('Overlap bottom', 'm')))
    for rebar in rebars:
        table.rows.append([
            rebar['diameter'], rebar['bend']['B90'], rebar['bend']['B135'], rebar['Ld']['top'], rebar['Ld']['bottom'],
            rebar['overlap']['top'], rebar['overlap']['bottom'],
        ])
    return table


# warning key: (name, value and limit keys of its detail, unit)
WARNINGS = {
    'min_gap': ('Min gap', 'gap', 'min_gap', 'm'),
    'max_gap': ('Max gap', 'gap', 'max_gap', 'm'),
    'min_ratio': ('Ratio (0.0018)', 'num', 'min_num', 'bars'),
}


def _warnings(warnings: Dict) -> Table:
    """the warnings of the report: value against the limit; for an excess stack, the length types used"""
    table = Table('Warnings', columns('Warning', 'Strip', 'Level', 'Value', 'Limit', 'Unit'))
    for key, (name, value, limit, unit) in WARNINGS.items():
        for w in warnings.get(key, []):
            table.rows.append([name, w['strip_name'], w['level'], w['detail'][value], w['detail'][limit], unit])
    for w in warnings.get('excess_stack', []):
        table.rows.append(['Excess stack number', w['strip_name'], w['level'], ', '.join(map(str, w['excess_list'])), None, 'length types'])
    return table


def _errors(errors: Dict) -> Table:
    table = Table('Errors', columns('Error', 'Value'))
    if 'min_feasible_num' in errors:
        table.rows.append(['The total number of length types is too small; the minimum feasible is', errors['min_feasible_num']])
    return table


# --- analysis ---------------------------------------------------------------------------------

def _analysis(results: List[Dict], config: Dict) -> Table:
    """the masses of every combination of stack and total; empty for a combination that isn't feasible.
    The total mass leaves out the shear rebars, as the report and the diagram of the app do."""
    table = Table('Analysis', columns(
        'Stack', 'Total', 'Feasible', ('Typical', 't'), ('Thermal', 't'), ('Additional', 't'), ('Total mass', 't'), ('Shear', 't')))
    type_number = config.get('type_number', {})
    pairs = None
    if isinstance(type_number.get('stack'), dict) and isinstance(type_number.get('total'), dict):
        pairs = [(stack, total)
                 for stack in range(type_number['stack']['from'], type_number['stack']['to'] + 1)
                 for total in range(type_number['total']['from'], type_number['total']['to'] + 1)]
        if len(pairs) != len(results):
            pairs = None
    for i, data in enumerate(results):
        if data:
            length_type = data['technical_spec']['length_type']
            rebar = data['summary']['rebar']
            masses = [round(float(rebar[k]['top']) + float(rebar[k]['bottom']), 3) for k in ('typical', 'thermal', 'additional')]
            table.rows.append([length_type['stack'], length_type['total'], True, *masses, round(sum(masses), 3), float(rebar['shear'])])
        elif pairs:
            table.rows.append([*pairs[i], False, None, None, None, None, None])
    return table
