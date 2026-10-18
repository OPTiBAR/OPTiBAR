from core.optimization.practical.errors import NotEnoughTypes
from core.components.piece import Piece
from core.components.collections import Stack

from .exactstack import StackAlgorithmExact
from .total import TotalAlgorithm


class ExecutiveOptimization():
    def __init__(self,
            pieces: list[Piece],
            stacks: dict[str, list[Stack]],
            total_num_of_types: int,
            stack_num_of_types: int
        ):
        """Algorithm to reduce number of length types of pieces and stacks.

        Args:
            pieces (List[Piece]): list of all pieces of the foundation
            stacks (Dict[str, List[Stack]]): dictionary of stacks the key is the strip name and the value is the list of stacks.
            total_num_of_types (int): total number of length types
            stack_num_of_types (int): stack number of length types
        """
        self.total_num_of_types = total_num_of_types
        self.stack_num_of_types = stack_num_of_types
        self.pieces = pieces
        self.stacks = stacks

    def run(self):
        total_alg = TotalAlgorithm(pieces= self.pieces)
        try:
            selected_lengths = total_alg.get_selected_lengths(number_of_types= self.total_num_of_types)
        except NotEnoughTypes as e:
            raise e
        stack_excess_list = []
        for strip_name in self.stacks:
            for level in self.stacks[strip_name]:
                excess_list = []
                for stack in self.stacks[strip_name][level]:
                    sa = StackAlgorithmExact(stack, selected_lengths, self.stack_num_of_types)
                    p = sa.run()
                    if p > self.stack_num_of_types:
                        excess_list.append(p)
                if len(excess_list)>0:
                    stack_excess_list.append({
                        'strip_name': strip_name,
                        'level': level,
                        'excess_list': excess_list
                    })
        return stack_excess_list
