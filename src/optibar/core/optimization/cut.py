import pyomo.environ as pyo
from typing import Dict, List, Union
# from pyomo.opt import SolverStatus, TerminationCondition
import math
from pprint import pprint
from copy import deepcopy

class CuttingStock():
    def __init__(self, lengths:List[float], numbers:List[int]) -> None:
        if not len(lengths) == len(numbers):
            raise ValueError("the length of the lengths and numbers arrays should be equal.")
        # zero length inputs
        if any(l > 12 for l in lengths):
            raise ValueError("all the lengths have to be shorter than 12 meteres")
        if any(n < 0 for n in numbers):
            raise ValueError("all the numbers have to be non-negative")
        
        self.lengths = lengths
        self.numbers = numbers
        self.N = len(self.lengths)

        solvername='glpk'
        self.solver = pyo.SolverFactory(solvername)
        self._initialize_patterns()
        self._run()
    
    def _remove_excess(self):
        patterns = self.patterns
        pattern_numbers = self.pattern_numbers
        # enumerate cut pieces
        cut_pieces = [0] * self.N
        for i,pattern in enumerate(patterns):
            for j in range(self.N):
                cut_pieces[j] += pattern_numbers[i] * pattern[j]
        # initialize excessive pieces
        excessive_pieces = [0] * self.N
        for i in range(self.N):
            excessive_pieces[i] = cut_pieces[i] - self.numbers[i] 

        while any(n > 0 for n in excessive_pieces):
            max_waste = float('-inf')
            max_pattern_index = None
            max_pattern_reductions = None
            # building new pattern
            for i,pattern in enumerate(patterns):
                if pattern_numbers[i] == 0:
                    continue
                waste = 12 - sum([self.lengths[j] * pattern[j] for j in range(self.N)])
                pattern_reductions = deepcopy(pattern)
                for j in range(self.N):
                    reduction = min(excessive_pieces[j], pattern[j])
                    waste += self.lengths[j] * reduction
                    pattern_reductions[j] = reduction
                if waste > max_waste and any(r > 0 for r in pattern_reductions):
                    max_pattern_reductions = pattern_reductions
                    max_pattern_index = i
                    max_waste = waste
            # make changes to the patterns
            n = min(
                pattern_numbers[max_pattern_index],
                *[excessive_pieces[i]//max_pattern_reductions[i] for i in range(self.N) if max_pattern_reductions[i] > 0]
            )
            pattern_numbers[max_pattern_index] -= n
            for i in range(self.N):
                excessive_pieces[i] -= n * max_pattern_reductions[i]
            new_pattern = [patterns[max_pattern_index][i] - max_pattern_reductions[i] for i in range(self.N)]
            patterns.append(new_pattern)
            pattern_numbers.append(n)


    def get_results(self):
        patterns = []
        pnumbers = []
        for i in range(len(self.patterns)):
            if self.pattern_numbers[i] != 0:
                patterns.append(self.patterns[i])
                pnumbers.append(self.pattern_numbers[i])
        return {
            'patterns': patterns,
            'numbers': pnumbers,
        }
    
    def _initialize_patterns(self)->None:
        patterns = []
        for i,l in enumerate(self.lengths):
            pattern = [0] * len(self.lengths)
            pattern[i] = math.floor(12/self.lengths[i])
            patterns.append(pattern)
        self.patterns = patterns


    def _main_model(self, domain, initial_values=None) -> Dict[str,Union[List,float]]:
        P = range(len(self.patterns))
        L = range(len(self.lengths))

        model = pyo.ConcreteModel()
        
        if initial_values is not None:
            model.x = pyo.Var(P, within=domain , initialize=initial_values)
        else:
            model.x = pyo.Var(P, within=domain)

        def pieces_rule(model,l):
            return sum(model.x[p]*self.patterns[p][l] for p in P) >= self.numbers[l]
        model.pieces_rule = pyo.Constraint(L, rule=pieces_rule)

        model.obj = pyo.Objective(expr=sum(model.x[p] for p in P))

        model.dual = pyo.Suffix(direction= pyo.Suffix.IMPORT)
        self.solver.solve(model)
        
        output = {
            'values': [pyo.value(model.x[p]) for p in P],
            'obj': pyo.value(model.obj),
        }
        
        if domain == pyo.NonNegativeReals:
            output['duals'] = [model.dual[model.pieces_rule[c]] for c in model.pieces_rule]
        
        return output



    def _knapsack_model(self, duals):
        L = range(len(self.lengths))
        model = pyo.ConcreteModel()
        model.x = pyo.Var(L, within=pyo.NonNegativeIntegers)
        def capacity_rule(model):
            return sum(model.x[l]*self.lengths[l] for l in L) <= 12
        model.capacity_rule = pyo.Constraint(rule=capacity_rule)
        model.obj = pyo.Objective(expr=sum(model.x[l]*duals[l] for l in L),sense=pyo.maximize)
        self.solver.solve(model)
        return {
            "obj":pyo.value(model.obj) ,
            "pattern": [int(pyo.value(model.x[l])) for l in L],
        }

    def _run(self):
        values = [0]*len(self.patterns)
        while True:
            results = self._main_model(domain=pyo.NonNegativeReals, initial_values=values)
            duals = results["duals"]
            values = results["values"]
            knapsack = self._knapsack_model(duals)
            if 1 - knapsack["obj"] < -1e-2:
                self.patterns.append(knapsack["pattern"])
                values.append(0)
            else:
                self.pattern_numbers = [int(x) for x in self._main_model(domain=pyo.NonNegativeIntegers)["values"]]
                break
        self._remove_excess()

if __name__ == '__main__':
    # numbers = [4,6,1,10]
    # lengths = [8.5,2,5,4.5]
    numbers = [20,40,34,25,12,30,20]
    lengths = [2.5,3.4,8,3.9,4.3,2.9,7.2]
    cs = CuttingStock(lengths, numbers)
    results = cs.get_results()
    N = len(lengths)
    narray = [0] * N
    for i,pattern in enumerate(results['patterns']):
        for j in range(N):
            narray[j] += pattern[j] * results['numbers'][i]
    print(narray)
    print(sum(results['numbers']))
    pprint(results)