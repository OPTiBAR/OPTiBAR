import pytest
from optibar_core.src.components.strip import Strip
from optibar_core.src.io.input import InputInterpreter
from optibar_core.src.components.rebar import RebarType

@pytest.fixture(scope="class")
def strip(input_interpreter : InputInterpreter):
    strip_dicts = input_interpreter.get_strips()
    return Strip(strip_dicts[0])
    

class TestStrip():
    def test_typical(self, strip):
        arrangment = {
            "method": "MIN_RATIO",
            "min_ratio": 0.0018
        }
        strip.set_typical_rebar(RebarType(20), RebarType(16), arrangment)

    def test_additional(self, strip):
        strip.set_additional_rebar(RebarType(25), .1)
    
    def test_shear(self, strip):
        strip.set_shear(.1)
        shear_zones = strip.get_shear_zones()
        # for shear_zone in shear_zones:
        #     print(shear_zone)
    
    def test_get_additional_pieces(self, strip: Strip):
        pieces = strip.get_additional_pieces()
        # for piece in pieces:
        #     print(piece)
    
    def test_get_typical_pieces(self, strip: Strip):
        piece_dict = strip.get_typical_pieces()
        # print(piece_dict["top"]["piece"])
        # print(piece_dict["top"]["number"])
        # print(piece_dict["bottom"]["piece"])
        # print(piece_dict["bottom"]["number"])
    
    def test_get_resistance_moment(self, strip: Strip):
        moment_dict = strip.get_resistance_moment()
        # print(moment_dict["top"]["stations"])
        # print(moment_dict["top"]["values"])
    


    
