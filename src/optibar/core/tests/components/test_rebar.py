from optibar.core.components.utilities import round_up
from optibar.core.components.rebar import Rebar, RebarType
import math


def test_area(rebar):
    assert rebar.get_area() == (20 * 20 * math.pi) / (4 * 1e6)

def test_calc_ld():
    fc = 3000 # ton/m^2
    fy = 40000 # ton/m^2
    to_mpa = 9.81 / 1000
    diameter = RebarType.T18.value
    ld_bottom_18 = round_up((diameter/1000)*((fy*to_mpa)/(math.sqrt(fc*to_mpa) * 2.1)),0.01)
    diameter = RebarType.T22.value
    ld_top_22 = round_up((diameter/1000)*((fy*to_mpa)/(math.sqrt(fc*to_mpa) * 1.7)) * 1.3, 0.01)
    assert (ld_bottom_18, ld_top_22) == (0.62, 1.22)
    assert ld_bottom_18 == Rebar.calc_ld(fc, fy, RebarType.T18, "bottom")
    assert ld_top_22 == Rebar.calc_ld(fc, fy, RebarType.T22, "top")

def test_overlap_length(rebar):
    assert rebar.get_bend_length() == .3

def test_get_diameter(rebar):
    assert rebar.get_diameter_mm() == 20

    