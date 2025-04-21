from optibar_core.src.io.input import InputInterpreter
from copy import deepcopy

class TestInput():
    def test_area_polygons(self, input_interpreter):
        for polygon in input_interpreter._area_polygons:
            pass
            # print(polygon)
        # assert False
    def test_strip_polygons(self, input_interpreter):
        for polygon in input_interpreter._strip_polygons:
            pass
            # print(polygon)
        # assert False
    def test_strip_props(self, input_interpreter):
        for prop in input_interpreter._strip_props:
            pass
            # print(prop)
        # assert False
        
    def test_strip_line_strings(self, input_interpreter):
        for line_string in input_interpreter._strip_line_strings:
            pass
            # print(line_string)
        # assert False
    
    def test_strip_column_sides(self, input_interpreter):
        for column_sides in input_interpreter._get_strip_column_sides():
            pass
            # print(column_sides)
        # assert False
    def test_strip_trim_sides(self, input_interpreter):
        for column_sides in input_interpreter._get_strip_trim_sides():
            pass
        #     print(column_sides)
        # assert False
    
    def test_get_strips(self, input_interpreter):
        for strip in input_interpreter.get_strips():
            pass
            # pprint(strip)
        # assert False
