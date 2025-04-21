import pytest
from optibar_core.src.components.mesh import Mesh, Section
from optibar_core.src.components.diagram import Diagram
from optibar_core.src.components.period import Period
from optibar_core.src.components.piece import Piece, Bend
from optibar_core.src.optimization.practical import DominationType, PieceDomination

import warnings

@pytest.fixture
def mesh():
    stations = list(range(10))
    areas = [.008, .006, .005, .008, .009, .007, .005, .002, .008, .005]
    diagram = Diagram(stations, areas)
    section = Section(width=1, thickness=.9, effective_thickness=.8)
    mesh = Mesh(diagram, section)
    return mesh

@pytest.fixture
def filled_mesh(mesh, rebar):
    arrangment = {
            "method": "MIN_RATIO",
            "min_ratio": 0.0018
        }
    mesh.set_typical_rebar(rebar, rebar, arrangment)
    mesh.set_additional_rebar(rebar, 0.1)
    return mesh

@pytest.fixture
def piece_factory(rebar):
    def _factory(start, end, shortest_piece_length):
        piece = Piece(rebar, Period(start,end))
        piece.practical = Period(start,end)
        piece.shortest_piece_length = shortest_piece_length
        return piece
    return _factory


class TestTypical():
    def test_insert_min_ratio(self, mesh, rebar):
        arrangment = {
            "method": "MIN_RATIO",
            "min_ratio": 0.0018
        }

        mesh.set_typical_rebar(rebar, None, arrangment)
        assert mesh.typical_rebar_num == 6

    def test_insert_count_less(self,mesh, rebar):
        arrangment = {
            "method": "COUNT",
            "min_ratio": 0.0018,
            "count": 5,
        }
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mesh.set_typical_rebar(rebar, rebar, arrangment)
        assert mesh.typical_rebar_num == 5
    
    def test_insert_count_more(self,mesh, rebar):
        arrangment = {
            "method": "COUNT",
            "min_ratio": 0.0018,
            "count": 10,
        }
        mesh.set_typical_rebar(rebar, rebar, arrangment)
        assert mesh.typical_rebar_num == 10
    
    def test_insert_interval_less(self,mesh, rebar):
        arrangment = {
            "method": "INTERVAL",
            "min_ratio": 0.0018,
            "interval": .4,
        }
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mesh.set_typical_rebar(rebar, rebar, arrangment)
        assert mesh.typical_rebar_num == 3
    
    def test_insert_interval_more(self,mesh, rebar):
        arrangment = {
            "method": "INTERVAL",
            "min_ratio": 0.0018,
            "interval": .1,
        }
        mesh.set_typical_rebar(rebar, rebar, arrangment)
        assert mesh.typical_rebar_num == 10
    
    def test_insert_smart_middle(self,mesh, rebar):
        arrangment = {
            "method": "SMART",
            "min_ratio": 0.0018
        }
        mesh.set_typical_rebar(rebar, rebar, arrangment)
        assert mesh.typical_rebar_num == 18
    
    def test_insert_smart_side(self,mesh, rebar):
        arrangment = {
            "method": "SMART",
            "min_ratio": 0.0018
        }
        stations = list(range(10))
        areas = [.008, .006, .005, .008, .009, .007, .006, .0045, .0045, .001]
        diagram = Diagram(stations, areas)
        section = Section(width=1, thickness=.9, effective_thickness=.8)
        mesh = Mesh(diagram, section)
        mesh.set_typical_rebar(rebar, rebar, arrangment)
        assert mesh.typical_rebar_num == 14
    
    def test_get_pieces(self,mesh,rebar):
        method = {
            "method": "MIN_RATIO",
            "min_ratio": 0.0018
        }
        stations = list(range(20))
        areas = 20 * [.008]
        diagram = Diagram(stations, areas)
        section = Section(width=1, thickness=.9, effective_thickness=.8)
        mesh = Mesh(diagram, section)
        mesh.set_typical_rebar(rebar, rebar, method)
        piece = mesh.get_typical_piece()
        pieces = piece.get_subpieces()
        
        period = Period(-.25,11.75)
        piece_1 = Piece(rebar, period)
        piece_1.practical = period
        piece_1.executive = period
        piece_1.bend.start = .3

        period = Period(10.45, 19.25)
        piece_2 = Piece(rebar, period)
        piece_2.practical = period
        piece_2.executive = period
        piece_2.bend.end = .3

        assert pieces == [piece_1, piece_2]

class TestSetPractical():
    def test_set_practical(self, mesh, rebar):
        method = {
            "method": "MIN_RATIO",
            "min_ratio": 0.0018
        }
        mesh.set_typical_rebar(rebar, rebar, method)
        mesh.additional_rebar = rebar
        mesh._insert_additional(0.1)
        mesh._set_practical()

class TestUnify():
    def test_unify(self, mesh, rebar):
        mesh.additional_rebar = rebar
        mesh._insert_additional(0.1)
        mesh._set_practical()
        mesh._unify(by="practical")


class TestInsertAdditional():
    def test_insert(self, mesh, rebar):
        method = {
            "method": "MIN_RATIO",
            "min_ratio": 0.0018
        }
        mesh.set_typical_rebar(rebar, rebar, method)
        mesh.additional_rebar = rebar
        mesh._insert_additional(0.1)
    
    def test_insert_rebar(self, mesh, rebar):
        method = {
            "method": "MIN_RATIO",
            "min_ratio": 0.0018
        }
        mesh.set_typical_rebar(rebar, rebar, method)
        mesh.set_additional_rebar(rebar, 0.1)

def test_get_bounds(mesh: Mesh):
    bounds = mesh._get_bounds()
    assert bounds == Period(0.05, 8.95)

class TestBend():
    def test_bend_theoretcal(self, mesh, rebar):
        piece = Piece(rebar,Period(-1,5))
        piece.practical = Period(-1,5)
        mesh._bend_piece(piece)
        assert piece.bend == Bend(0.3,0)

        piece = Piece(rebar,Period(1,10))
        piece.practical = Period(1,10)
        mesh._bend_piece(piece)
        assert piece.bend == Bend(0,0.3)

        piece = Piece(rebar,Period(-1,10))
        piece.practical = Period(-1,10)
        mesh._bend_piece(piece)
        assert piece.bend == Bend(0.3,0.3)
    
    def test_bend_practical(self, mesh, rebar):
        piece = Piece(rebar,Period(1,8))
        piece.practical = Period(-1,8)
        piece.domination = PieceDomination(DominationType.D,DominationType.D)
        mesh._bend_piece(piece)
        assert piece.bend == Bend(0,0)

        piece = Piece(rebar,Period(1,8))
        piece.practical = Period(-1,8)
        piece.domination = PieceDomination(DominationType.LD,DominationType.LD)
        mesh._bend_piece(piece)
        assert piece.bend == Bend(0.3,0)

        piece = Piece(rebar,Period(1,8))
        piece.practical = Period(1,9)
        piece.domination = PieceDomination(DominationType.LD,DominationType.LD)
        mesh._bend_piece(piece)
        assert piece.bend == Bend(0,0.3)

class TestUpperBound():
    def test_set_upper_bound(self, mesh, rebar):
        piece = Piece(rebar,Period(1,8))
        piece.practical = Period(.25,8)
        piece.bend.start = .3
        mesh._set_piece_upper_bound(piece)
        assert piece.length_upper_bound == 9.2 #(9.3 - 2 * 0.05)

        piece = Piece(rebar,Period(1,8))
        piece.practical = Period(1,9.25)
        piece.bend.end = .3
        mesh._set_piece_upper_bound(piece)
        assert piece.length_upper_bound == 9.2 #(9.3 - 2 * 0.05)

        piece = Piece(rebar,Period(1,8))
        piece.practical = Period(-.25,9.25)
        piece.bend.start = .3
        piece.bend.end = .3
        mesh._set_piece_upper_bound(piece)
        assert piece.length_upper_bound == 9.5 #(9.3 - 2 * 0.05)

class TestRound():
    def test_round_down(self, mesh, rebar):
        piece = Piece(rebar,Period(1,8))
        piece.practical = Period(0,8.96)
        piece.length_upper_bound = 9
        mesh._round_piece(piece)
        assert piece.shortest_piece_length == 9
    
    def test_round_up(self, mesh, rebar):
        piece = Piece(rebar,Period(1,8))
        piece.practical = Period(0,8.96)
        piece.length_upper_bound = 8.99
        mesh._round_piece(piece)
        assert piece.shortest_piece_length == 8.95


class TestUnifyPiece():
    def test_twp_piece(self, mesh, rebar):
        piece_1 = Piece(rebar,Period(1,4))
        piece_2 = Piece(rebar,Period(4,8))
        row = [piece_1, piece_2]
        mesh.additional_rebar = rebar
        is_unified = mesh._unify_row(row, "theoretical", )
        assert row[0].theoretical == Period(1,8) and is_unified
    
    def test_four_piece(self, mesh, rebar):
        piece_1 = Piece(rebar,Period(1,4))
        piece_2 = Piece(rebar,Period(4,6))
        piece_3 = Piece(rebar,Period(5,7))
        piece_4 = Piece(rebar,Period(6.5,8))
        row = [piece_1, piece_2, piece_3, piece_4]
        mesh.additional_rebar = rebar
        mesh._unify_row(row, "theoretical")
        assert row[0].theoretical == Period(1,8)
    
    def test_four_piece_splited(self, mesh, rebar):
        piece_1 = Piece(rebar,Period(0,4))
        piece_2 = Piece(rebar,Period(4,6))
        piece_3 = Piece(rebar,Period(6,7))
        piece_4 = Piece(rebar,Period(6.5,13))
        row = [piece_1, piece_2, piece_3, piece_4]
        mesh.additional_rebar = rebar
        mesh._unify_row(row, "theoretical")
        assert row[0].theoretical == Period(0,4)
        assert row[1].theoretical == Period(4,13)

class TestSetPieceExecutive():
    def test_no_bend_negative(self, mesh, piece_factory):
        piece = piece_factory(0,5,4)
        mesh._set_piece_executive(piece)
        assert piece.theoretical == Period(0.5, 4.5)
    
    def test_no_bend_positive_no_base(self, mesh, piece_factory):
        # exactly reach start 
        piece = piece_factory(1,5,4.95)
        mesh._set_piece_executive(piece)
        assert piece.executive == Period(0.05, 5)
        # reach start and has more to be added
        piece = piece_factory(1,5,5)
        mesh._set_piece_executive(piece)
        assert piece.executive == Period(0.05, 5.05)
        # exactly reach end
        piece = piece_factory(4,8,4.95)
        mesh._set_piece_executive(piece)
        assert piece.executive == Period(4, 8.95)
        # exactly reach end and has more to be added
        piece = piece_factory(4,8,5)
        mesh._set_piece_executive(piece)
        assert piece.executive == Period(3.95, 8.95)
        # doesn't reach end
        piece = piece_factory(3,7,5)
        mesh._set_piece_executive(piece)
        assert piece.executive == Period(2.5, 7.5)
    
    def test_no_bend_positive_no_bend_base(self, mesh, piece_factory):
        # reach start
        base = piece_factory(1,5,5)
        base.executive = Period(.6,5.5)
        piece = piece_factory(1,5,5)
        mesh._set_piece_executive(piece, base)
        assert piece.executive == Period(.6, 5.5)
        # reach end
        base = piece_factory(1,5,5)
        base.executive = Period(.5,6.5)
        piece = piece_factory(2,6,5)
        mesh._set_piece_executive(piece)
        assert piece.executive == Period(1.5, 6.5)
        # doesn't reach any of ends
        base = piece_factory(1,5,5)
        base.executive = Period(1.5,8.5)
        piece = piece_factory(3,7,5)
        mesh._set_piece_executive(piece)
        assert piece.executive == Period(2.5, 7.5)

    def test_no_bend_positive_start_bend_base(self, mesh, piece_factory):
        # reach end
        base = piece_factory(1,5,5)
        base.executive = Period(-.25,8)
        base.bend.start = .3
        piece = piece_factory(1,5,7)
        mesh._set_piece_executive(piece, base)
        assert piece.executive == Period(1, 8)
        # reach end
        base = piece_factory(1,5,7.25)
        base.executive = Period(-.25,7)
        base.bend.start = .3
        piece = piece_factory(2,6,7)
        mesh._set_piece_executive(piece, base)
        assert piece.executive == Period(-.25, 6.75)
        # increase length
        base = piece_factory(1,5,6.4)
        base.executive = Period(-.25,6.15)
        base.bend.start = .3
        piece = piece_factory(2,6,6.15)
        mesh._set_piece_executive(piece, base)
        assert piece.executive == Period(-.25, 6.15) and base.shortest_piece_length == piece.shortest_piece_length
        # doesn't reach any of ends , equal increase
        base = piece_factory(1,5,6.4)
        base.executive = Period(-.25,8)
        base.bend.start = .3
        piece = piece_factory(2,6,5)
        mesh._set_piece_executive(piece, base)
        assert piece.executive == Period(1.5, 6.5)
        # doesn't reach any of ends , but reaches start bound
        base = piece_factory(1,5,6.4)
        base.executive = Period(-.25,8)
        base.bend.start = .3
        piece = piece_factory(.1,6.1,6.3)
        mesh._set_piece_executive(piece, base)
        assert piece.executive == Period(0.05, 6.35)

    def test_no_bend_positive_end_bend_base(self, mesh, piece_factory):
        # reach start
        base = piece_factory(1,5,5)
        base.executive = Period(4.5,9.25)
        base.bend.end = .3
        piece = piece_factory(5,8,4)
        mesh._set_piece_executive(piece, base)
        assert piece.executive == Period(4.5, 8.5)
        # reach end
        base = piece_factory(1,5,5)
        base.executive = Period(4.5,9.25)
        base.bend.end = .3
        piece = piece_factory(7,8,3)
        mesh._set_piece_executive(piece, base)
        assert piece.executive == Period(6.25, 9.25) and piece.bend.end == .3
        # increase length
        base = piece_factory(3,9,6.4)
        base.executive = Period(2.85,9.25)
        base.bend.end = .3
        piece = piece_factory(3,7,6.15)
        mesh._set_piece_executive(piece, base)
        assert piece.executive == Period(2.85, 9.25) and piece.bend.end == .3
        # doesn't reach any of ends , equal increase
        base = piece_factory(1,5,8.25)
        base.executive = Period(1,9.25)
        base.bend.end = .3
        piece = piece_factory(3,7,5)
        mesh._set_piece_executive(piece, base)
        assert piece.executive == Period(2.5, 7.5)
        # doesn't reach any of ends , but reaches end bound
        base = piece_factory(1,5,8.25)
        base.executive = Period(1,9.25)
        base.bend.end = .3
        piece = piece_factory(2.9,8.9,6.3)
        mesh._set_piece_executive(piece, base)
        assert piece.executive == Period(2.65, 8.95)

    def test_start_bend(self, mesh, piece_factory):
        # decrease length
        piece = piece_factory(-0.25,5,4.25)
        piece.bend.start = 0.3
        mesh._set_piece_executive(piece)
        assert piece.executive == Period(-.25,4)
        # increase length
        piece = piece_factory(-0.25,5,8.25)
        piece.bend.start = 0.3
        mesh._set_piece_executive(piece)
        assert piece.executive == Period(-.25,8)
    
    def test_end_bend(self, mesh, piece_factory):
        # decrease length
        piece = piece_factory(4,9.25,4.25)
        piece.bend.end = 0.3
        mesh._set_piece_executive(piece)
        assert piece.executive == Period(5,9.25)
        # increase length
        piece = piece_factory(5,9.25,5.25)
        piece.bend.end = 0.3
        mesh._set_piece_executive(piece)
        assert piece.executive == Period(4,9.25)
    
    def test_both_bend(self, mesh, piece_factory):
        # decrease length
        piece = piece_factory(-0.25,9.25,9.25)
        piece.bend.end = 0.3
        piece.bend.start = 0.3
        mesh._set_piece_executive(piece)
        assert piece.executive == Period(-0.25,9)
        # increase length
        piece = piece_factory(-0.25,9.25,10)
        piece.bend.end = 0.3
        piece.bend.start = 0.3
        mesh._set_piece_executive(piece)
        assert piece.executive == Period(-0.25,9.25)
            

class TestTheoreticalToExecutive():
    def test_theoretical_to_executive(self, mesh, rebar):
        method = {
            "method": "MIN_RATIO",
            "min_ratio": 0.0018
        }
        mesh.set_typical_rebar(rebar, rebar, method)
        mesh.additional_rebar = rebar
        mesh._insert_additional(0.1)
        mesh._theoretical_to_executive()

class TestEffectiveDiagram():
    def test_effecitive_area_diagram(self, mesh, rebar):
        method = {
            "method": "MIN_RATIO",
            "min_ratio": 0.0018
        }
        mesh.set_typical_rebar(rebar, rebar, method)
        mesh.additional_rebar = rebar
        mesh._insert_additional(.1)
        mesh._theoretical_to_executive()
        mesh._get_effective_area_diagram()
        # assert False
    
    def test_resistance_moment_diagram(self, filled_mesh, rebar):
        diagram = filled_mesh.get_resistance_moment_diagram(
            widths= [1,1,1.2,3,4],
            stations= [0,5,6,8,9],
            fy= 40000,
            fc= 3000
        )
        # print(diagram)
        # assert False

        
        