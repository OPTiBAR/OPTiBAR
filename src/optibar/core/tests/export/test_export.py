import csv
import io
import json
import pathlib
import zipfile

import pytest
from openpyxl import load_workbook

from optibar.core.export import FORMATS, export, prepare
from optibar.core.export.tables import WASTE_LABEL, bar_mass_kg
from optibar.core.run import run_calculation

DATA_PATH = pathlib.Path(__file__).parent.parent.joinpath('data_files', 'parsed_data.json')
CONFIG = {
    "diameter": {"additional": 25, "shear": 14, "thermal": 12, "typical": 18},
    "elimination": {"additional": 0.2, "shear": 2.0},
    "type_number": {"shear": 4, "stack": 2, "total": 20},
    "side_cover": 0.05,
    "typical_arrangement": {"method": "INTERVAL", "value": 0.2, "exceptions": []},
}
CALCULATION_TABLES = [
    'Settings', 'Mass Summary', 'Typical Rebars', 'Thermal Rebars', 'Additional Rebars', 'Shear Rebars',
    'Shear Types', 'Cutting Plans', 'Cutting Patterns', 'Bars', 'Shear Zones', 'Specifications',
    'Rebar Specifications', 'Warnings',
]


def saved_result(calc_type, config, result):
    """what Save Results writes"""
    return {
        'optibar_version': '0.1.0', 'created': '2026-11-15T18:00:00', 'input_file': 'C:/projects/foundation.accdb',
        'calc_type': calc_type, 'config': config, 'result': result,
    }


@pytest.fixture(scope='module')
def output():
    with open(DATA_PATH) as f:
        return run_calculation(json.load(f), CONFIG)


@pytest.fixture(scope='module')
def saved(output):
    return saved_result('calculation', CONFIG, output)


@pytest.fixture(scope='module')
def tables(saved):
    return prepare(saved)


class TestPrepare():
    def test_tables(self, tables):
        assert tables.names() == CALCULATION_TABLES
        assert tables.meta['Input file'] == 'C:/projects/foundation.accdb'
        assert tables.meta['Type'] == 'calculation'
        for table in tables.tables:
            assert all(len(row) == len(table.columns) for row in table.rows), table.name

    def test_values_are_plain(self, tables):
        """numbers stay numbers, so a spreadsheet can sum them"""
        for table in tables.tables:
            for row in table.rows:
                assert all(v is None or isinstance(v, (int, float, str, bool)) for v in row), (table.name, row)
        weights = [row[-1] for row in tables['Additional Rebars'].rows]
        assert all(isinstance(w, float) for w in weights)

    def test_mass_summary(self, tables, output):
        rebar = output['data']['summary']['rebar']
        rows = {row[0]: row for row in tables['Mass Summary'].rows}
        assert rows['Additional'][1:] == pytest.approx(
            [rebar['additional']['top'], rebar['additional']['bottom'], rebar['additional']['top'] + rebar['additional']['bottom']])
        total = sum(rebar[k]['top'] + rebar[k]['bottom'] for k in ('typical', 'thermal', 'additional')) + rebar['shear']
        assert rows['Total'][3] == pytest.approx(total, abs=1e-3)

    def test_piece_list_weights_add_up_to_the_mass(self, tables, output):
        """the piece lists use the density of the engine: their weights add up to the summary"""
        rebar = output['data']['summary']['rebar']
        for title, kind in (('Typical Rebars', 'typical'), ('Additional Rebars', 'additional')):
            weight = sum(row[-1] for row in tables[title].rows)
            assert weight / 1000 == pytest.approx(rebar[kind]['top'] + rebar[kind]['bottom'], abs=0.005), title
        assert sum(row[-1] for row in tables['Shear Rebars'].rows) / 1000 == pytest.approx(rebar['shear'], abs=0.005)

    def test_positions_are_those_of_the_cutting_plans(self, tables, output):
        """every piece of a cutting plan refers to a row of the piece lists"""
        positions = {row[0] for name in ('Typical Rebars', 'Thermal Rebars', 'Additional Rebars', 'Shear Rebars')
                     for row in tables[name].rows}
        for plan in output['data']['cut']:
            for pattern in plan['patterns']:
                for piece in pattern['pieces']:
                    if piece['label'] != [WASTE_LABEL]:
                        assert set(piece['label']) <= positions

    def test_cutting(self, tables, output):
        plans = output['data']['cut']
        assert len(tables['Cutting Plans'].rows) == len(plans)
        assert len(tables['Cutting Patterns'].rows) == sum(len(plan['patterns']) for plan in plans)
        for row in tables['Cutting Patterns'].rows:
            stock = next(plan['stock_length'] for plan in plans if plan['diameter'] == row[0])
            assert row[4] + row[5] == pytest.approx(stock, abs=0.011) # used + waste

    def test_bars(self, tables, output):
        expected = 0
        for strip in output['data']['strips']:
            for level in ('top', 'bottom'):
                mesh = strip['mesh']
                expected += sum(1 for b in mesh['typical'][level] if b['number'])
                expected += sum(1 for row in mesh['additional'][level] for piece in row for b in piece if b['number'])
        assert len(tables['Bars'].rows) == expected
        for record in tables['Bars'].records():
            # start and end are rounded to the mm each
            assert record['Length'] == pytest.approx(record['End'] - record['Start'], abs=2.1e-3)

    def test_warnings(self, tables, output):
        warnings = output.get('warnings', {})
        assert len(tables['Warnings'].rows) == sum(len(w) for w in warnings.values())

    def test_settings_of_the_app(self, output):
        """the app's settings have tuples and lists of exceptions; every value comes out plain"""
        exceptions = [
            {'strip_name': 'CSA1', 'level': 'top', 'method': 'INTERVAL', 'value': 0.15, 'diameter': 20},
            {'strip_name': 'CSB1', 'level': 'bottom', 'method': 'COUNT', 'value': 12, 'diameter': 16},
        ]
        config = dict(CONFIG,
            typical_arrangement={'method': 'INTERVAL', 'value': 0.2, 'exceptions': exceptions},
            special_lengths={'diameters': (8, 10), 'ld': {'top': (0.37, 0.46)}})
        rows = {row[0]: row[1:] for row in prepare(saved_result('calculation', config, output))['Settings'].rows}
        assert rows['special_lengths.diameters'] == ['8, 10', 'mm']
        assert rows['special_lengths.ld.top'] == ['0.37, 0.46', 'm']
        assert rows['typical_arrangement.value'] == [0.2, 'm']
        assert rows['typical_arrangement.exceptions.1.value'] == [0.15, 'm'] # a spacing
        assert rows['typical_arrangement.exceptions.2.value'] == [12, None] # a number of bars
        assert rows['typical_arrangement.exceptions.2.diameter'] == [16, 'mm']
        assert rows['typical_arrangement.exceptions.1.strip_name'] == ['CSA1', None]

    def test_infeasible(self):
        tables = prepare(saved_result('calculation', CONFIG, {'errors': {'min_feasible_num': 12}}))
        assert tables.names() == ['Settings', 'Errors']
        assert tables['Errors'].rows[0][1] == 12

    def test_analysis(self, output):
        """a row per combination; one that isn't feasible has no masses"""
        config = dict(CONFIG, type_number={'stack': {'from': 2, 'to': 2}, 'total': {'from': 19, 'to': 20}, 'shear': 4})
        tables = prepare(saved_result('analysis', config, [{}, output['data']]))
        assert tables.names() == ['Settings', 'Analysis']
        infeasible, feasible = tables['Analysis'].records()
        assert (infeasible['Stack'], infeasible['Total'], infeasible['Feasible'], infeasible['Total mass']) == (2, 19, False, None)
        rebar = output['data']['summary']['rebar']
        assert feasible['Feasible'] is True
        assert feasible['Total mass'] == pytest.approx(sum(rebar[k]['top'] + rebar[k]['bottom'] for k in ('typical', 'thermal', 'additional')))

    def test_bar_mass(self):
        # one 1 m bar of 20 mm: 0.000314 m² x 7.85 t/m³ = 2.47 kg
        assert bar_mass_kg(20, 1, 1) == pytest.approx(2.466, abs=1e-3)


class TestWriters():
    def test_json(self, saved, tables, tmp_path):
        path = tmp_path / 'result.json'
        export(saved, path)
        content = json.loads(path.read_text(encoding='utf-8'))
        assert content['meta'] == tables.meta
        assert list(content['tables']) == tables.names()
        mass = content['tables']['Mass Summary']
        assert {'name': 'Top', 'unit': 't'} in mass['columns']
        assert mass['rows'] == tables['Mass Summary'].records()

    def test_csv_zip(self, saved, tables, tmp_path):
        path = tmp_path / 'result.zip'
        export(saved, path)
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            assert names[0] == '00_about.csv'
            assert names[1:] == [f'{i:02d}_{name.lower().replace(" ", "_")}.csv' for i, name in enumerate(tables.names(), start=1)]
            text = archive.read('05_additional_rebars.csv').decode('utf-8-sig')
        rows = list(csv.reader(io.StringIO(text)))
        assert rows[0] == [c.label for c in tables['Additional Rebars'].columns]
        assert len(rows) == len(tables['Additional Rebars'].rows) + 1
        assert float(rows[1][4]) == tables['Additional Rebars'].rows[0][4]

    def test_xlsx(self, saved, tables, tmp_path):
        path = tmp_path / 'result.xlsx'
        export(saved, path)
        workbook = load_workbook(path)
        assert workbook.sheetnames == ['About'] + tables.names()
        sheet = workbook['Mass Summary']
        assert [cell.value for cell in sheet[1]] == ['Type', 'Top (t)', 'Bottom (t)', 'Total (t)']
        assert [cell.value for cell in sheet[6]] == tables['Mass Summary'].rows[4] # numbers, not text
        about = {row[0].value: row[1].value for row in workbook['About'].iter_rows()}
        assert about['Input file'] == 'C:/projects/foundation.accdb'

    def test_every_format(self, saved, tmp_path):
        for extension in FORMATS:
            path = tmp_path / f'result{extension}'
            export(saved, path)
            assert path.stat().st_size > 0

    def test_unknown_format(self, saved, tmp_path):
        with pytest.raises(ValueError, match='unknown export format'):
            export(saved, tmp_path / 'result.txt')
