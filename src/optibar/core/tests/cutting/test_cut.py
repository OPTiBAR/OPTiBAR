import json
import math
import pathlib
from collections import Counter
import pyomo.environ as pyo
import pytest
from optibar.core.optimization.cut import CuttingStock, cutting_plans, pattern_text, _piece_demand, WASTE_LABEL
from optibar.core.run import run_calculation, run_analysis

DATA_PATH = pathlib.Path(__file__).parent.parent.joinpath('data_files', 'parsed_data.json')
CONFIG = {
    "diameter": {"additional": 25, "shear": 14, "thermal": 12, "typical": 18},
    "elimination": {"additional": 0.2, "shear": 2.0},
    "type_number": {"shear": 4, "stack": 2, "total": 20},
    "side_cover": 0.05,
    "typical_arrangement": {"method": "INTERVAL", "value": 0.2, "exceptions": []},
}


@pytest.fixture(scope='module')
def parsed_data():
    with open(DATA_PATH) as f:
        return json.load(f)


@pytest.fixture(scope='module')
def data(parsed_data):
    return run_calculation(parsed_data, CONFIG)['data']


def cut_counts(patterns, numbers, n):
    return [sum(p[j] * k for p, k in zip(patterns, numbers)) for j in range(n)]


class TestCuttingStock():
    def test_exact_pieces(self):
        lengths = [2.5, 3.4, 8, 3.9, 4.3, 2.9, 7.2]
        numbers = [20, 40, 34, 25, 12, 30, 20]
        result = CuttingStock(lengths, numbers).get_results()
        assert cut_counts(result['patterns'], result['numbers'], len(lengths)) == numbers
        for pattern in result['patterns']:
            assert sum(l * c for l, c in zip(lengths, pattern)) <= 12 + 1e-9

    def test_optimal(self):
        """the integer plan uses as many bars as the LP bound rounded up"""
        lengths = [9.8, 8.8, 6.6, 5.1, 4.8, 4.4, 4.0, 3.6]
        numbers = [26, 39, 29, 54, 4, 2, 17, 3]
        stock = CuttingStock(lengths, numbers)
        lower_bound = stock._main_model(pyo.NonNegativeReals)['obj']
        assert sum(stock.get_results()['numbers']) == math.ceil(lower_bound - 1e-6)

    def test_stock_length(self):
        result = CuttingStock([3.0], [5], stock_length=6).get_results()
        assert result == {'patterns': [[2], [1]], 'numbers': [2, 1]}

    @pytest.mark.parametrize('lengths, numbers', [([13], [1]), ([0], [1]), ([2], [-1]), ([2, 3], [1])])
    def test_invalid_input(self, lengths, numbers):
        with pytest.raises(ValueError):
            CuttingStock(lengths, numbers)


class TestCuttingPlans():
    def test_plans_cover_the_pieces(self, data):
        demand = _piece_demand(data['pieces'])
        assert [plan['diameter'] for plan in data['cut']] == sorted(demand)
        for plan in data['cut']:
            cut = Counter()
            for pattern in plan['patterns']:
                assert sum(p['length'] for p in pattern['pieces']) == pytest.approx(plan['stock_length'])
                for piece in pattern['pieces']:
                    if piece['label'] != [WASTE_LABEL]:
                        cut[piece['length']] += pattern['number']
            assert dict(cut) == {length: entry['number'] for length, entry in demand[plan['diameter']].items()}
            assert plan['bars'] == sum(p['number'] for p in plan['patterns'])
            assert plan['waste'] == pytest.approx(sum(p['number'] * p['waste'] for p in plan['patterns']), abs=0.01)

    def test_labels_follow_the_piece_list_rows(self, data):
        """each label is a row of the piece lists: one row per piece and bend shape"""
        rows = {}
        for rebar_type, prefix in (('typical', 'T'), ('thermal', 'Th'), ('additional', 'A')):
            row = 0
            for piece in data['pieces'][rebar_type]:
                for shape in ('no_side', 'one_side', 'two_side'):
                    if piece['bend'][shape]:
                        row += 1
                        rows[f'{prefix}{row}'] = (piece['diameter'], piece['length'])
        for row, piece in enumerate(data['pieces']['shear'], start=1):
            rows[f'S{row}'] = (piece['diameter'], piece['length'])
        for plan in data['cut']:
            for pattern in plan['patterns']:
                for piece in pattern['pieces']:
                    for label in piece['label']:
                        if label != WASTE_LABEL:
                            assert rows[label] == (plan['diameter'], piece['length'])

    def test_pattern_text(self):
        pattern = {'pieces': [{'label': ['S2'], 'length': 1.4}] * 3 + [{'label': ['S1'], 'length': 1.11}] * 7 + [{'label': ['w'], 'length': 0.03}]}
        assert pattern_text(pattern) == '3 x 1.4 (S2) + 7 x 1.11 (S1)'

    def test_analysis_skips_cutting(self, parsed_data):
        config = dict(CONFIG, type_number={'total': {'from': 20, 'to': 20}, 'stack': {'from': 2, 'to': 2}, 'shear': 4})
        [result] = run_analysis(parsed_data, config)
        assert result['cut'] == []
