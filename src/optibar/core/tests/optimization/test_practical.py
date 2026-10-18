import pytest
from optibar.core.components.collections import Stack
from optibar.core.optimization.practical.practical import PracticalOptimization
from optibar.core.optimization.practical.total import NotEnoughTypes

@pytest.fixture
def stack_one(piece_required_factory):
    stack = Stack(5)
    stack.add_piece(piece_required_factory(4,8,5))
    stack.add_piece(piece_required_factory(2,8,10))
    stack.add_piece(piece_required_factory(2,8,10))
    stack.add_piece(piece_required_factory(0,8,10))
    stack.add_piece(piece_required_factory(0,15,5))
    stack.add_piece(piece_required_factory(0,15,5))
    stack.add_piece(piece_required_factory(0,15,5))
    return stack

@pytest.fixture
def stack_two(piece_required_factory):
    stack = Stack(5)
    stack.add_piece(piece_required_factory(6,8,4))
    stack.add_piece(piece_required_factory(6,8,4))
    stack.add_piece(piece_required_factory(5,8,8))
    stack.add_piece(piece_required_factory(0,12,12))
    stack.add_piece(piece_required_factory(0,12,12))
    return stack

def stacks(*stacks):
    return {'S1': {'bottom': list(stacks)}}

def shortest_lengths(stack):
    return [round(piece.shortest_piece_length, 2) for piece in stack.get_pieces()]

class TestPracticalOptimization():
    def test_not_enough_total(self,stack_one, stack_two):
        pieces = stack_one.get_pieces()+stack_two.get_pieces()
        with pytest.raises(NotEnoughTypes, match="total") as excinfo:
            PracticalOptimization(pieces,stacks(stack_one,stack_two),3,3).run()
        # [2, 4.3, 8, 12] covers all pieces within their upper bounds
        assert 4 == excinfo.value.min_feasible_type_num
    
    def test_not_enough_stack(self,stack_one, stack_two):
        """a stack that needs more types than allowed is reported, not an error"""
        pieces = stack_one.get_pieces()+stack_two.get_pieces()
        excess = PracticalOptimization(pieces,stacks(stack_one,stack_two),5,1).run()
        # stack_one has one and two-subpiece pieces, each group needs its own type
        assert excess == [{'strip_name': 'S1', 'level': 'bottom', 'excess_list': [2]}]

    def test_no_error(self,stack_one, stack_two):
        pieces = stack_one.get_pieces()+stack_two.get_pieces()
        assert PracticalOptimization(pieces,stacks(stack_one,stack_two),5,3).run() == []
        assert shortest_lengths(stack_one) == [6,6,6,8,4.3,4.3,4.3]
        assert shortest_lengths(stack_two) == [2,2,4.3,12,12]
