import pytest
from optibar_core.src.components.collections import Stack, Bunch, Container
from optibar_core.src.components.piece import Piece
from optibar_core.src.components.diagram import Diagram

@pytest.fixture
def stack(short_piece, medium_piece, long_piece):
    stack = Stack(10)
    stack.add_piece(short_piece)
    stack.add_piece(medium_piece)
    stack.add_piece(long_piece)
    return stack

@pytest.fixture(scope="class")
def diagram():
    stations = list(range(10))
    areas = [3, 0, 0, 0, 5, 4, 3, 1, 0, 4]
    return Diagram(stations, areas)

@pytest.fixture(scope="class")
def container(diagram):
    return Container(diagram)

@pytest.fixture
def container_bunched(diagram, piece_factory):
    factory = piece_factory
    container = Container(diagram)
    container.add_row([factory(0,3), factory(2,9)]) # row 0
    container.add_row([factory(0,2), factory(2,9)]) # row 1
    container.add_row([factory(0,2), factory(2,5), factory(6,8)]) # row 2
    container.add_row([factory(0,2), factory(2,5)]) # row 3
    container.add_row([factory(2,4)]) # row 4
    container.add_row([factory(2,4)]) # row 5
    container.add_row([factory(2,3)]) # row 6
    return container

class TestStack():
    def test_stack_lenght(self, stack):
        assert len(stack) == 3
    def test_stack_equality(self, stack,short_piece, medium_piece, long_piece):
        other = Stack(10)
        other.add_piece(short_piece)
        other.add_piece(medium_piece)
        other.add_piece(long_piece)
        assert other == stack
class TestBunch():
    def test_bunch_count(self, piece_factory):
        bunch = Bunch()
        piece = piece_factory(1,2)
        bunch.add(piece)
        assert bunch.get_count() == 1
    
    def test_bunch_pieces(self, piece_factory):
        bunch = Bunch()
        bunch.add(piece_factory(1,2))
        bunch.add(piece_factory(1,2))
        assert bunch.get_count() == 2


class TestContainer():
    def test_add_row(self, container, diagram, rebar):
        rows = []
        while diagram.is_positive():
            periods = diagram.insert_additional(1)
            row = [Piece(rebar,period) for period in periods]
            for piece in row:
                piece.practical = piece.theoretical
                piece.executive = piece.theoretical
            container.add_row(row)
            rows.append(row)
            # print(diagram.is_positive())
        assert container.get_rows() == rows

    def test_get_pieces(self, container):
        pieces = list(container.get_pieces())
        for piece in pieces:
            pass
            # print(piece)
        assert len(list(container.get_pieces())) == 11
        
    def test_get_stacks(self, container):
        stacks = container.get_stacks("executive")
        assert len(stacks) == 3
        assert len(stacks[2].get_pieces()) == 3 and stacks[2].peak_station == 0
        assert len(stacks[0].get_pieces()) == 5 and stacks[0].peak_station == 4
        assert len(stacks[1].get_pieces()) == 4 and stacks[1].peak_station == 9
    
    def test_drawing_data(self, container_bunched):
        rows = container_bunched.get_drawing_data()
        checks = (
            len(rows) == 4,
            len(rows[0]) == 2 and rows[0][0].get_count() == 1 and rows[0][1].get_count() == 2,
            len(rows[1]) == 3 and rows[1][0].get_count() == 3 and rows[1][1].get_count() == 2 and rows[1][2].get_count() == 1,
            len(rows[2]) == 1 and rows[2][0].get_count() == 2,
            len(rows[3]) == 1 and rows[3][0].get_count() == 1
        )
        assert all(checks)

