import json
import pytest
from jsonschema import Draft7Validator
from optibar.core.tests.conftest import SCHEMA_PATH

LEVELS = ('top', 'bottom')


class TestOutput():
    def test_areas(self, output):
        areas = output._get_areas()
        assert len(areas['individuals']) > 0
        assert len(areas['union']) > 0

    def test_columns(self, output):
        columns = output._get_columns()
        assert len(columns) > 0
        assert all({'point', 'dim'} <= set(column) for column in columns)

    def test_material(self, output):
        material = output._get_material()
        assert material['fc'] > 0 and material['fy'] > 0

    def test_covers(self, output):
        covers = output._get_covers()
        assert set(covers) == {'side', 'top', 'bottom'}
        assert covers['side'] == 0.05

    def test_rebars(self, output):
        rebars = output._get_rebars()
        diameters = [rebar['diameter'] for rebar in rebars]
        assert diameters == sorted(diameters)
        for rebar in rebars:
            assert rebar['Ld']['top'] >= rebar['Ld']['bottom'] > 0

    def test_length_type(self, output):
        assert output._get_length_type() == {'total': 20, 'stack': 2}

    def test_technical_spec(self, output):
        assert set(output._get_technical_spec()) == {'material', 'covers', 'rebars', 'length_type'}

    def test_typical_thermal_piece_list(self, output):
        piece_dict = output._get_typical_thermal_piece_list()
        assert set(piece_dict) == {'typical', 'thermal'}
        for piece in piece_dict['typical']:
            assert piece['diameter'] == 18
            assert sum(piece['bend'].values()) == piece['number']

    def test_additional_piece_list(self, output):
        piece_list = output._get_additional_piece_list()
        assert len(piece_list) > 0
        for piece in piece_list:
            assert piece['diameter'] == 25
            assert sum(piece['bend'].values()) == piece['number']

    def test_shear_piece_list(self, output):
        piece_list = output._get_shear_piece_list()
        assert len(piece_list) > 0
        assert all(piece['diameter'] == 14 for piece in piece_list)

    def test_pieces(self, output):
        assert set(output._get_pieces()) == {'typical', 'thermal', 'additional', 'shear'}

    def test_concrete_volume(self, output):
        assert output._get_concrete_volume() > 0

    def test_masses(self, output):
        """the masses in the summary are the sums of the piece list masses (tons)"""
        additional = output._get_additional_mass()
        typical_thermal = output._get_typical_thermal_mass()
        assert set(additional) == set(LEVELS)
        assert set(typical_thermal) == {'typical', 'thermal'}
        assert output._get_shear_mass() > 0
        summary = output._get_summary()
        assert summary['rebar']['additional'] == additional
        assert summary['rebar']['typical'] == typical_thermal['typical']
        assert summary['concrete'] == output._get_concrete_volume()

    def test_shear_types(self, output):
        shear_types = output._get_shear_types()
        assert 0 < len(shear_types) <= 4
        assert [shear_type['id'] for shear_type in shear_types] == list(range(1, len(shear_types) + 1))

    def test_strips(self, output):
        strips = output._get_strips()
        names = output._get_strips_name()
        assert [strip['name'] for strip in strips] == names
        assert len(set(names)) == len(names)
        for strip in strips:
            assert set(strip['mesh']) == {'typical', 'additional'}
            assert set(strip['moment']) == {'ultimate', 'resistance'}
            for level in LEVELS:
                for kind in ('ultimate', 'resistance'):
                    moment = strip['moment'][kind][level]
                    assert len(moment['stations']) == len(moment['values'])

    def test_strips_shear_zones(self, output):
        ids = {shear_type['id'] for shear_type in output._get_shear_types()}
        for zones in output._get_strips_shear_zones():
            for zone in zones:
                assert zone['id'] in ids
                assert zone['period'][0] < zone['period'][1]

    def test_grid(self, output):
        grid = output._get_grid()
        for axis in ('X', 'Y'):
            ordinates = [line['ordinate'] for line in grid[axis]]
            assert ordinates == sorted(ordinates)

    def test_output(self, output):
        """the output, as saved to JSON, follows the output schema"""
        out = json.loads(json.dumps(output.get_output()))
        assert 'errors' not in out
        with open(SCHEMA_PATH.joinpath('output.json'), 'r') as file:
            schema = json.load(file)
        errors = [f'{list(error.path)}: {error.message}' for error in Draft7Validator(schema).iter_errors(out)]
        assert errors == []
