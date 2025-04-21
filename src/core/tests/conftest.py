import pytest
from optibar.src.components.period import Period
from optibar.src.components.piece import Piece,Bend
from optibar.src.components.rebar import Rebar, RebarType
from optibar.src.components.diagram import Diagram, Point
from optibar.src.components.config import Config
import pathlib
import json
from optibar.src.components.foundation import Foundation
from optibar.src.io.input import InputInterpreter
from optibar.src.io.output import Output


@pytest.fixture
def rebar():
    rebar_type = RebarType.T20
    rebar = Rebar(rebar_type, 1e-6, .85, "bottom")
    return rebar

@pytest.fixture
def piece_factory(rebar):
    def _factory(start, end):
        period = Period(start, end)
        piece = Piece(rebar, period)
        piece.practical = period
        piece.executive = period
        return piece
    return _factory

@pytest.fixture
def short_piece(rebar):
    theoretical =  Period(5,8)
    piece = Piece(rebar,theoretical)
    piece.practical = Period(4.5,8.5)
    piece.executive = Period(4,9)
    return piece

@pytest.fixture
def medium_piece(rebar):
    theoretical =  Period(5,16)
    piece = Piece(rebar,theoretical)
    piece.practical = Period(4.5,16.5)
    piece.executive = Period(4,17)
    return piece

@pytest.fixture
def long_piece(rebar):
    theoretical =  Period(5,18)
    piece = Piece(rebar,theoretical)
    piece.practical = Period(4.5,18.5)
    piece.executive = Period(4,19)
    return piece

@pytest.fixture
def very_long_piece(rebar):
    theoretical =  Period(5,25)
    piece = Piece(rebar,theoretical)
    piece.practical = Period(4.5,26)
    piece.executive = Period(4,27)
    return piece

# path = pathlib.Path(__file__).parent.joinpath('io', 'data', 'accdb')

@pytest.fixture(scope='class')
def input_interpreter():
    with open(pathlib.Path(__file__).parent.joinpath('data_files', 'parsed_data.json'), 'r') as f: 
        parsed_data = json.load(f)
        return InputInterpreter(parsed_data)


@pytest.fixture(scope="class")
def config(config_dict):
    return Config(config_dict)

@pytest.fixture(scope="class")
def foundation(input_intepreter):
    return Foundation(input_intepreter)

# @pytest.fixture(scope="class")
# def output(foundation_dict, foundation, config):
#     arrangment = {
#             "method": "MIN_RATIO",
#             "min_ratio": 0.0018
#         }
#     foundation.set_general_rebar(RebarType(20), RebarType(16), arrangment)
#     foundation.set_reinforcement_rebar(RebarType(25), .1)
#     foundation.set_shear_rebar(RebarType(18), .1, 2)
#     foundation.set_length_type_num(2,2)
#     return Output(foundation, foundation_dict, config)

