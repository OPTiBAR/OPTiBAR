import pytest
from optibar.core.components.period import Period
from optibar.core.components.piece import Piece,Bend
from optibar.core.components.rebar import Rebar, RebarType
from optibar.core.components.diagram import Diagram, Point
from optibar.core.components.config import Config
import pathlib
import json
from optibar.core.components.foundation import Foundation
from optibar.core.io.input import InputInterpreter
from optibar.core.io.output import Output


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
        piece.required = period
        piece.practical = period
        return piece
    return _factory

@pytest.fixture
def short_piece(rebar):
    theoretical =  Period(5,8)
    piece = Piece(rebar,theoretical)
    piece.required = Period(4.5,8.5)
    piece.practical = Period(4,9)
    return piece

@pytest.fixture
def medium_piece(rebar):
    theoretical =  Period(5,16)
    piece = Piece(rebar,theoretical)
    piece.required = Period(4.5,16.5)
    piece.practical = Period(4,17)
    return piece

@pytest.fixture
def long_piece(rebar):
    theoretical =  Period(5,18)
    piece = Piece(rebar,theoretical)
    piece.required = Period(4.5,18.5)
    piece.practical = Period(4,19)
    return piece

@pytest.fixture
def very_long_piece(rebar):
    theoretical =  Period(5,25)
    piece = Piece(rebar,theoretical)
    piece.required = Period(4.5,26)
    piece.practical = Period(4,27)
    return piece

SCHEMA_PATH = pathlib.Path(__file__).parent.parent.joinpath('schemas')


@pytest.fixture(scope='class')
def input_interpreter():
    with open(pathlib.Path(__file__).parent.joinpath('data_files', 'parsed_data.json'), 'r') as f: 
        parsed_data = json.load(f)
        return InputInterpreter(parsed_data)


@pytest.fixture(scope="class")
def config_dict():
    return {
        "diameter": {"additional": 25, "shear": 14, "thermal": 12, "typical": 18},
        "elimination": {"additional": 0.2, "shear": 2.0},
        "type_number": {"shear": 4, "stack": 2, "total": 20},
        "side_cover": 0.05,
        "typical_arrangement": {"method": "INTERVAL", "value": 0.2, "exceptions": []},
    }

@pytest.fixture(scope="class")
def config(config_dict):
    return Config(config_dict)

@pytest.fixture(scope="class")
def foundation(input_interpreter, config):
    foundation = Foundation(input_interpreter)
    foundation.run(config)
    return foundation

@pytest.fixture(scope="class")
def output(foundation):
    return Output(foundation)
