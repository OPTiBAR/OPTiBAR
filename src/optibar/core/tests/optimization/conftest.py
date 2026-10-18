import pytest

@pytest.fixture
def piece_theoretical_factory(piece_factory):
    def _factory(start, end):
        piece = piece_factory(start,end)
        piece.required = None
        piece.practical = None
        return piece
    return _factory

@pytest.fixture
def piece_required_factory(piece_factory):
    def _factory(start, end, upper_bound):
        piece = piece_factory(start,end)
        piece.required = piece.theoretical
        piece.practical = piece.theoretical
        piece.length_upper_bound = upper_bound
        piece.shortest_piece_length = piece.get_shortest_piece_length("required")
        return piece
    return _factory