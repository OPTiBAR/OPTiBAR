import pytest
from optibar_core.src.components.diagram import Diagram, Point
from optibar_core.src.components.period import Period

@pytest.fixture(scope="class")
def diagram():
    stations = list(range(10))
    areas = [3, 0, 0, 0, 5, 4, 3, 1, 0, 4]
    return Diagram(stations, areas)

class TestBasicOperations():
    def test_get_periods_before(self, diagram):
        periods = diagram.get_periods()
        assert periods == [Period(0,1), Period(3,9)]
    
    def test_max_point_before(self, diagram):
        assert diagram.get_max_point(Period(3.2,5)) == Point(4,5)
        assert diagram.get_max_point(Period(4.5,7)) == Point(4.5,4.5)

    def test_reduce(self, diagram):
        areas = diagram.get_values()
        diagram._reduce(1)
        reducted_areas = diagram.get_values()
        assert list(map(lambda area: area-1, areas)) == reducted_areas
    
    def test_interpolation_zero_line_one(self):
        point_1 = Point(5, 3)
        point_2 = Point(8, -6)
        assert Diagram._interpolate_zero_line(point_1, point_2) == Point(6,0)
    
    def test_interpolation_zero_line_two(self):
        point_1 = Point(5, -6)
        point_2 = Point(8, 3)
        assert Diagram._interpolate_zero_line(point_1, point_2) == Point(7,0)
    
    def test_add_intersection_point(self, diagram):
        diagram._add_intersection_points()
        stations = [0,2/3,1,2,3,3.2,4,5,6,7,8,8.25,9]
        areas = [2, 0, -1, -1, -1, 0, 4, 3, 2, 0, -1, 0, 3]
        checks = (
            stations == diagram.get_stations(),
            areas == diagram.get_values()
        )
        assert all(checks)
    def test_increase_nagative_points(self, diagram):
        diagram._increase_nagative_points()
        stations = [0,2/3,1,2,3,3.2,4,5,6,7,8,8.25,9]
        areas = [2, 0, 0, 0, 0, 0, 4, 3, 2, 0, 0, 0, 3]
        checks = (
            stations == diagram.get_stations(),
            areas == diagram.get_values()
        )
        assert all(checks)
    
    def test_remove_consecutive_zeros(self, diagram):
        diagram._remove_consecutive_zeros()
        stations = [0,2/3,3.2,4,5,6,7,8.25,9]
        areas = [2, 0, 0, 4, 3, 2, 0, 0, 3]
        checks = (
            stations == diagram.get_stations(),
            areas == diagram.get_values()
        )
        assert all(checks)

    def test_get_periods_after(self, diagram):
        periods = diagram.get_periods()
        assert periods == [Period(0,2/3), Period(3.2,7), Period(8.25,9)]


class TestSideDist():
    @pytest.fixture(scope="class")
    def diagram_zero_start_end(self):
        stations = list(range(9))+[12]
        areas = [0, 0, 4, 5, 6, 5, 4, 1, 0, 0]
        return Diagram(stations, areas)
    def test_side_def(self, diagram_zero_start_end):
        assert  diagram_zero_start_end.get_side_distance() == 4

class TestMiddleDist():
    def test_get_middle_distance_before(self, diagram):
        diagram._remove_consecutive_zeros()
        assert diagram.get_middle_distance() == 2
    
    def test_get_middle_distance_after(self, diagram):
        diagram._reduce(2)
        diagram._add_intersection_points()
        diagram._increase_nagative_points()
        diagram._remove_consecutive_zeros()
        assert diagram.get_middle_distance() == 3.4 - 1/3

class TestBounds():
    def test_get_bounds(self, diagram):
        assert diagram.get_bounds() == Period(0,9)

class TestIsPositve():
    def test_is_postive_before(self, diagram):
        assert diagram.is_positive()
    
    def test_is_postive_after(self, diagram):
        diagram._reduce(5)
        diagram._add_intersection_points()
        diagram._increase_nagative_points()
        diagram._remove_consecutive_zeros()
        assert not diagram.is_positive()

class TestInsert():
    def test_insert(self, diagram):
        diagram._insert(1)
        stations = [0,2/3,3.2,4,5,6,7,8.25,9]
        areas = [2, 0, 0, 4, 3, 2, 0, 0, 3]
        checks = (
            stations == diagram.get_stations(),
            areas == diagram.get_values()
        )
        assert all(checks)
class TestInsertGeneral():
    def test_insert_general(self, diagram):
        diagram.insert_typical(1)
        stations = [0,2/3,3.2,4,5,6,7,8.25,9]
        areas = [2, 0, 0, 4, 3, 2, 0, 0, 3]
        checks = (
            stations == diagram.get_stations(),
            areas == diagram.get_values()
        )
        assert all(checks)

class TestInsertAdditional():
    def test_insert_additional(self, diagram):
        periods = diagram.insert_additional(1)
        stations = [0,2/3,3.2,4,5,6,7,8.25,9]
        areas = [2, 0, 0, 4, 3, 2, 0, 0, 3]
        checks = (
            stations == diagram.get_stations(),
            areas == diagram.get_values(),
            periods == [Period(0,1), Period(3,9)]
        )
        assert all(checks)

class TestEffective():
    def test_increase_area(self):
        stations = [0,10]
        areas = [0,0]
        diagram = Diagram(stations, areas)
        diagram.increase_area(
            bends = {"start":False, "end":False},
            stations = [1,2,5,6],
            value= 1
        )
        diagram.increase_area(
            bends = {"start":True, "end":False},
            stations = [3,5],
            value= 2
        )
        diagram.increase_area(
            bends = {"start":False, "end":True},
            stations = [5,6],
            value= 3
        )
        diagram.increase_area(
            bends = {"start":True, "end":True},
            stations = [],
            value= 1
        )
        assert diagram.get_stations() == [0,1,2,3,5,6,10]
        assert diagram.get_values() == [3,3,4,4,2,4,4]

class TestTrimPeriod():
    def test_trim_period(self, diagram):
        diagram.trim_period(Period(3.2, 5.3))
        assert diagram.get_stations() == [0,1,2,3,3.2,3.221,5.279,5.3,6,7,8,9]
        assert diagram.get_values() == [3,0,0,0,1.0000000000000009, 0,0,0.08737864077669863,3,1,0,4]

class TestLinearizePeriod():
    def test_linearize_period(self, diagram):
        diagram.linearize_period(Period(2,5.5))
        assert diagram.get_stations() == [0, 1, 2, 5.5, 6, 7, 8, 9]
        assert diagram.get_values() == [3, 0, 0, 3.5, 3, 1, 0, 4]

