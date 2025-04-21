import pytest
from optibar_core.src.containers import Stack
from optibar_core.src.optimization.executive.executive import ExecutiveOptimization
from optibar_core.src.optimization.executive.total import NotEnoughTypes

@pytest.fixture
def stack_one(piece_practical_factory):
    stack = Stack(5)
    stack.add_piece(piece_practical_factory(4,8,5))
    stack.add_piece(piece_practical_factory(2,8,10))
    stack.add_piece(piece_practical_factory(2,8,10))
    stack.add_piece(piece_practical_factory(0,8,10))
    stack.add_piece(piece_practical_factory(0,15,5))
    stack.add_piece(piece_practical_factory(0,15,5))
    stack.add_piece(piece_practical_factory(0,15,5))
    return stack

@pytest.fixture
def stack_two(piece_practical_factory):
    stack = Stack(5)
    stack.add_piece(piece_practical_factory(6,8,4))
    stack.add_piece(piece_practical_factory(6,8,4))
    stack.add_piece(piece_practical_factory(5,8,8))
    stack.add_piece(piece_practical_factory(0,12,12))
    stack.add_piece(piece_practical_factory(0,12,12))
    return stack

class TestExecutiveOptimization():
    def test_not_enough_total(self,stack_one, stack_two):
        pieces = stack_one.get_pieces()+stack_two.get_pieces()
        with pytest.raises(NotEnoughTypes, match="total") as excinfo:
            ExecutiveOptimization(pieces,[stack_one,stack_two],4,3)
        assert 5 == excinfo.value.min_feasible_type_num
    
    def test_not_enough_stack(self,stack_one, stack_two):
        pieces = stack_one.get_pieces()+stack_two.get_pieces()
        with pytest.raises(NotEnoughTypes, match="stack") as excinfo:
            ExecutiveOptimization(pieces,[stack_one,stack_two],5,2)
        assert 3 == excinfo.value.min_feasible_type_num

    def test_no_error(self,stack_one, stack_two):
        pieces = stack_one.get_pieces()+stack_two.get_pieces()
        ExecutiveOptimization(pieces,[stack_one,stack_two],5,3)
        for stack in (stack_one, stack_two):
            for piece in stack.get_pieces():
                piece.shortest_piece_length = round(piece.shortest_piece_length,2)
        assert list(map(lambda piece: piece.shortest_piece_length,stack_one.get_pieces())) == \
                [4.3,8,8,8,4.3,4.3,4.3]
        assert list(map(lambda piece: piece.shortest_piece_length,stack_two.get_pieces())) == \
                [2,2,4.3,12,12]

