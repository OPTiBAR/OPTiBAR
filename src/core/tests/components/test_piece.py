import pytest
from optibar_core.src.components.piece import Piece,Bend
from optibar_core.src.components.period import Period


class TestStatic():
    """tests static methods of Piece class
    """
    def test_net_length_shorter_than_std(self):
        checks = (
            10 == Piece.get_net_length(10, 1),
            12 == Piece.get_net_length(12, 1)
        )
        assert all(checks)
    
    def test_net_length_longer_than_std(self):
        checks = (
            12 + 2 == Piece.get_net_length(13, 1),
            12 + 12 == Piece.get_net_length(23, 1),
            12 + 12 + 2 == Piece.get_net_length(24, 1),
        )
        assert all(checks)
    def test_get_shortest_piece_net_length(self):
        checks = (
            8 == Piece.get_shortest_piece_net_length(8, 1),
            12 == Piece.get_shortest_piece_net_length(12, 1),
            2 == Piece.get_shortest_piece_net_length(13, 1),
            12 == Piece.get_shortest_piece_net_length(23, 1),
            2 == Piece.get_shortest_piece_net_length(24, 1),
        )
        assert all(checks)

class TestShortestPiece():
    def test_long_piece(self,long_piece):
        checks = (
            3.3 == round(long_piece.get_shortest_piece_length("practical"),3),
            4.3 == round(long_piece.get_shortest_piece_length("executive"),3)
        )
        assert all(checks)
    
    def test_short_piece(self, short_piece):
        checks = (
            4 == short_piece.get_shortest_piece_length("practical"),
            5 == short_piece.get_shortest_piece_length("executive")
        )
        assert all(checks)

class TestNumOfPieces():
    def test_short_piece(self, short_piece):
        checks = (
            1 == short_piece.get_num_of_pieces("practical"),
            1 == short_piece.get_num_of_pieces("executive")
        )
        assert all(checks)

    def test_medium_piece(self, medium_piece):
        checks = (
            1 == medium_piece.get_num_of_pieces("practical"),
            2 == medium_piece.get_num_of_pieces("executive")
        )
        assert all(checks)
    def test_long_piece(self, long_piece):
        checks = (
            2 == long_piece.get_num_of_pieces("practical"),
            2 == long_piece.get_num_of_pieces("executive"),
        )

class TestBend():
    def test_eq_init(self):
        bend_1 = Bend()
        bend_2 = Bend(0,0)
        assert bend_1 == bend_2
    
    def test_eq_start(self):
        bend_1 = Bend(0,1)
        bend_2 = Bend(0,0)
        assert bend_1 != bend_2

    def test_eq_start(self):
        bend_1 = Bend(1,1)
        bend_2 = Bend(0,0)
        assert bend_1 != bend_2

class TestEquality():
    def test_true(self, rebar, short_piece):
        theoretical =  Period(5,8)
        piece = Piece(rebar,theoretical)
        piece.practical = Period(4.5,8.5)
        piece.executive = Period(4,9)
        assert piece == short_piece
    def test_bend_diff(self, rebar, short_piece):
        theoretical =  Period(5,8)
        piece = Piece(rebar,theoretical)
        piece.practical = Period(4.5,8.5)
        piece.executive = Period(4,9)
        piece.bend.start = 1
        assert piece != short_piece

# @pytest.mark.usefixtures("rebar")
class TestSubpieces():
    def test_short_piece(self, rebar, short_piece):
        assert short_piece.get_subpieces() == [short_piece]
    def test_medium_piece(self, rebar, medium_piece):
        # first piece
        theoretical =  Period(5,16)
        piece_1 = Piece(rebar,theoretical)
        piece_1.practical = Period(4.5,16)
        piece_1.executive = Period(4,16)
        # second piece
        theoretical =  Period(14.7,16)
        piece_2 = Piece(rebar,theoretical)
        piece_2.practical = Period(14.7,16.5)
        piece_2.executive = Period(14.7,17)
        assert medium_piece.get_subpieces() == [piece_1,piece_2]

    def test_long_piece(self, rebar, long_piece):
        # first piece
        theoretical =  Period(5,16)
        piece_1 = Piece(rebar,theoretical)
        piece_1.practical = Period(4.5,16)
        piece_1.executive = Period(4,16)
        # second piece
        theoretical =  Period(14.7,18)
        piece_2 = Piece(rebar,theoretical)
        piece_2.practical = Period(14.7,18.5)
        piece_2.executive = Period(14.7,19)
        assert long_piece.get_subpieces() == [piece_1,piece_2]
    
    def test_long_start_bended_piece(self, rebar, long_piece):
        long_piece.bend.end = long_piece.rebar.get_bend_length()
        # first piece
        theoretical =  Period(5,16)
        piece_1 = Piece(rebar,theoretical)
        piece_1.practical = Period(4.5,16)
        piece_1.executive = Period(4,16)
        # second piece
        theoretical =  Period(14.7,18)
        piece_2 = Piece(rebar,theoretical)
        piece_2.practical = Period(14.7,18.5)
        piece_2.executive = Period(14.7,19)
        piece_2.bend.end = long_piece.rebar.get_bend_length()
        assert long_piece.get_subpieces() == [piece_1,piece_2]

    def test_long_end_bended_piece(self, rebar, long_piece):
        long_piece.bend.end = long_piece.rebar.get_bend_length()
        # first piece
        theoretical =  Period(5,16)
        piece_1 = Piece(rebar,theoretical)
        piece_1.practical = Period(4.5,16)
        piece_1.executive = Period(4,16)
        # second piece
        theoretical =  Period(14.7,18)
        piece_2 = Piece(rebar,theoretical)
        piece_2.practical = Period(14.7,18.5)
        piece_2.executive = Period(14.7,19)
        piece_2.bend.end = long_piece.rebar.get_bend_length()
        assert long_piece.get_subpieces() == [piece_1,piece_2]

    def test_long_two_side_bended_piece(self, rebar, long_piece):
        long_piece.bend.start = long_piece.rebar.get_bend_length()
        long_piece.bend.end = long_piece.rebar.get_bend_length()
        # first piece
        theoretical =  Period(5,16)
        piece_1 = Piece(rebar,theoretical)
        piece_1.practical = Period(4.5,16)
        piece_1.executive = Period(4,16)
        piece_1.bend.start = long_piece.rebar.get_bend_length()
        # second piece
        theoretical =  Period(14.7,18)
        piece_2 = Piece(rebar,theoretical)
        piece_2.practical = Period(14.7,18.5)
        piece_2.executive = Period(14.7,19)
        piece_2.bend.end = long_piece.rebar.get_bend_length()
        assert long_piece.get_subpieces() == [piece_1,piece_2]

    def test_very_long_piece(self, rebar, very_long_piece):
        # first piece
        theoretical =  Period(5,16)
        piece_1 = Piece(rebar,theoretical)
        piece_1.practical = Period(4.5,16)
        piece_1.executive = Period(4,16)
        # second piece
        theoretical =  Period(14.7,26.7)
        piece_2 = Piece(rebar,theoretical)
        piece_2.practical = Period(14.7,26.7)
        piece_2.executive = Period(14.7,26.7)
        # third piece
        theoretical =  Period(25.4,25.4)
        piece_3 = Piece(rebar,theoretical)
        piece_3.practical = Period(25.4,26)
        piece_3.executive = Period(25.4,27)
        assert very_long_piece.get_subpieces() == [piece_1, piece_2, piece_3]

class TestRefresh():
    def test_refresh(self, short_piece):
        piece = short_piece
        piece.bend.start = 0.4
        piece.bend.start = 0.3
        piece.shortest_piece_length = 10
        piece.length_upper_bound = 11
        piece.refresh()
        checks = (
            piece.practical is None,
            piece.executive is None,
            piece.shortest_piece_length is None,
            piece.length_upper_bound is None,
            piece.bend == Bend(),
        )
        assert all(checks)
