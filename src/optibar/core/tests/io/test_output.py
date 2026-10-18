
from pprint import pp, pprint
from jsonschema import validate, Draft7Validator
import json
import pathlib

import jsonschema

class TestOutput():
    def test_areas(self, output):
        areas = output._Output__get_areas()
        # pprint(areas)

    def test_columns(self, output):
        columns = output._Output__get_columns()
        # pprint(columns)
        
    def test_material(self, output):
        material = output._Output__get_material()
        # pprint(material)
    
    def test_covers(self, output):
        covers = output._Output__get_covers()
        # pprint(covers)
    
    def test_rebars(self, output):
        rebars = output._Output__get_rebars()
        # pprint(rebars)
    
    def test_length_type(self, output):
        length_type = output._Output__get_length_type()
        # pprint(length_type)
    
    def test_technical_spec(self, output):
        technical_spec = output._Output__get_technical_spec()
        # pprint(technical_spec)

    def test_general_thermal_piece_list(self, output):
        piece_dict = output._Output__get_general_thermal_piece_list()
        # pprint(piece_dict)
    
    def test_reinforcement_piece_list(self, output):
        piece_list = output._Output__get_reinforcement_piece_list()
        # pprint(piece_list)

    def test_shear_piece_list(self, output):
        piece_list = output._Output__get_shear_piece_list()
        # pprint(piece_list)
    
    def test_pieces(self, output):
        piece_list = output._Output__get_pieces()
        # print("\n")
        # pprint(piece_list)
    
    def test_concrete_volume(self, output):
        volume = output._Output__get_concrete_volume()
        # print(volume)
    
    def test_reinforcement_mass(self, output):
        mass_dict = output._Output__get_reinforcement_mass()
        # pprint(mass_dict)
    
    def test_shear_mass(self, output):
        mass = output._Output__get_shear_mass()
        # print(mass)
    
    def test_general_thermal_mass(self, output):
        mass_dict = output._Output__get_general_thermal_mass()
        # pprint(mass_dict)
    
    def test_rebar_mass(self, output):
        mass_dict = output._Output__get_rebar_mass()
        # pprint(mass_dict)

    def test_summary(self, output):
        summary_dict = output._Output__get_summary()
        # pprint(summary_dict)
    
    def test_shear_types(self, output):
        shear_types = output._Output__get_shear_types()
        # pprint(shear_types)
    
    def test_strips_name(self, output):
        names = output._Output__get_strips_name()
        # pprint(names)
    
    def test_strips_covers(self, output):
        strips_covers = output._Output__get_strips_covers()
        # pprint(strips_covers)
    
    def test_strips_midline(self, output):
        midlines = output._Output__get_strips_midline()
        # pprint(midlines)
    
    def test_strip_geometry(self, output):
        strips = output._Output__get_strips_geometry()
        # print("\n")
        # pprint(strips)
    
    def test_strips_general_mesh(self, output):
        strips = output._Output__get_strips_general_mesh()
        # pprint(strips)
    
    def test_strips_reinforcement_mesh(self, output):
        strips = output._Output__get_strips_reinforcement_mesh()
        # pprint(strips)
    
    def test_strips_mesh(self, output):
        strips = output._Output__get_strips_mesh()
        # pprint(strips)
    
    def test_strips_shear_zones(self, output):
        strips = output._Output__get_strips_shear_zones()
        # pprint(strips)
    
    def test_strips_moment(self, output):
        strips = output._Output__get_strips_moment()
        # pprint(strips)
    
    def test_strips(self, output):
        strips = output._Output__get_strips()
        # pprint(strips)
    
    def test_grid(self, output):
        grid = output._Output__get_grid()
        # pprint(grid)
    
    def test_output(self, output):
        out = output.get_output()
        with open(str(pathlib.Path('optibar').joinpath('src', 'schemas', 'output.json').absolute()), 'r') as file:
            schema = json.load(file)
        v = Draft7Validator(schema=schema)
        errors = sorted(v.iter_errors(out), key=lambda e: e.path)
        for error in errors:
            print(error.message)
            print(error.path)
        # pprint(out)
        with open('data.json', 'w') as output_file:
            json.dump(out, output_file, indent=4)
        assert len(errors) == 0