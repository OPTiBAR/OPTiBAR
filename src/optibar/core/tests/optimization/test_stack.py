import pytest
from optibar.core.components.collections import Stack
from optibar.core.optimization.practical.stack import StackAlgorithm, StackProgram

SELECTED = [4, 5, 6, 12] # the lengths of the foundation


class TestStackProgram():
    @pytest.mark.parametrize('p, expected', [
        (1, [5, 5, 5]), # one type: the longest piece decides
        (2, [4, 5, 5]), # 3.2 m gets 4 m; 4.1 m can't, it is longer
        (3, [4, 5, 5]), # a third type doesn't help
    ])
    def test_least_added_length(self, p, expected):
        program = StackProgram(SELECTED, [3.2, 4.1, 5.0], [12, 12, 12], [1, 1, 1])
        assert program.run(p) == 'optimal'
        assert program.get_results() == expected

    def test_no_length_long_enough(self):
        program = StackProgram(SELECTED, [12.5], [13], [1])
        assert program.run(3) == 'infeasible'

    def test_types_count_the_number_of_pieces(self):
        """two 4 m lengths, one of a single piece and one the short end of a 16 m bar: two types"""
        program = StackProgram(SELECTED, [4.0, 4.0], [12, 12], [1, 2])
        assert program.run(1) == 'infeasible'
        assert program.run(2) == 'optimal'
        assert program.get_results() == [4, 4]


class TestStackAlgorithm():
    def test_sets_the_lengths(self, piece_required_factory):
        stack = Stack(5)
        for start, end in ((2, 5.2), (1, 5.1), (0, 5)):
            stack.add_piece(piece_required_factory(start, end, 12))
        assert StackAlgorithm(stack, SELECTED, 1).run() == 1
        assert [piece.shortest_piece_length for piece in stack.get_pieces()] == [5, 5, 5]

    def test_more_types_when_needed(self, piece_required_factory):
        """a piece of one bar and a piece of two bars with the same short length need two types:
        asked for one, the stack gets two"""
        stack = Stack(5)
        stack.add_piece(piece_required_factory(0, 4, 12))
        long = piece_required_factory(0, 20, 12)
        stack.add_piece(long)
        assert long.get_num_of_pieces('practical') == 2
        assert StackAlgorithm(stack, SELECTED + [long.shortest_piece_length], 1).run() == 2
