import pytest
import copy
from optibar_core.src.optimization.executive.stack import StackAlgorithm, TypeCounter, Cell
from optibar_core.src.optimization.executive.errors import NotEnoughTypes
from optibar_core.src.components.collections import Stack

@pytest.fixture
def type_counter() -> TypeCounter:
    tc = TypeCounter()
    tc.add_piece(1,3)
    tc.add_piece(1,5)
    tc.add_piece(2,5)
    tc.add_piece(3,6)
    return tc

@pytest.fixture
def stack(piece_practical_factory):
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
def type_counter_factory():
    def _factory(data_dict):
        tc = TypeCounter()
        for num_of_pieces in data_dict:
            for length in data_dict[num_of_pieces]:
                tc.add_piece(num_of_pieces, length)
        return tc
    return _factory

@pytest.fixture
def cell_factory() -> Cell:
    def _factory(value, ref, type_counter):
        cell = Cell()
        cell.value = value
        cell.ref = ref
        cell.type_counter = type_counter
        return cell
    return _factory
    
class TestStackTypeCounter():
    def test_get_num_of_types(self, type_counter: TypeCounter):
        assert type_counter.get_num_of_types() == 4
    
    def test_add_duplicate(self, type_counter: TypeCounter):
        type_counter.add_piece(1,3)
        assert type_counter.get_num_of_types() == 4
    
    def test_copy_eq(self, type_counter: TypeCounter):
        tc = copy.copy(type_counter)
        tc.add_piece(2,13)
        assert tc != type_counter
    def test_add(self, type_counter: TypeCounter):
        tc_1 = TypeCounter()
        tc_1.add_piece(1,2)
        tc_2 = TypeCounter()
        tc_2.add_piece(1,3)
        tc_1.add(tc_2)
        tc_3 = TypeCounter()
        tc_3.add_piece(1,2)
        tc_3.add_piece(1,3)
        assert tc_1 == tc_3
    

class TestStackAlgorithm():
    def test_run(self, stack: Stack, cell_factory, type_counter_factory):
        sa = StackAlgorithm(stack, [4,5,6,10])
        container = sa._container
        desired_container = [
            [
                cell_factory(0,None,type_counter_factory({1:{4}})),
                cell_factory(3.1,None,type_counter_factory({1:{5},2:{5}})),
                cell_factory(None,None,type_counter_factory({})),
                cell_factory(None,None,type_counter_factory({}))
            ],
            [
                None,
                cell_factory(2.1,0,type_counter_factory({1:{4},2:{5}})),
                cell_factory(3.1,1,type_counter_factory({1:{5,6},2:{5}})),
                cell_factory(13.1,1,type_counter_factory({1:{10,5},2:{5}}))
            ],
            [
                None,
                None,
                cell_factory(2.1,1,type_counter_factory({1:{4,6},2:{5}})),
                cell_factory(5.1,2,type_counter_factory({1:{10,5,6},2:{5}}))
            ],
            [
                None,
                None,
                None,
                cell_factory(4.1,2,type_counter_factory({1:{10,4,6},2:{5}}))
            ]
        ]
        assert container == desired_container
    
    def test_get_lengths(self, stack):
        sa = StackAlgorithm(stack, [4,5,6,10])
        type_dict = sa._get_selected_lengths()
        assert type_dict == {3:[10,5],4:[10,6,5,4]}
    
    def test_adjust_lengths_one(self, stack):
        sa = StackAlgorithm(stack, [4,5,6,10])
        type_dict = sa._get_selected_lengths()
        sa._adjust_lengths(type_dict[3])
        assert (
            list(map(lambda piece: getattr(piece,'shortest_piece_length'),stack.get_pieces())) == \
                [5,10,10,10,5,5,5]
        )
    
    def test_adjust_lengths_two(self, stack):
        sa = StackAlgorithm(stack, [4,5,6,10])
        type_dict = sa._get_selected_lengths()
        sa._adjust_lengths(type_dict[4])
        assert (
            list(map(lambda piece: getattr(piece,'shortest_piece_length'),stack.get_pieces())) == \
                [4,6,6,10,5,5,5]
        )

    def test_adjust_lengths_bound_error(self, stack):
        sa = StackAlgorithm(stack, [4,5,6,10])
        type_dict = sa._get_selected_lengths()
        with pytest.raises(ValueError, match="upper bound"):
            sa._adjust_lengths([6,8,10])

    def test_adjust_lengths_longest_error(self, stack):
        sa = StackAlgorithm(stack, [4,5,6,10])
        type_dict = sa._get_selected_lengths()
        with pytest.raises(ValueError, match="longest"):
            sa._adjust_lengths([4,5,6])
    
    def test_set_lengths_one(self, stack):
        sa = StackAlgorithm(stack, [4,5,6,10])
        sa.set_lengths(3)
        assert (
            list(map(lambda piece: getattr(piece,'shortest_piece_length'),stack.get_pieces())) == \
                [5,10,10,10,5,5,5]
        )
    
    def test_set_lengths_two(self, stack):
        sa = StackAlgorithm(stack, [4,5,6,10])
        sa.set_lengths(4)
        assert (
            list(map(lambda piece: getattr(piece,'shortest_piece_length'),stack.get_pieces())) == \
                [4,6,6,10,5,5,5]
        )
    
    def test_set_lengths_error(self,stack):
        sa = StackAlgorithm(stack, [4,5,6,10])
        with pytest.raises(NotEnoughTypes, match="stack"):
            sa.set_lengths(2)
