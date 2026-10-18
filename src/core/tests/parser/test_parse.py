import pytest
import pathlib
import json
from jsonschema import Draft7Validator
from core.parser.parse import V16Parser, has_access_driver
from core.parser.errors import TableMissingError, DriverMissingError

pytestmark = pytest.mark.skipif(not has_access_driver(), reason='Microsoft Access ODBC driver is not installed')

DATA_PATH = pathlib.Path(__file__).parent.joinpath('data_files')
SCHEMA_PATH = pathlib.Path(__file__).parent.parent.parent.joinpath('parser', 'schemas', 'input.json')

grid_data = {
    'X': [
        {'name': 'A', 'ordinate': 0.0},
        {'name': 'B', 'ordinate': 6.0},
        {'name': 'C', 'ordinate': 12.0},
        {'name': 'D', 'ordinate': 18.0}
        ],
    'Y': [
        {'name': '1', 'ordinate': 0.0},
        {'name': '2', 'ordinate': 6.0},
        {'name': '3', 'ordinate': 12.0},
        {'name': '4', 'ordinate': 18.0}
        ]
    }

def validate_foundation(foundation):
    with open(SCHEMA_PATH, 'r') as file:
        schema = json.load(file)
    errors = sorted(Draft7Validator(schema=schema).iter_errors(foundation), key=lambda e: e.path)
    for error in errors:
        print(error.message)
        print(error.path)
    assert len(errors) == 0

class Test_tonf_m():
    def test_extract_unit(self, tonf_m_parser):
        unit_conversion = tonf_m_parser._extract_unit_conversion()
        assert unit_conversion["length"] == 1
        assert unit_conversion["force"] == 1

    def test_extract_grid(self, tonf_m_parser):
        grid = tonf_m_parser._extract_grid()
        assert grid == grid_data

    def test_extract_flexural_shear_data(self, tonf_m_parser):
        tonf_m_parser._extract_flexural_shear_data()

    def test_extract_strip_geometry(self, tonf_m_parser):
        tonf_m_parser._extract_strip_geometry()

    def test_extract_concrete_material(self, tonf_m_parser):
        tonf_m_parser._extract_concrete_material()

    def test_extract_rebar_material(self, tonf_m_parser):
        tonf_m_parser._extract_rebar_material()

    def test_extract_strip_prop(self, tonf_m_parser):
        tonf_m_parser._extract_strip_prop()

    def test_extract_cover_preferences(self, tonf_m_parser):
        tonf_m_parser._extract_cover_preferences()

    def test_get_strip_prop(self, tonf_m_parser):
        tonf_m_parser._get_strip_prop()

    def test_extract_slab_properties(self, tonf_m_parser):
        tonf_m_parser._extract_slab_properties()

    def test_extract_slab_prop_assignment(self, tonf_m_parser):
        tonf_m_parser._extract_slab_prop_assignment()

    def test_extract_point_coordinates(self, tonf_m_parser):
        tonf_m_parser._extract_point_coordinates()

    def test_extract_point_load_geometry(self, tonf_m_parser):
        tonf_m_parser._extract_point_load_geometry()

    def test_extract_area_geometry(self, tonf_m_parser):
        tonf_m_parser._extract_area_geometry()

    def test_get_columns(self, tonf_m_parser):
        tonf_m_parser._get_columns()

    def test_get_grid(self, tonf_m_parser):
        tonf_m_parser._get_grid()

    def test_get_slab_prop(self, tonf_m_parser):
        tonf_m_parser._get_slab_prop()

    def test_area_prop(self, tonf_m_parser):
        tonf_m_parser._get_area_prop()

    def test_get_areas(self, tonf_m_parser):
        tonf_m_parser._get_areas()

    def test_get_strips(self, tonf_m_parser):
        strips = tonf_m_parser._get_strips()
        assert len(strips) == 3

    def test_get_foundation(self, tonf_m_parser):
        validate_foundation(tonf_m_parser.get_foundation())

    def test_single_materials(self, tonf_m_parser):
        assert len(tonf_m_parser.get_concrete_set()) == 1
        assert len(tonf_m_parser.get_steel_set()) == 1


class TestMdb():
    def test_same_as_accdb(self, tonf_m_mdb_parser, tonf_m_parser):
        foundation = tonf_m_mdb_parser.get_foundation()
        validate_foundation(foundation)
        assert [s['name'] for s in foundation['strips']] == [s['name'] for s in tonf_m_parser.get_foundation()['strips']]


class TestError():
    def test_multiple_fc_error(self, error_fc_parser):
        assert len(error_fc_parser.get_concrete_set()) > 1

    def test_multiple_fy_error(self, error_fy_parser):
        assert len(error_fy_parser.get_steel_set()) > 1

    def test_multiple_cover_error(self, error_fy_parser):
        covers = error_fy_parser.get_cover_set()
        assert len(covers['top']) == 1 and len(covers['bottom']) == 1


class TestMissingTable():
    def test_miss_program_control(self):
        parser = V16Parser(str(DATA_PATH.joinpath('missing_table', 'program_control.accdb')))
        try:
            with pytest.raises(TableMissingError) as tmerr:
                parser.get_foundation()
        finally:
            parser.close()
        assert tmerr.value.table_name == '[Program Control]'
        assert tmerr.value.message == 'Please select "MODEL DEFINITION" tables when exporting access file from CSI SAFE.'


class TestDriver():
    def test_missing_driver(self, monkeypatch):
        monkeypatch.setattr('core.parser.parse.has_access_driver', lambda: False)
        with pytest.raises(DriverMissingError) as err:
            V16Parser(str(DATA_PATH.joinpath('tonf_m.accdb')))
        assert err.value.url.startswith('https://www.microsoft.com/')
