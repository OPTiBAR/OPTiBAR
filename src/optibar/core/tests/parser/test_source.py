"""the parser reads SAFE's tables from any table source, not only from an Access file"""
import json
import pathlib
import pytest
from optibar.core.parser.parse import V16Parser, has_access_driver
from optibar.core.parser.source import MemorySource, AccessSource
from optibar.core.parser.errors import TableMissingError
from test_parse import validate_foundation, grid_data

DATA_PATH = pathlib.Path(__file__).parent.joinpath('data_files')
# the tables of tonf_m.accdb, so these tests run without the Access ODBC driver
TABLES_PATH = DATA_PATH.joinpath('tonf_m_tables.json')

requires_driver = pytest.mark.skipif(not has_access_driver(), reason='Microsoft Access ODBC driver is not installed')


@pytest.fixture
def tables():
    with open(TABLES_PATH, encoding='utf-8') as file:
        return json.load(file)


class TestMemorySource():
    def test_foundation(self, tables):
        parser = V16Parser(MemorySource(tables))
        foundation = parser.get_foundation()
        validate_foundation(foundation)
        assert len(foundation['strips']) == 3
        assert foundation['grid'] == grid_data

    def test_read_columns(self, tables):
        rows = MemorySource(tables).read('Grid Lines', ['GridID', 'Ordinate'])
        assert rows[0] == {'GridID': 'A', 'Ordinate': 0.0}

    def test_missing_table(self, tables):
        del tables['Program Control']
        with pytest.raises(TableMissingError) as err:
            V16Parser(MemorySource(tables)).get_foundation()
        assert err.value.table_name == 'Program Control'
        assert 'MODEL DEFINITION' in err.value.message

    def test_missing_column(self, tables):
        for row in tables['Concrete Slab Design 01 - Flexural And Shear Data']:
            del row['VArea']
        with pytest.raises(TableMissingError) as err:
            V16Parser(MemorySource(tables)).get_foundation()
        assert err.value.table_name == 'Concrete Slab Design 01 - Flexural And Shear Data'
        assert 'DESIGN RESULTS' in err.value.message


@requires_driver
class TestAccessSource():
    def test_same_as_memory(self, tables):
        """the JSON tables are the access file's, read through the driver"""
        with_path = V16Parser(str(DATA_PATH.joinpath('tonf_m.accdb')))
        with_source = V16Parser(AccessSource(str(DATA_PATH.joinpath('tonf_m.accdb'))))
        from_memory = V16Parser(MemorySource(tables))
        try:
            assert with_path.get_foundation() == with_source.get_foundation() == from_memory.get_foundation()
        finally:
            with_path.close()
            with_source.close()

    def test_missing_column(self):
        source = AccessSource(str(DATA_PATH.joinpath('tonf_m.accdb')))
        try:
            with pytest.raises(TableMissingError):
                source.read('Grid Lines', ['NoSuchColumn'])
        finally:
            source.close()

    def test_close_twice(self):
        parser = V16Parser(str(DATA_PATH.joinpath('tonf_m.accdb')))
        parser.close()
        parser.close()


class TestCoverOverwrite():
    def _overwrite(self, tables, **covers):
        """the first strip overwrites its covers; the others use the preferences"""
        row = tables['Slab Design Overwrites 01 - Strip Based'][0]
        row['CoverType'] = 'User'
        row.update(covers)
        return row['Strip']

    def test_top_and_bottom(self, tables):
        strip = self._overwrite(tables, CoverTop=0.075, CoverBot=0.06)
        prop = V16Parser(MemorySource(tables))._get_strip_prop()
        assert prop[strip]['covers'] == {'top': 0.075, 'bottom': 0.06}
        preferences = tables['Design Preferences 02 - Rebar Cover - Slabs'][0]
        others = [p['covers'] for name, p in prop.items() if name != strip]
        assert others and all(c == {'top': preferences['CoverTop'], 'bottom': preferences['CoverBot']} for c in others)

    def test_converts_units(self, tables):
        tables['Program Control'][0]['CurrUnits'] = 'Tonf, cm, C'
        strip = self._overwrite(tables, CoverTop=7.5, CoverBot=6.0)
        covers = V16Parser(MemorySource(tables))._get_strip_prop()[strip]['covers']
        assert covers == pytest.approx({'top': 0.075, 'bottom': 0.06})

    def test_cover_set(self, tables):
        self._overwrite(tables, CoverTop=0.075, CoverBot=0.06)
        covers = V16Parser(MemorySource(tables)).get_cover_set()
        assert len(covers['top']) == 2 and len(covers['bottom']) == 2

    def test_missing_cover_columns(self, tables):
        self._overwrite(tables)
        with pytest.raises(TableMissingError) as err:
            V16Parser(MemorySource(tables))._get_strip_prop()
        assert err.value.table_name == 'Slab Design Overwrites 01 - Strip Based'
