from __future__ import annotations
from typing import List
from optibar.core.components.collections import Stack
from pyomo.environ import *
from pyomo.opt import SolverStatus, TerminationCondition

class Minimization():
    def __init__(self, selected_length: list[float], lengths: list[float], upper_bounds: list[float], num_pieces: list[int]):
        self.lengths = lengths
        self.upper_bounds = upper_bounds
        self.num_pieces = num_pieces
        self.selected_lengths = selected_length

    def run(self, p:int):
        I = range(len(self.lengths))
        J = range(len(self.selected_lengths))
        M = sorted(list(set(self.num_pieces)))
        self.I = I
        self.J = J
        self.M = M

        LS = self.lengths
        LO = self.selected_lengths
        LU = self.upper_bounds
        NSUB = {}

        for m in M:
            sublist = []
            for i,num in enumerate(self.num_pieces):
                if num == m:
                    sublist.append(i)
            NSUB[m] = sublist
        # print(M)
        # print(NSUB)

        C = [[0 for j in J] for i in I]
        for i in I:
            for j in J:
                if LS[i] <= LO[j] + 1e-6:
                    C[i][j] = max(0, LO[j]-LS[i])
                else:
                    C[i][j] = 0


        model = ConcreteModel(name='Type Minimizer')
        self.model = model

        model.x = Var(I, J, within=Binary)
        model.z = Var(M,J, within=Binary)


        def service_rule(model,i):
            return sum(model.x[i,j] for j in J) == 1
        model.service = Constraint(I, rule=service_rule)

        def not_shorter_rule(model,i,j):
            if LS[i] > LO[j] + 1e-6:
                return model.x[i,j] == 0
            else:
                return Constraint.Skip
        model.not_shorter = Constraint(I, J, rule=not_shorter_rule)

        # a piece can't be longer than its upper bound (e.g. the foundation length)
        def not_longer_rule(model,i,j):
            if LO[j] > LU[i] + 1e-6:
                return model.x[i,j] == 0
            else:
                return Constraint.Skip
        model.not_longer = Constraint(I, J, rule=not_longer_rule)

        def subset_lower_rule(model,i,j,m):
            if i in NSUB[m]:
                return model.z[m,j] >= model.x[i,j]
            else:
                return Constraint.Skip
        model.subset_lower = Constraint(I, J, M, rule=subset_lower_rule)

        def subset_number_rule(model):
            return sum(model.z[m,j] for j in J for m in M) <= p
        model.subset_number = Constraint(rule=subset_number_rule)

        model.obj = Objective(expr=sum(C[i][j]*model.x[i,j] for j in J for i in I))

        # HiGHS ships with the highspy package, so no external solver install is needed
        solver = SolverFactory('appsi_highs')
        solver.options['mip_rel_gap'] = 0.1
        # solutions are loaded only when optimal, so an infeasible model doesn't raise
        results = solver.solve(model, load_solutions=False)
        if results.solver.termination_condition == TerminationCondition.optimal:
            model.solutions.load_from(results)
            # Do something when the solution in optimal and feasible
            # print('feasible optimal')
            return('optimal')
        elif (results.solver.termination_condition == TerminationCondition.infeasible):
            # Do something when model is infeasible
            # print('infeasible')
            return('infeasible')
        else:
            # Something else is wrong
            # print('something eslse is wrong',results.solver.status)
            raise Exception("it should not happen please investigate the problem.")

    def get_results(self):
        result_list = []
        for i in self.I:
            for j in self.J:
                if round(value(self.model.x[i,j]),3) == 1:
                    result_list.append(self.selected_lengths[j])
        return result_list

class StackAlgorithmExact():
    def __init__(self, stack : Stack, selected_lengths: List[float], p: int) -> int:
        """reduces the stack length type to p types. the availale lengths are given in selected_lengths.

        Args:
            stack (Stack): stack of pieces
            selected_lengths (List[float]): list of awailable lengths
            p (int):

        Returns:
            int: number of types of the lengths, it may be greater then the given value.
        """
        self.stack = stack
        self.selected_lengths = selected_lengths
        self.p = p
    def run(self):
        p = self.p
        pieces = self.stack.get_pieces()
        minimization = Minimization(
            self.selected_lengths,
            [piece.shortest_piece_length for piece in pieces],
            [piece.length_upper_bound for piece in pieces],
            [piece.get_num_of_pieces("practical") for piece in pieces]
        )
        # every (number of subpieces, length) pair as its own type is the most a stack can need
        max_p = len(set(minimization.num_pieces)) * len(self.selected_lengths)
        while True:
            if minimization.run(p) == 'optimal':
                break
            elif p >= max_p:
                raise ValueError("a piece of the stack fits none of the selected lengths")
            else:
                p = p+1

        new_lengths = minimization.get_results()
        for i,length in enumerate(new_lengths):
            pieces[i].shortest_piece_length = length
        return p
