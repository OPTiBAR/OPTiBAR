import pytest
from optibar_core.src.rebar import RebarType
from optibar_core.src.foundation import Foundation

class TestFoundation():
    def test_set_general(self, foundation):
        arrangment = {
            "method": "MIN_RATIO",
            "min_ratio": 0.0018
        }
        foundation.set_general_rebar(RebarType(20), RebarType(16), arrangment)
    def test_set_reinforcement(self, foundation):
        foundation.set_reinforcement_rebar(RebarType(25), .1)
    
    def test_set_shear_rebar(self, foundation: Foundation):
        foundation.set_shear_rebar(RebarType(18), .1, 2)
        # for strip_shear_zones in foundation.get_strip_shear_zones():
        #     for shear_zone in strip_shear_zones:
        #         print(shear_zone)
        # for shear_type in foundation.get_shear_types():
        #     print(shear_type)

    def test_set_length_type_num(self, foundation: Foundation):
        foundation.set_length_type_num(2,2)

    def test_get_reinforcement_subpieces(self, foundation: Foundation):
        strips = foundation.get_reinforcement_subpieces()
        # for strip in strips:
        #     for row in strip["top"]:
        #         for subpiece in row:
        #             print(subpiece)

    def test_get_general_subpieces(self, foundation: Foundation):
        strips = foundation.get_general_subpieces()
        # for strip in strips:
        #     for subpiece in strip["top"]["subpieces"]:
        #         print(subpiece)
        #     print(strip["top"]["number"])

    def test_get_shear_piece_list(self, foundation: Foundation):
        strips = foundation.get_shear_piece_list()
        # for strip in strips:
        #     print(f'diameter: {strip["rebar"].get_diameter_mm()}, "number": {strip["number"]}, "length": {strip["length"]}')

    
