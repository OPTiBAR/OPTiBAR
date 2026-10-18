import pytest
from optibar.core.components.strip import Strip
from optibar.core.io.input import InputInterpreter
from optibar.core.components.rebar import RebarType

LEVELS = ('top', 'bottom')

@pytest.fixture(scope="class")
def strip(input_interpreter : InputInterpreter):
    strip_dicts = input_interpreter.get_strips()
    return Strip(strip_dicts[0])
    

class TestStrip():
    def test_typical(self, strip):
        strip.set_side_cover(0.05)
        level = {
            'method': {'method': 'INTERVAL', 'value': 0.2},
            'typical_rebar_type': RebarType(20),
            'thermal_rebar_type': RebarType(16),
        }
        strip.set_typical_rebar({'top': level, 'bottom': level})

    def test_additional(self, strip):
        strip.set_additional_rebar(RebarType(25), .1)
    
    def test_shear(self, strip):
        strip.set_shear(.1)
        for zone in strip.get_shear_zones():
            assert zone.period.get_length() > .1
    
    def test_get_additional_pieces(self, strip: Strip):
        pieces = list(strip.get_additional_pieces())
        assert len(pieces) > 0
        for piece in pieces:
            assert piece.rebar.get_diameter_mm() == 25
            assert piece.theoretical.is_subset_of(piece.required)
    
    def test_get_typical_pieces(self, strip: Strip):
        piece_dict = strip.get_typical_pieces()
        for level in LEVELS:
            assert piece_dict[level]['number'] > 0
            diameter = 20 if piece_dict[level]['type'] == 'typical' else 16
            assert piece_dict[level]['piece'].rebar.get_diameter_mm() == diameter
    
    def test_get_resistance_moment(self, strip: Strip):
        moment_dict = strip.get_resistance_moment()
        for level in LEVELS:
            assert len(moment_dict[level]["stations"]) == len(moment_dict[level]["values"]) > 0
