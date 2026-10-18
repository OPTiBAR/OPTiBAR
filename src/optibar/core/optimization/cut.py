"""cutting plans: how to cut the rebar pieces of each diameter from standard length bars with the least waste.

CuttingStock solves the cutting stock problem by column generation (Gilmore-Gomory): an LP over the
known cutting patterns gives dual prices, a knapsack finds the pattern worth adding, and once no pattern
improves the LP an integer program picks how many bars to cut with each pattern. Bars that would yield
more pieces than needed are then trimmed, the surplus becoming waste.
"""
from __future__ import annotations
import math
from collections import defaultdict
from copy import deepcopy
from typing import Dict, List

import pyomo.environ as pyo
from pyomo.opt import TerminationCondition

from optibar.core.setting import STANDARD_LENGTH

SOLVER = 'appsi_highs'
# pieces are labelled with their position in the piece lists of the drawing, e.g. A3 = third additional row
LABEL_PREFIX = {'typical': 'T', 'thermal': 'Th', 'additional': 'A', 'shear': 'S'}
WASTE_LABEL = 'w'


class CuttingStock():
    def __init__(self, lengths: List[float], numbers: List[int], stock_length: float = STANDARD_LENGTH) -> None:
        if not len(lengths) == len(numbers):
            raise ValueError("the length of the lengths and numbers arrays should be equal.")
        if any(l > stock_length for l in lengths):
            raise ValueError(f"all the lengths have to be at most {stock_length} meters")
        if any(l <= 0 for l in lengths):
            raise ValueError("all the lengths have to be positive")
        if any(n < 0 for n in numbers):
            raise ValueError("all the numbers have to be non-negative")

        self.lengths = lengths
        self.numbers = numbers
        self.stock_length = stock_length
        self.N = len(self.lengths)
        self.solver = pyo.SolverFactory(SOLVER)
        self._initialize_patterns()
        self._run()

    def _remove_excess(self):
        """the integer solution can cut more pieces than needed; trim them from the patterns,
        preferring the trims that leave the most waste in one bar (so other bars stay full)"""
        patterns = self.patterns
        pattern_numbers = self.pattern_numbers
        cut_pieces = [0] * self.N
        for i,pattern in enumerate(patterns):
            for j in range(self.N):
                cut_pieces[j] += pattern_numbers[i] * pattern[j]
        excessive_pieces = [cut_pieces[i] - self.numbers[i] for i in range(self.N)]

        while any(n > 0 for n in excessive_pieces):
            max_waste = float('-inf')
            max_pattern_index = None
            max_pattern_reductions = None
            for i,pattern in enumerate(patterns):
                if pattern_numbers[i] == 0:
                    continue
                waste = self.stock_length - sum([self.lengths[j] * pattern[j] for j in range(self.N)])
                pattern_reductions = deepcopy(pattern)
                for j in range(self.N):
                    reduction = min(max(excessive_pieces[j], 0), pattern[j])
                    waste += self.lengths[j] * reduction
                    pattern_reductions[j] = reduction
                if waste > max_waste and any(r > 0 for r in pattern_reductions):
                    max_pattern_reductions = pattern_reductions
                    max_pattern_index = i
                    max_waste = waste
            if max_pattern_index is None:
                break
            n = min(
                pattern_numbers[max_pattern_index],
                *[excessive_pieces[i]//max_pattern_reductions[i] for i in range(self.N) if max_pattern_reductions[i] > 0]
            )
            n = max(n, 1)
            pattern_numbers[max_pattern_index] -= n
            for i in range(self.N):
                excessive_pieces[i] -= n * max_pattern_reductions[i]
            new_pattern = [patterns[max_pattern_index][i] - max_pattern_reductions[i] for i in range(self.N)]
            patterns.append(new_pattern)
            pattern_numbers.append(n)

    def get_results(self) -> Dict[str, List]:
        patterns = []
        pnumbers = []
        for i in range(len(self.patterns)):
            if self.pattern_numbers[i] != 0 and any(self.patterns[i]):
                patterns.append(self.patterns[i])
                pnumbers.append(self.pattern_numbers[i])
        return {
            'patterns': patterns,
            'numbers': pnumbers,
        }

    def _initialize_patterns(self) -> None:
        """one pattern per length, as many of that length as fit in a bar"""
        patterns = []
        for i in range(self.N):
            pattern = [0] * self.N
            pattern[i] = math.floor(self.stock_length / self.lengths[i] + 1e-9)
            patterns.append(pattern)
        self.patterns = patterns

    def _main_model(self, domain) -> Dict:
        P = range(len(self.patterns))
        L = range(self.N)

        model = pyo.ConcreteModel()
        model.x = pyo.Var(P, within=domain)
        def pieces_rule(model,l):
            return sum(model.x[p]*self.patterns[p][l] for p in P) >= self.numbers[l]
        model.pieces_rule = pyo.Constraint(L, rule=pieces_rule)
        model.obj = pyo.Objective(expr=sum(model.x[p] for p in P))
        if domain == pyo.NonNegativeReals: # duals only exist for the LP; asking HiGHS for them on the integer model fails
            model.dual = pyo.Suffix(direction= pyo.Suffix.IMPORT)
        results = self.solver.solve(model)
        if results.solver.termination_condition != TerminationCondition.optimal:
            raise RuntimeError(f'the cutting stock model was not solved: {results.solver.termination_condition}')

        output = {
            'values': [pyo.value(model.x[p]) for p in P],
            'obj': pyo.value(model.obj),
        }
        if domain == pyo.NonNegativeReals:
            output['duals'] = [model.dual[model.pieces_rule[c]] for c in model.pieces_rule]
        return output

    def _knapsack_model(self, duals) -> Dict:
        """the pattern with the highest total dual price that fits in a bar"""
        L = range(self.N)
        model = pyo.ConcreteModel()
        model.x = pyo.Var(L, within=pyo.NonNegativeIntegers)
        def capacity_rule(model):
            return sum(model.x[l]*self.lengths[l] for l in L) <= self.stock_length
        model.capacity_rule = pyo.Constraint(rule=capacity_rule)
        model.obj = pyo.Objective(expr=sum(model.x[l]*duals[l] for l in L),sense=pyo.maximize)
        self.solver.solve(model)
        return {
            "obj":pyo.value(model.obj) ,
            "pattern": [round(pyo.value(model.x[l])) for l in L],
        }

    def _run(self):
        while True:
            results = self._main_model(domain=pyo.NonNegativeReals)
            knapsack = self._knapsack_model(results["duals"])
            # a pattern is worth adding when its dual value is above the cost of one bar
            if knapsack["obj"] > 1 + 1e-2 and knapsack["pattern"] not in self.patterns:
                self.patterns.append(knapsack["pattern"])
            else:
                values = self._main_model(domain=pyo.NonNegativeIntegers)["values"]
                self.pattern_numbers = [round(x) for x in values]
                break
        self._remove_excess()


def _piece_demand(pieces: Dict[str, List[Dict]]) -> Dict[float, Dict[float, Dict]]:
    """the cut lengths needed per diameter: {diameter: {length: {'number': n, 'labels': [...]}}}.
    Labels follow the rows of the piece lists in the drawings (one row per piece and bend shape)."""
    demand = defaultdict(lambda: defaultdict(lambda: {'number': 0, 'labels': []}))
    for rebar_type in ('typical', 'thermal', 'additional'):
        row = 0
        for piece in pieces.get(rebar_type, []):
            for shape in ('no_side', 'one_side', 'two_side'):
                count = piece['bend'][shape]
                if count:
                    row += 1
                    entry = demand[piece['diameter']][piece['length']]
                    entry['number'] += count
                    entry['labels'].append(f"{LABEL_PREFIX[rebar_type]}{row}")
    for row, piece in enumerate(pieces.get('shear', []), start=1):
        entry = demand[piece['diameter']][piece['length']]
        entry['number'] += piece['number']
        entry['labels'].append(f"{LABEL_PREFIX['shear']}{row}")
    return demand


def cutting_plans(data: Dict, stock_length: float = STANDARD_LENGTH) -> List[Dict]:
    """the cutting plan of every diameter for the "data" part of the engine output.

    Each plan lists its patterns, most used first. A pattern is a bar cut into pieces, the last
    piece being the waste (label "w") when there is any.
    """
    plans = []
    for diameter, by_length in sorted(_piece_demand(data['pieces']).items()):
        lengths = sorted(by_length, reverse=True)
        numbers = [by_length[length]['number'] for length in lengths]
        result = CuttingStock(lengths, numbers, stock_length).get_results()
        patterns = []
        for pattern, number in zip(result['patterns'], result['numbers']):
            pieces = []
            for length, count in zip(lengths, pattern):
                pieces += [{'label': by_length[length]['labels'], 'length': length}] * count
            waste = round(stock_length - sum(piece['length'] for piece in pieces), 2)
            if waste > 0:
                pieces.append({'label': [WASTE_LABEL], 'length': waste})
            patterns.append({'number': number, 'pieces': pieces, 'waste': max(waste, 0)})
        patterns.sort(key=lambda p: (-p['number'], p['waste']))
        bars = sum(p['number'] for p in patterns)
        waste = round(sum(p['number'] * p['waste'] for p in patterns), 2)
        plans.append({
            'diameter': diameter,
            'stock_length': stock_length,
            'bars': bars,
            'waste': waste,
            'waste_ratio': round(waste / (bars * stock_length), 4) if bars else 0,
            'patterns': patterns,
        })
    return plans


def pattern_text(pattern: Dict) -> str:
    """pieces of one bar, identical neighbours grouped: 3 x 1.4 (S2) + 7 x 1.11 (S1)"""
    groups = []
    for piece in pattern['pieces']:
        if piece['label'] == [WASTE_LABEL]:
            continue
        key = (piece['length'], '/'.join(piece['label']))
        if groups and groups[-1][0] == key:
            groups[-1][1] += 1
        else:
            groups.append([key, 1])
    return ' + '.join(f"{count} x {length:g} ({labels})" if count > 1 else f"{length:g} ({labels})" for (length, labels), count in groups)
