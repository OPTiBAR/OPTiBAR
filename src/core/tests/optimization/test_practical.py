import pytest
from optibar_core.src.components.collections import Stack
from optibar_core.src.components.period import Period
from optibar_core.src.optimization.practical import (
    PieceDomination,
    StackMinimization,
    PracticalOptimization,
    IncreasedLength,
    DominationType
)


@pytest.fixture
def pair_factory(rebar):
    def _factory(value, ref, domination):
        pair = StackMinimization.Pair()
        pair.value = value
        pair.ref = ref
        pair.domination = domination
        return pair
    return _factory

@pytest.fixture
def stack(piece_theoretical_factory):
    stack = Stack(0)
    stack.add_piece(piece_theoretical_factory(-2,1))
    stack.add_piece(piece_theoretical_factory(-3,1.5))
    stack.add_piece(piece_theoretical_factory(-3.5,2))
    return stack

class TestHelperClasses():
    def test_pair(self):
        pair_1 = StackMinimization.Pair()
        pair_1.domination = DominationType.D
        pair_1.value = 10
        pair_1.ref = 2

        pair_2 = StackMinimization.Pair()
        pair_2.domination = DominationType.D
        pair_2.value = 10
        pair_2.ref = 2

        pair_3 = StackMinimization.Pair()
        pair_3.domination = DominationType.LD
        pair_3.value = 11
        pair_3.ref = 2
        assert all((
            pair_1 == pair_2,
            pair_1 != pair_3
        ))
    def test_selected_length(self):
        selected_length_1 = StackMinimization.SelectedLength(10, DominationType.D)
        selected_length_2 = StackMinimization.SelectedLength(10, DominationType.D)
        selected_length_3 = StackMinimization.SelectedLength(11, DominationType.LD)
        assert all((
            selected_length_1 == selected_length_2,
            selected_length_1 != selected_length_3
        ))

    def test_increased_length(self):
        increased_length_1 = IncreasedLength(10, DominationType.LD)
        increased_length_2 = IncreasedLength(10, DominationType.LD)
        increased_length_3 = IncreasedLength(12, DominationType.D)
        assert all((
            increased_length_1 == increased_length_2,
            increased_length_1 != increased_length_3
        ))
    def test_piece_domination(self):
        piece_domination_1  = PieceDomination(DominationType.D, DominationType.LD)
        piece_domination_2  = PieceDomination(DominationType.D, DominationType.LD)
        piece_domination_3  = PieceDomination(DominationType.LD, DominationType.LD)
        assert all((
            piece_domination_1 == piece_domination_2,
            piece_domination_1 != piece_domination_3
        ))

class TestStackMinimization():
    def test_container(self, pair_factory):
        sm = StackMinimization(lengths=[1,1.5,2], d_length=.3, ld_length=1.4)
        container = [
            [
                pair_factory(1.4,None,DominationType.LD),
                pair_factory(3.6,None,DominationType.D),
                pair_factory(6.9,None,DominationType.D)
            ],
            [
                None,
                pair_factory(3.8,0,DominationType.LD),
                pair_factory(6.2,0,DominationType.LD)
            ],
            [
                None,
                None,
                pair_factory(6.7,1,DominationType.LD)
            ]
        ]
        equality = True
        for i,row in enumerate(sm._container):
            for j,pair in enumerate(row):
                if container[i][j] != pair:
                    equality = False
                    break
        assert equality
    
    def test_selected_length(self):
        sm = StackMinimization(lengths=[1,1.5,2], d_length=.3, ld_length=1.4)
        selected_lengths = [
            StackMinimization.SelectedLength(2,DominationType.LD),
            StackMinimization.SelectedLength(0,DominationType.LD),
        ]
        
        assert sm._selected_lengths == selected_lengths
    
    def test_get_results(self):
        sm = StackMinimization(lengths=[1,1.5,2], d_length=.3, ld_length=1.4)
        increased_lengths = [
            IncreasedLength(.4, DominationType.LD),
            IncreasedLength(.9, DominationType.LD),
            IncreasedLength(.9, DominationType.LD)
        ]
        assert increased_lengths == sm.get_results()



class TestPracticalOptimization():
    def test_extract_lengths(self, stack):
        po = PracticalOptimization(stack=stack, d_length=0.3, ld_length=1.4)
        # for piece in stack.get_pieces():
        #     print(piece)
        assert all((
            po._extract_lengths("start") == [2,3,3.5],
            po._extract_lengths("end") == [1,1.5,2]
        ))
    def test_results(self, stack):
        po = PracticalOptimization(stack=stack, d_length=0.3, ld_length=1.4)
        assert (
            [piece.practical for piece in stack.get_pieces()] == [
                Period(-2.3,1.4),
                Period(-3.8,2.4),
                Period(-4.3,2.9)
            ]
        )


    
        