import pytest
import copy
from optibar_core.src.optimization.executive.total import TotalAlgorithm, Bunch
from optibar_core.src.optimization.executive.errors import NotEnoughTypes


@pytest.fixture
def pair_factory():
    def _factory(value, ref):
        pair = TotalAlgorithm.Pair()
        pair.value = value
        pair.ref = ref
        return pair
    return _factory

@pytest.fixture
def pieces(piece_practical_factory):
    pieces = [
        piece_practical_factory(-1,0, 2),
        piece_practical_factory(0,1, 3),
        piece_practical_factory(0,2, 3),
        piece_practical_factory(0,2, 3),
        piece_practical_factory(0,2, 5),
        piece_practical_factory(-1,3, 4),
        piece_practical_factory(-1,3, 4),
        piece_practical_factory(-2,4, 7),
    ]
    return pieces

@pytest.fixture
def pieces_no_bound(piece_practical_factory):
    pieces = [
        piece_practical_factory(-1,0, 12),
        piece_practical_factory(0,1, 12),
        piece_practical_factory(0,2, 12),
        piece_practical_factory(0,2, 12),
        piece_practical_factory(0,2, 12),
        piece_practical_factory(-1,3, 12),
        piece_practical_factory(-1,3, 12),
        piece_practical_factory(-2,4, 12),
    ]
    return pieces

class TestPair():
    def test_pair_class(self):
        pair_1 = TotalAlgorithm.Pair()
        pair_1.value = 10
        pair_1.ref = 2
        pair_2 = TotalAlgorithm.Pair()
        pair_2.value = 10
        pair_2.ref = 2
        pair_3 = TotalAlgorithm.Pair()
        pair_3.value = 11
        pair_3.ref = 3
        assert all((
            pair_1 == pair_2,
            pair_1 != pair_3
        ))

class TestBunch():
    def test_bunch(self, piece_factory):
        bunch = Bunch(10)
        for i in range(4):
            piece = piece_factory(0,5)
            piece.length_upper_bound = piece.theoretical.get_length() + i
            bunch.add_piece(piece)
        assert all((
            bunch.get_length() == 10,
            len(bunch.get_pieces()) == 4,
            bunch.get_count() == 4,
            bunch.get_upper_bound() == 5
        ))


class TestTotalAlgorithm():
    def test_get_bunch_dict(self, pieces):
        ta = TotalAlgorithm(pieces)
        bunch_dict = ta._get_bunch_dict(pieces)
        bunches = [bunch_dict[length] for length in sorted(bunch_dict.keys())]
        counts = list(map(lambda bunch: bunch.get_count(), bunches))
        lengths = list(map(lambda bunch: bunch.get_length(), bunches))
        assert all((
            counts == [2,3,2,1],
            lengths == [1,2,4,6]
        ))
    
    def test_get_inputs(self,pieces):
        ta = TotalAlgorithm(pieces)
        bunch_dict = ta._get_bunch_dict(pieces)
        input_dict = ta._get_inputs(bunch_dict)
        assert all((
            input_dict["lengths"] == [1,2,4,6,12],
            input_dict["counts"] == [2,3,2,1,0],
            input_dict["upper_bounds"] == [2,3,4,7,12]
        ))

    def test_run_no_bound(self, pieces_no_bound, pair_factory):
        ta = TotalAlgorithm(pieces_no_bound)
        container = ta._container
        desired_container = [
            [
                pair_factory(0,None),
                pair_factory(2,None),
                pair_factory(12,None),
                pair_factory(26,None),
                pair_factory(74,None)
            ],
            [
                None,
                pair_factory(0,0),
                pair_factory(2,1),
                pair_factory(12,1),
                pair_factory(26,2)
            ],
            [
                None,
                None,
                pair_factory(0,1),
                pair_factory(2,2),
                pair_factory(12,2)
            ],
            [
                None,
                None,
                None,
                pair_factory(0,2),
                pair_factory(2,3)
            ],
            [
                None,
                None,
                None,
                None,
                pair_factory(0,3)
            ]
        ]
        assert container == desired_container
    def test_run_bounded(self, pieces, pair_factory):
        ta = TotalAlgorithm(pieces)
        container = ta._container
        # for row in container:
        #     for pair in row:
        #         print(pair)
        desired_container = [
            [
                pair_factory(0,None),
                pair_factory(2,None),
                pair_factory(float("inf"),None),
                pair_factory(float("inf"),None),
                pair_factory(float("inf"),None)
            ],
            [
                None,
                pair_factory(0,0),
                pair_factory(2,1),
                pair_factory(float("inf"),None),
                pair_factory(float("inf"),None)
            ],
            [
                None,
                None,
                pair_factory(0,1),
                pair_factory(2,2),
                pair_factory(float("inf"),None)
            ],
            [
                None,
                None,
                None,
                pair_factory(0,2),
                pair_factory(2,3)
            ],
            [
                None,
                None,
                None,
                None,
                pair_factory(0,3)
            ]
        ]
        assert container == desired_container

    def test_run_document(self, pieces_no_bound, pair_factory):
        ta = TotalAlgorithm(pieces_no_bound)
        input_dict = {
            "lengths": [2,3,7,11,15],
            "counts": [1,5,3,10,4],
            "upper_bounds": [15,15,15,15,15]
        }
        ta._run(**input_dict)
        container = ta._container
        desired_container = [
            [
                pair_factory(0,None),
                pair_factory(1,None),
                pair_factory(25,None),
                pair_factory(61,None),
                pair_factory(137,None),
            ],
            [
                None,
                pair_factory(0,0),
                pair_factory(1,1),
                pair_factory(25,1),
                pair_factory(61,3),
            ],
            [
                None,
                None,
                pair_factory(0,1),
                pair_factory(1,2),
                pair_factory(25,3),
            ],
            [
                None,
                None,
                None,
                pair_factory(0,2),
                pair_factory(1,3),
            ],
            [
                None,
                None,
                None,
                None,
                pair_factory(0,3),
            ]
        ]
        assert(container == desired_container)
    
    def test_get_selected_lengths_too_much(self, pieces):
        ta = TotalAlgorithm(pieces)
        # with pytest.raises(ValueError, match="too much"):
        # print(ta.get_selected_lengths(12))
    
    def test_get_selected_lengths_not_enough(self, pieces):
        ta = TotalAlgorithm(pieces)
        with pytest.raises(NotEnoughTypes, match="total") as excinfo:
            ta.get_selected_lengths(3)
        assert 4 == excinfo.value.min_feasible_type_num
        