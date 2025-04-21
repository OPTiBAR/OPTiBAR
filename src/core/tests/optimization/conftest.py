import pytest

@pytest.fixture
def piece_theoretical_factory(piece_factory):
    def _factory(start, end):
        piece = piece_factory(start,end)
        piece.practical = None
        piece.executive = None
        return piece
    return _factory

@pytest.fixture
def piece_practical_factory(piece_factory):
    def _factory(start, end, upper_bound):
        piece = piece_factory(start,end)
        piece.practical = piece.theoretical
        piece.executive = None
        piece.length_upper_bound = upper_bound
        piece.shortest_piece_length = piece.get_shortest_piece_length("practical")
        return piece
    return _factory