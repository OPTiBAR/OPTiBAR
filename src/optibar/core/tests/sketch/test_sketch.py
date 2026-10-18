import copy
import json
import pathlib
import pytest
from pypdf import PdfReader
from optibar.core.run import run_calculation
from optibar.core.sketch.sketch import Sketch

DATA_PATH = pathlib.Path(__file__).parent.parent.joinpath('data_files', 'parsed_data.json')
CONFIG = {
    "diameter": {"additional": 25, "shear": 14, "thermal": 12, "typical": 18},
    "elimination": {"additional": 0.2, "shear": 2.0},
    "type_number": {"shear": 4, "stack": 2, "total": 20},
    "side_cover": 0.05,
    "typical_arrangement": {"method": "INTERVAL", "value": 0.2, "exceptions": []},
}


def count_pages(path: pathlib.Path) -> int:
    return len(PdfReader(path).pages)


@pytest.fixture(scope='module')
def output():
    with open(DATA_PATH) as f:
        parsed_data = json.load(f)
    return run_calculation(parsed_data, CONFIG)['data']


class TestSketch():
    def test_draw(self, output, tmp_path):
        path = tmp_path.joinpath('drawing.pdf')
        Sketch(output).save(path)
        assert path.read_bytes().startswith(b'%PDF')
        tables = 5 + sum(1 for rebar_type in ('additional', 'typical', 'thermal') if output['pieces'][rebar_type])
        if not output['pieces']['shear']:
            tables -= 1
        if not output['shear_types']:
            tables -= 1
        tables += len(output['cut']) # a cutting plan page per diameter
        assert count_pages(path) == len(output['strips']) + tables

    def test_long_table_continues_on_next_page(self, output, tmp_path):
        long_output = copy.deepcopy(output)
        long_output['pieces']['typical'] = long_output['pieces']['typical'] * 20
        short_path, long_path = tmp_path.joinpath('short.pdf'), tmp_path.joinpath('long.pdf')
        Sketch(output).save(short_path)
        Sketch(long_output).save(long_path)
        assert count_pages(long_path) > count_pages(short_path)
