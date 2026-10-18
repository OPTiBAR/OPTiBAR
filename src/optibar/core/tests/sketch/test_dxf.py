import copy
import json
import pathlib
import ezdxf
import pytest
from optibar.core.run import run_calculation
from optibar.core.sketch.dxf import DxfDrawing, LAYERS, PLAN_TITLES, StripLine

DATA_PATH = pathlib.Path(__file__).parent.parent.joinpath('data_files', 'parsed_data.json')
CONFIG = {
    "diameter": {"additional": 25, "shear": 14, "thermal": 12, "typical": 18},
    "elimination": {"additional": 0.2, "shear": 2.0},
    "type_number": {"shear": 4, "stack": 2, "total": 20},
    "side_cover": 0.05,
    "typical_arrangement": {"method": "INTERVAL", "value": 0.2, "exceptions": []},
}


@pytest.fixture(scope='module')
def output():
    with open(DATA_PATH) as f:
        parsed_data = json.load(f)
    return run_calculation(parsed_data, CONFIG)['data']


@pytest.fixture(scope='module')
def doc(output, tmp_path_factory):
    path = tmp_path_factory.mktemp('dxf').joinpath('drawing.dxf')
    DxfDrawing(output).save(path)
    return ezdxf.readfile(path)


def texts(doc):
    msp = doc.modelspace()
    return [e.dxf.text for e in msp.query('TEXT')] + [e.text for e in msp.query('MTEXT')]


def drawn_bars(output, level, kind):
    """bars the drawing should contain: non empty bunches that start on their strip"""
    count = 0
    for strip in output['strips']:
        line = StripLine(strip['geometry']['mid_line'])
        mesh = strip['mesh'][kind][level]
        bunches = mesh if kind == 'typical' else [b for row in mesh for piece in row for b in piece]
        count += sum(1 for b in bunches if b['number'] != 0 and b['stations'][0] + b['bends'][0] < line.length)
    return count


class TestDxf():
    def test_valid(self, doc):
        auditor = doc.audit()
        assert auditor.errors == []
        assert doc.header['$INSUNITS'] == 6 # meters

    def test_layers(self, doc):
        for name in LAYERS:
            assert name in doc.layers

    def test_titles_and_strip_names(self, doc, output):
        content = texts(doc)
        for title in PLAN_TITLES.values():
            assert title in content
        for strip in output['strips']:
            assert strip['name'] in content

    def test_bars(self, doc, output):
        msp = doc.modelspace()
        for level in ('top', 'bottom'):
            typical = len(msp.query(f'LWPOLYLINE[layer=="Typical Rebar {level.capitalize()}"]'))
            assert typical == drawn_bars(output, level, 'typical')
        additional = sum(len(msp.query(f'LWPOLYLINE[layer=="{layer}"]')) for layer in ('Additional Rebar Top', 'Additional Rebar Bottom', 'continuous Rebar'))
        assert additional == drawn_bars(output, 'top', 'additional') + drawn_bars(output, 'bottom', 'additional')
        labels = len(msp.query('TEXT[layer=="Rebar Text"]'))
        assert labels == sum(drawn_bars(output, level, kind) for level in ('top', 'bottom') for kind in ('typical', 'additional'))

    def test_dimensions(self, doc, output):
        grid = output['grid']
        grid_dims = len(PLAN_TITLES) * (len(grid['X']) - 1 + len(grid['Y']) - 1)
        width_dims = sum(len(s['geometry']['mid_line']) - 1 for s in output['strips'])
        section_dims = 2 * len(output['shear_types'])
        assert len(doc.modelspace().query('DIMENSION')) == grid_dims + width_dims + section_dims

    def test_summary_values(self, doc, output):
        rebar = output['summary']['rebar']
        total = rebar['typical']['top'] + rebar['typical']['bottom']
        assert str(round(1000 * total)) in texts(doc)

    def test_cutting_sheets(self, doc, output):
        """a sheet per 15 patterns of each diameter, titled with the diameter"""
        sheets = sum(-(-len(plan['patterns']) // 15) for plan in output['cut'])
        assert output['cut']
        headers = [t for t in texts(doc) if t == 'Cutting Pattern']
        assert len(headers) == sheets
        for plan in output['cut']:
            assert any(t.startswith(f"Cutting Plan %%C{plan['diameter']}") for t in texts(doc))

    def test_bars_beyond_the_strip(self, output, tmp_path):
        """the plugin crashed when a bar or shear zone ran past the end of its strip"""
        broken = copy.deepcopy(output)
        strip = broken['strips'][0]
        length = StripLine(strip['geometry']['mid_line']).length
        strip['mesh']['typical']['top'][0]['stations'] = [length + 1, length + 5]
        strip['mesh']['typical']['bottom'][0]['stations'] = [length - 1, length + 2]
        strip['shear_zones'].append({'id': 1, 'period': [length - 0.5, length + 3]})
        path = tmp_path.joinpath('broken.dxf')
        DxfDrawing(broken).save(path)
        assert ezdxf.readfile(path).audit().errors == []
