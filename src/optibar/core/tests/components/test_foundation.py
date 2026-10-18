import math
import pytest
from optibar.core.components.config import Config
from optibar.core.components.foundation import Foundation
from optibar.core.io.input import InputInterpreter

LEVELS = ('top', 'bottom')


class TestFoundation():
    def test_run(self, foundation: Foundation):
        assert foundation.errors == {}
        assert foundation.config is not None

    def test_shear_types(self, foundation: Foundation):
        shear_types = foundation.get_shear_types()
        assert 0 < len(shear_types) <= 4
        for shear_type in shear_types:
            assert shear_type.rebar.get_diameter_mm() == 14

    def test_strip_shear_zones(self, foundation: Foundation):
        for zones in foundation.get_strip_shear_zones():
            for zone in zones:
                assert zone.shear_type in foundation.get_shear_types()

    def test_additional_subpieces(self, foundation: Foundation):
        strips = foundation.get_additional_subpieces()
        assert len(strips) == len(foundation._strips)
        for strip in strips:
            for level in LEVELS:
                for row in strip[level]:
                    for subpiece in row:
                        assert subpiece.rebar.get_diameter_mm() == 25
                        assert subpiece.practical.get_length() > 0

    def test_typical_subpieces(self, foundation: Foundation):
        for strip in foundation.get_typical_subpieces():
            for level in LEVELS:
                assert strip[level]['type'] in ('typical', 'thermal')
                assert strip[level]['number'] > 0
                assert len(strip[level]['subpieces']) > 0

    def test_shear_piece_list(self, foundation: Foundation):
        piece_list = foundation.get_shear_piece_list()
        assert len(piece_list) > 0
        for piece in piece_list:
            assert piece['number'] > 0 and piece['length'] > 0

    def test_total_type_number(self, foundation: Foundation):
        """the practical lengths of the additional pieces use at most the configured number of types"""
        lengths = {
            (subpiece.rebar.get_diameter_mm(), round(subpiece.practical.get_length(), 2))
            for strip in foundation.get_additional_subpieces()
            for level in LEVELS for row in strip[level] for subpiece in row
        }
        assert len(lengths) <= foundation.config.total_type_number

    def test_warnings(self, foundation: Foundation):
        assert set(foundation.warnings) <= {'min_gap', 'max_gap', 'min_ratio', 'excess_stack'}


def test_not_enough_types(input_interpreter: InputInterpreter, config_dict):
    config = Config(dict(config_dict, type_number={'shear': 4, 'stack': 1, 'total': 1}))
    foundation = Foundation(input_interpreter)
    foundation.run(config)
    assert foundation.errors['total_type_num']['num'] == 1
    assert foundation.errors['total_type_num']['min_feasible_num'] > 1


def test_exception_levels(input_interpreter: InputInterpreter, config_dict):
    """a strip exception applies its own method and diameter to the level it names only"""
    name = input_interpreter.get_strips()[0]['name']
    exceptions = [{'strip_name': name, 'level': 'top', 'method': 'COUNT', 'value': 7, 'diameter': 20}]
    arrangement = dict(config_dict['typical_arrangement'], exceptions=exceptions)
    foundation = Foundation(input_interpreter)
    foundation.run(Config(dict(config_dict, typical_arrangement=arrangement)))
    interval_num = lambda mesh: math.ceil(round(mesh.section.width, 2) / 0.2)
    strip = foundation._strips[0]
    top, bottom = strip._top_mesh, strip._bottom_mesh
    assert top.typical_type == bottom.typical_type == 'typical'
    assert (top.typical_rebar_num, top.typical_rebar.get_diameter_mm()) == (7, 20)
    assert (bottom.typical_rebar_num, bottom.typical_rebar.get_diameter_mm()) == (interval_num(bottom), 18)
    for strip in foundation._strips[1:]:
        for mesh in (strip._top_mesh, strip._bottom_mesh):
            if mesh.typical_type == 'typical':
                assert (mesh.typical_rebar_num, mesh.typical_rebar.get_diameter_mm()) == (interval_num(mesh), 18)
