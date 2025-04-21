from optibar_core.src.components.period import Period
from optibar_core.src.components.shear import ShearZone, ShearType
from optibar_core.src.optimization.shear import ShearOptimization
import pytest
import math

@pytest.fixture
def shear_zone_factory():
    def _factory(start, end , density):
        return ShearZone(Period(start,end), density, 1)
    return _factory

@pytest.fixture
def shear_type_factory(rebar):
    def _factory(interval, number, id):
        return ShearType(rebar, interval, number, id)
    return _factory

def test_shear_zone_eq(shear_zone_factory):
        sz1 = shear_zone_factory(0,5,1)
        sz2 = shear_zone_factory(0,5,1)
        sz3 = shear_zone_factory(0,5,2)
        assert sz1 == sz2
        assert sz1 != sz3

class TestShearType():
    def test_shear_type_eq(self, shear_type_factory):
        st1 = shear_type_factory(.3, 3, 1)
        st2 = shear_type_factory(.3, 3, 2)
        assert st1 == st2
    def test_get_density(self, shear_type_factory):
        st = shear_type_factory(.3, 3, 1)
        assert st.get_density() == st.number * st.rebar.get_area()/st.interval

class TestShearOptimization():
    def test_shear_optimization(self, rebar, shear_zone_factory, shear_type_factory):
        shear_zones = [
            shear_zone_factory(0,2,math.pi * 1e-4 * 10),
            shear_zone_factory(3,3.1,math.pi * 1e-4 * 3),
            shear_zone_factory(6,7,math.pi * 1e-4 * 2),
            shear_zone_factory(9,10.5,math.pi * 1e-4 * 10),
        ]
        so = ShearOptimization(rebar, .4, shear_zones, 2)
        so.run()
        so.get_shear_types() == [
            ShearType(rebar, .4, 1, 1),
            ShearType(rebar, .2, 2, 2),
        ]
        sorted_shear_zones = so._shear_zones
        assert all((
            sorted_shear_zones[0].shear_type.id == 1,
            sorted_shear_zones[1].shear_type.id == 2,
            sorted_shear_zones[2].shear_type.id == 2,
            sorted_shear_zones[3].shear_type.id == 2,
        ))

