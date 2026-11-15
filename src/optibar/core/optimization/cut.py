"""cutting plans: how to cut the rebar pieces of each diameter from standard length bars with the least waste.

CuttingStock solves the cutting stock problem exactly with the arc-flow model (Valerio de Carvalho):

* The lengths are measured in grid cells, the coarsest unit that holds all the piece lengths and the
  stock length exactly (their greatest common divisor): pieces rounded to 10 cm give a 12 m bar 120
  cells, pieces rounded to 1 cm 1200.
* The nodes of a graph are positions along a bar, in cells. A piece from position p is an arc from p to
  p plus its length, and every position has an offcut arc to the end of the bar, so a bar is a path from
  0 to the end, its arcs the pieces it is cut into.
* The LP of the model is solved first. It is as strong as the Gilmore-Gomory column generation LP, and
  no plan has fewer bars than its optimum rounded up, which nearly always is the optimum.
* An integer flow of as few bars as possible, but at least that bound, with at least the pieces needed
  on the arcs, is solved by HiGHS (branch and cut). With the bound given, HiGHS does not have to prove
  it, and stops as soon as a plan reaches it.
* The flow is split into the paths of the bars, and the pieces cut beyond the demand are taken off
  again, so the plan cuts exactly the demand.

Only the paths with the pieces longest first are built, which every pattern has, so the graph stays
small. Solved to the end, the plan has the fewest bars possible, proven; stopped by the time limit, it
is the best plan found, not proven.
"""
from __future__ import annotations
import math
from collections import defaultdict
from typing import Dict, List, Tuple

import pyomo.environ as pyo
from pyomo.opt import TerminationCondition

from optibar.core.setting import STANDARD_LENGTH

SOLVER = 'appsi_highs'
TIME_LIMIT = 20 # seconds for the arc-flow model; stopped by it, the best plan found is used, not proven optimal
# pieces are labelled with their position in the piece lists of the drawing, e.g. A3 = third additional row
LABEL_PREFIX = {'typical': 'T', 'thermal': 'Th', 'additional': 'A', 'shear': 'S'}
WASTE_LABEL = 'w'

Pattern = Tuple[int, ...] # pieces of each length cut from one bar
Arc = Tuple[int, int, int] # (tail, head, length index or -1 for the offcut)


def integer_grid(lengths: List[float], stock_length: float) -> Tuple[List[int], int]:
    """the sizes of the pieces and of the bar as integers, on the coarsest grid that holds them all exactly.

    Lengths given to the centimetre (or millimetre, or 0.1 mm) are exact. Finer lengths are rounded up and
    the bar down, so every pattern found on the grid still fits in a real bar.
    """
    values = [*lengths, stock_length]
    for scale in (100, 1000, 10000):
        units = [round(v * scale) for v in values]
        if all(abs(v * scale - u) < 1e-6 * scale for v, u in zip(values, units)):
            break
    else:
        units = [math.ceil(v * scale - 1e-9) for v in lengths] + [math.floor(stock_length * scale + 1e-9)]
    unit = math.gcd(*units)
    return [u // unit for u in units[:-1]], units[-1] // unit


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
        self.numbers = list(numbers)
        self.stock_length = stock_length
        self.N = len(self.lengths)
        self.sizes, self.capacity = integer_grid(lengths, stock_length)
        self.lower_bound = 0.0 # no plan has fewer bars than this rounded up
        self.proven_optimal = True # whether no plan has fewer bars
        self.patterns: List[List[int]] = []
        self.pattern_numbers: List[int] = []
        if any(self.numbers):
            self._run()

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

    def _run(self) -> None:
        arcs = self._graph()
        flow, self.proven_optimal = self._solve(arcs)
        if flow is None:
            raise RuntimeError(f'the cutting stock model found no plan within {TIME_LIMIT} s')
        plan = self._split(arcs, flow)
        self._trim(plan)
        bars = [(list(pattern), n) for pattern, n in plan.items() if n and any(pattern)]
        self.patterns = [pattern for pattern, _ in bars]
        self.pattern_numbers = [n for _, n in bars]

    def _graph(self) -> List[Arc]:
        """the arcs of the arc-flow graph.

        Every pattern has a path with its pieces longest first, so only those paths are built: the arcs
        of a length start where a longer piece ends (or at 0), at most as many in a row as there are
        pieces of that length, and as fit. Every position reached has an offcut arc to the end.
        """
        arcs = set()
        reached = {0}
        for i in sorted((i for i in range(self.N) if self.numbers[i]), key=lambda i: -self.sizes[i]):
            size = self.sizes[i]
            front = set(reached)
            for _ in range(min(self.numbers[i], self.capacity // size)):
                front = {p for p in front if p + size <= self.capacity}
                arcs.update((p, p + size, i) for p in front)
                front = {p + size for p in front}
                reached |= front
        arcs.update((p, self.capacity, -1) for p in reached if p < self.capacity)
        return sorted(arcs)

    def _solve(self, arcs: List[Arc]) -> Tuple[List[int] | None, bool]:
        """the integer flow on the arcs: as few bars as possible (the flow out of 0), with at least the
        pieces needed on the arcs of each length, and as much flow into every position as out of it.

        The LP of the model is solved first: no plan has fewer bars than its optimum rounded up, and the
        integer model is given that bound, which spares HiGHS from proving it and lets it stop as soon as
        a plan reaches it.

        Returns:
            (the flow, or None if the time limit stopped the model before any plan; whether it is optimal)
        """
        A = range(len(arcs))
        out_arcs, in_arcs, piece_arcs = defaultdict(list), defaultdict(list), defaultdict(list)
        for a, (tail, head, i) in enumerate(arcs):
            out_arcs[tail].append(a)
            in_arcs[head].append(a)
            piece_arcs[i].append(a)
        inner = sorted(p for p in set(out_arcs) | set(in_arcs) if 0 < p < self.capacity)
        L = [i for i in range(self.N) if self.numbers[i]]
        model = pyo.ConcreteModel()
        model.flow = pyo.Var(A, within=pyo.NonNegativeReals)
        model.conservation = pyo.Constraint(inner, rule=lambda m, p:
            sum(m.flow[a] for a in in_arcs[p]) == sum(m.flow[a] for a in out_arcs[p]))
        model.pieces = pyo.Constraint(L, rule=lambda m, i: sum(m.flow[a] for a in piece_arcs[i]) >= self.numbers[i])
        model.bars = pyo.Expression(expr=sum(model.flow[a] for a in out_arcs[0]))
        model.obj = pyo.Objective(expr=model.bars)
        solver = pyo.SolverFactory(SOLVER)
        solver.options['time_limit'] = TIME_LIMIT
        if solver.solve(model).solver.termination_condition != TerminationCondition.optimal:
            raise RuntimeError('the LP of the cutting stock model was not solved')
        lp = pyo.value(model.obj)
        model.lower = pyo.Constraint(expr=model.bars >= math.ceil(lp - 1e-6))
        model.flow.domain = pyo.NonNegativeIntegers
        results = solver.solve(model, load_solutions=False)
        bound = results.problem.lower_bound
        self.lower_bound = max(lp, float(bound) if bound is not None and math.isfinite(bound) else 0.0)
        try:
            model.solutions.load_from(results)
        except Exception: # stopped before any plan
            return None, False
        flow = [round(pyo.value(model.flow[a])) for a in A]
        bars = sum(flow[a] for a in out_arcs[0])
        # optimal, or stopped just when the plan reached the bound
        proven = results.solver.termination_condition == TerminationCondition.optimal or bars <= math.ceil(self.lower_bound - 1e-6)
        return flow, proven

    def _split(self, arcs: List[Arc], flow: List[int]) -> Dict[Pattern, int]:
        """the bars of the flow: paths from 0 to the end of the bar, each as many times as the least flow
        on it; the pieces on a path are the pattern of its bars"""
        flow = list(flow)
        out_arcs = defaultdict(list)
        for a, (tail, _, _) in enumerate(arcs):
            out_arcs[tail].append(a)
        plan: Dict[Pattern, int] = defaultdict(int)
        while any(flow[a] for a in out_arcs[0]):
            p, path = 0, []
            while p != self.capacity:
                a = next(a for a in out_arcs[p] if flow[a] > 0)
                path.append(a)
                p = arcs[a][1]
            n = min(flow[a] for a in path)
            pattern = [0] * self.N
            for a in path:
                flow[a] -= n
                if arcs[a][2] >= 0:
                    pattern[arcs[a][2]] += 1
            plan[tuple(pattern)] += n
        return plan

    def _cut(self, plan: Dict[Pattern, int]) -> List[int]:
        """the pieces of each length that the bars of the plan cut"""
        return [sum(pattern[i] * n for pattern, n in plan.items()) for i in range(self.N)]

    def _waste(self, pattern: Pattern) -> int:
        """the offcut of a bar cut with the pattern, in grid cells"""
        return self.capacity - sum(s * a for s, a in zip(self.sizes, pattern))

    def _trim(self, plan: Dict[Pattern, int]) -> None:
        """takes the pieces cut beyond the demand off the bars of the plan, so it cuts exactly the demand.

        Each step takes the surplus that one bar can give up off as many bars of one pattern as the
        surplus allows. The pattern is chosen by, in order:
        1. a trim that empties the bar: the bar is not needed at all;
        2. a trim that gives a pattern already in the plan: no new pattern;
        3. the largest waste in the trimmed bar: the waste stays in few bars, as long offcuts.
        """
        surplus = [max(c - n, 0) for c, n in zip(self._cut(plan), self.numbers)]
        empty = tuple([0] * self.N)
        while any(surplus):
            best = None
            for pattern, n in plan.items():
                if n == 0:
                    continue
                trim = [min(surplus[j], pattern[j]) for j in range(self.N)]
                if not any(trim):
                    continue
                trimmed = tuple(a - t for a, t in zip(pattern, trim))
                key = (trimmed == empty, plan.get(trimmed, 0) > 0, self._waste(trimmed))
                if best is None or key > best[0]:
                    best = (key, pattern, trim, trimmed)
            _, pattern, trim, trimmed = best
            n = min(plan[pattern], *[surplus[j] // trim[j] for j in range(self.N) if trim[j]])
            plan[pattern] -= n
            plan[trimmed] += n
            surplus = [s - n * t for s, t in zip(surplus, trim)]
        for pattern in [p for p, n in plan.items() if n == 0 or p == empty]:
            del plan[pattern]


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
    piece being the waste (label "w") when there is any. "optimal" says whether no plan uses fewer
    bars, and "lower_bound" is the fewest bars any plan could use: the bars of the plan when optimal.
    """
    plans = []
    for diameter, by_length in sorted(_piece_demand(data['pieces']).items()):
        lengths = sorted(by_length, reverse=True)
        numbers = [by_length[length]['number'] for length in lengths]
        stock = CuttingStock(lengths, numbers, stock_length)
        result = stock.get_results()
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
            'optimal': stock.proven_optimal,
            'lower_bound': bars if stock.proven_optimal else math.ceil(stock.lower_bound - 1e-6),
            'patterns': patterns,
        })
    return plans


def optimality_text(plan: Dict) -> str:
    """'optimal', or the fewest bars any plan could use when the plan is not proven optimal;
    empty for plans saved before they carried it"""
    if 'optimal' not in plan:
        return ''
    return 'optimal' if plan['optimal'] else f"not proven optimal, at least {plan['lower_bound']} bars"


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
