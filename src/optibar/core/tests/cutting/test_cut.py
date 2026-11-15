import json
import math
import random
import pathlib
from collections import Counter, defaultdict
import pytest
from optibar.core.optimization.cut import CuttingStock, integer_grid, cutting_plans, pattern_text, _piece_demand, WASTE_LABEL
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


HARD = [ # pieces just above 1/2, 1/3, 1/4, 1/5 of the bar, where plans are hardest to get optimal
    (sorted({round(12 / r.choice([2, 3, 4, 5]) + r.randint(1, 8) / 100, 2) for _ in range(r.randint(2, 5))}, reverse=True), r)
    for r in (random.Random(seed) for seed in range(15))
]


class TestCuttingStock():
    @staticmethod
    def bare(lengths, numbers):
        """a CuttingStock for its helpers, without solving"""
        stock = CuttingStock.__new__(CuttingStock)
        stock.lengths, stock.numbers, stock.N = lengths, list(numbers), len(lengths)
        stock.sizes, stock.capacity = integer_grid(lengths, 12)
        return stock

    # --- the whole method -------------------------------------------------------------------------

    def test_exact_pieces(self):
        lengths = [2.5, 3.4, 8, 3.9, 4.3, 2.9, 7.2]
        numbers = [20, 40, 34, 25, 12, 30, 20]
        result = CuttingStock(lengths, numbers).get_results()
        assert cut_counts(result['patterns'], result['numbers'], len(lengths)) == numbers
        for pattern in result['patterns']:
            assert sum(l * c for l, c in zip(lengths, pattern)) <= 12 + 1e-9

    def test_optimal(self):
        """the arc-flow model solves it to the end: the fewest bars, proven"""
        lengths = [9.8, 8.8, 6.6, 5.1, 4.8, 4.4, 4.0, 3.6]
        numbers = [26, 39, 29, 54, 4, 2, 17, 3]
        stock = CuttingStock(lengths, numbers)
        assert stock.proven_optimal
        assert sum(stock.get_results()['numbers']) == 116 == math.ceil(stock.lower_bound - 1e-6)

    @pytest.mark.parametrize('seed', range(10))
    def test_optimal_random(self, seed):
        """random instances on 1, 10, 20 and 50 cm grids are cut exactly, with the bars of the lower bound"""
        rng = random.Random(seed)
        unit = rng.choice([0.01, 0.1, 0.2, 0.5])
        lengths = sorted({round(rng.randint(1, int(11.9 / unit)) * unit, 2) for _ in range(rng.randint(3, 10))}, reverse=True)
        numbers = [rng.randint(1, 60) for _ in lengths]
        stock = CuttingStock(lengths, numbers)
        result = stock.get_results()
        assert stock.proven_optimal
        assert cut_counts(result['patterns'], result['numbers'], len(lengths)) == numbers
        assert sum(result['numbers']) == math.ceil(stock.lower_bound - 1e-6)

    @pytest.mark.parametrize('lengths, rng', HARD)
    def test_optimal_hard(self, lengths, rng):
        numbers = [rng.randint(1, 9) for _ in lengths]
        stock = CuttingStock(lengths, numbers)
        result = stock.get_results()
        assert stock.proven_optimal
        assert cut_counts(result['patterns'], result['numbers'], len(lengths)) == numbers

    def test_better_than_heuristics(self):
        """an instance where the column generation heuristics needed 4 bars: the optimum is 3"""
        lengths, numbers = [6.08, 6.06, 3.05, 3.01, 2.48], [1, 1, 1, 2, 5]
        stock = CuttingStock(lengths, numbers)
        result = stock.get_results()
        assert sum(result['numbers']) == 3 and stock.proven_optimal
        assert cut_counts(result['patterns'], result['numbers'], len(lengths)) == numbers

    def test_stock_length(self):
        result = CuttingStock([3.0], [5], stock_length=6).get_results()
        assert result == {'patterns': [[2], [1]], 'numbers': [2, 1]}

    def test_exact_fit(self):
        """five 2.4 m pieces fill a 12 m bar exactly, which floating point sums put at 12.000000000000002"""
        result = CuttingStock([2.4], [10]).get_results()
        assert result == {'patterns': [[5]], 'numbers': [2]}

    def test_no_pieces(self):
        assert CuttingStock([2.0, 3.0], [0, 0]).get_results() == {'patterns': [], 'numbers': []}

    @pytest.mark.parametrize('lengths, numbers', [([13], [1]), ([0], [1]), ([2], [-1]), ([2, 3], [1])])
    def test_invalid_input(self, lengths, numbers):
        with pytest.raises(ValueError):
            CuttingStock(lengths, numbers)

    @pytest.mark.parametrize('lengths, stock, sizes, capacity', [
        ([2.5, 3.5], 12, [5, 7], 24),          # 50 cm grid
        ([3.4, 8.0], 12, [17, 40], 60),        # 20 cm grid
        ([3.0, 4.0], 12, [3, 4], 12),          # 1 m grid
        ([1.11, 1.4], 12, [111, 140], 1200),   # shear pieces, 1 cm grid
        ([0.3333], 1, [3333], 10000),          # 0.1 mm grid
        ([0.12345], 1, [247], 2000),           # finer: piece rounded up to 0.1235, then the 0.5 mm grid
    ])
    def test_integer_grid(self, lengths, stock, sizes, capacity):
        assert integer_grid(lengths, stock) == (sizes, capacity)

    # --- the arc-flow model -----------------------------------------------------------------------

    def test_graph(self):
        """pieces longest first: 5 m arcs from 0, 3 m arcs where a 5 m piece ends (one 3 m piece only),
        and an offcut arc from every position reached to the end of the bar"""
        stock = self.bare([5.0, 3.0], [2, 1])
        assert stock.sizes == [5, 3] and stock.capacity == 12
        assert stock._graph() == sorted([
            (0, 5, 0), (5, 10, 0),
            (0, 3, 1), (5, 8, 1), # not from 10: 10 + 3 passes the end
            (0, 12, -1), (3, 12, -1), (5, 12, -1), (8, 12, -1), (10, 12, -1),
        ])

    def test_split(self):
        """a flow of one bar along 0-5-10-12 and one along 0-3-12 is a 5 + 5 bar and a 3 bar"""
        stock = self.bare([5.0, 3.0], [2, 1])
        arcs = stock._graph()
        on = {(0, 5, 0), (5, 10, 0), (10, 12, -1), (0, 3, 1), (3, 12, -1)}
        assert dict(stock._split(arcs, [1 if arc in on else 0 for arc in arcs])) == {(2, 0): 1, (0, 1): 1}

    @pytest.mark.parametrize('lengths, numbers, optimum', [
        ([5.0, 4.0, 3.0], [2, 2, 2], 2),
        ([7.0, 3.0, 2.0], [4, 4, 1], 4),
        ([9.8, 8.8, 6.6, 5.1, 4.8, 4.4, 4.0, 3.6], [26, 39, 29, 54, 4, 2, 17, 3], 116),
    ])
    def test_solve(self, lengths, numbers, optimum):
        """the flow is optimal and proven, and splits into bars that fit and cut at least the demand"""
        stock = self.bare(lengths, numbers)
        arcs = stock._graph()
        flow, proven = stock._solve(arcs)
        plan = stock._split(arcs, flow)
        assert proven and sum(plan.values()) == optimum == math.ceil(stock.lower_bound - 1e-6)
        assert all(c >= n for c, n in zip(stock._cut(plan), numbers))
        assert all(stock._waste(pattern) >= 0 for pattern in plan)

    @pytest.mark.parametrize('plan, demand, expected', [
        # two 3 m too many: 3+3+3+2.5 gives both up and keeps a 6.5 m offcut, rather than 3+4+4 one
        ({(3, 1, 0): 1, (1, 0, 2): 1}, [2, 1, 2], {(1, 1, 0): 1, (1, 0, 2): 1}),
        # one 3 m too many: 3+2.5+4 becomes 2.5+4, already in the plan, rather than 3+3 a 3 m bar
        ({(2, 0, 0): 1, (1, 1, 1): 1, (0, 1, 1): 1}, [2, 2, 2], {(2, 0, 0): 1, (0, 1, 1): 2}),
        # a bar of surplus pieces only is dropped
        ({(1, 0, 0): 1, (1, 0, 2): 1}, [1, 0, 2], {(1, 0, 2): 1}),
        # no surplus: nothing changes
        ({(1, 0, 2): 3}, [3, 0, 6], {(1, 0, 2): 3}),
    ])
    def test_trim(self, plan, demand, expected):
        stock = self.bare([3.0, 2.5, 4.0], demand)
        plan = defaultdict(int, plan)
        stock._trim(plan)
        assert dict(plan) == expected

    # --- stopped by the time limit ----------------------------------------------------------------

    def test_time_limit_with_a_plan(self, monkeypatch):
        """stopped before the proof: the best plan found is used, cut exactly, and not proven optimal"""
        solve = CuttingStock._solve
        monkeypatch.setattr(CuttingStock, '_solve', lambda self, arcs: (solve(self, arcs)[0], False))
        lengths, numbers = [9.8, 8.8, 6.6, 5.1, 4.8, 4.4, 4.0, 3.6], [26, 39, 29, 54, 4, 2, 17, 3]
        stock = CuttingStock(lengths, numbers)
        result = stock.get_results()
        assert not stock.proven_optimal
        assert cut_counts(result['patterns'], result['numbers'], len(lengths)) == numbers

    def test_time_limit_without_a_plan(self, monkeypatch):
        """stopped before any plan: an error, rather than a plan that doesn't exist"""
        monkeypatch.setattr(CuttingStock, '_solve', lambda self, arcs: (None, False))
        with pytest.raises(RuntimeError, match='no plan'):
            CuttingStock([5.0, 4.0], [2, 3])


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

    def test_plans_are_optimal(self, data):
        """every plan of the foundation is proven optimal: its lower bound is its bars"""
        for plan in data['cut']:
            assert plan['optimal'] is True
            assert plan['lower_bound'] == plan['bars']

    def test_unproven_plan_carries_its_lower_bound(self, data, monkeypatch):
        """stopped by the time limit, a plan is not optimal and gives the fewest bars any plan could use"""
        solve = CuttingStock._solve
        def stopped(self, arcs):
            flow, _ = solve(self, arcs)
            self.lower_bound -= 1 # as if the bound were not closed yet
            return flow, False
        monkeypatch.setattr(CuttingStock, '_solve', stopped)
        for plan in cutting_plans(data):
            assert plan['optimal'] is False
            assert plan['lower_bound'] == plan['bars'] - 1

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
