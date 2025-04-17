from core.src.components.collections import Stack
from pyomo.environ import *
from typing import List
from pyomo.opt import SolverStatus, TerminationCondition

class Minimization():
    def __init__(self, selected_length: List[float], lengths: List[float], upper_bounds: List[float], num_pieces: List[int]):
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
                if LS[i] <= LO[j]:
                    C[i][j] = LO[j]-LS[i]
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
            if LS[i] > LO[j]:
                return model.x[i,j] == 0
            else:
                return Constraint.Skip
        model.not_shorter = Constraint(I, J, rule=not_shorter_rule)

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

        solvername='glpk'
        # solverpath_folder='D:\\winglpk-4.65\\glpk-4.65\\w64' #does not need to be directly on c drive
        solverpath_exe='D:\\winglpk-4.65\\glpk-4.65\\w64\\glpsol' #does not need to be directly on c drive
        # sys.path.append(solverpath_folder)

        # solvername='cplex'
        # solverpath_exe='C:\\Program Files\\IBM\\ILOG\\CPLEX_Studio1261\\cplex\\bin\\x64_win64\\cplex'

        solver=SolverFactory(solvername)#, executable=solverpath_exe)
        solver.options['mipgap'] = 0.1
        results = solver.solve(model)
        if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
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
            [piece.get_num_of_pieces("executive") for piece in pieces]
        )
        while True:
            if minimization.run(p) == 'optimal':
                break
            else:
                p = p+1
                
        new_lengths = minimization.get_results()
        for i,length in enumerate(new_lengths):
            pieces[i].shortest_piece_length = length
        return p
        