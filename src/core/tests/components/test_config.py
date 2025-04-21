from optibar_core.src.components.config import Config
from optibar_core.src.components.rebar import RebarType
import pathlib
import pytest
from jsonschema import Draft7Validator
import json 


@pytest.fixture(scope="class")
def config_dict():
    return {
        "diameter": {
            "additional": 25,
            "typical": 20,
            "thermal": 14,
            "shear": 16
        },
        "type_number": {
            "total": 15,
            "stack": 3,
            "shear": 4, 
        },
        "elimination": {
            "additional": .1,
            "shear": .2
        },
        "typical_arrangement": {
            "method": "INTERVAL",
            "value": .2,
            "exceptions": [
                {
                    "strip_name": "CSA2",
                    "method": "COUNT",
                    "value": 12,
                    "diameter": 14,
                },
                {
                    "strip_name": "CSA3",
                    "method": "INTERVAL",
                    "value": .2,
                    "diameter": 16,
                }
            ]
        }
    }

def test_config(config_dict):
    with open(str(pathlib.Path('optibar').joinpath('src', 'schemas', 'config.json').absolute()), 'r') as file:
        schema = json.load(file)
    v = Draft7Validator(schema=schema)
    errors = sorted(v.iter_errors(config_dict), key=lambda e: e.path)
    for error in errors:
        print(error.message)
        print(error.path)
    assert len(errors) == 0
    config = Config(config_dict)
    assert config.typical_arrangement == {
        "method": "INTERVAL",
        "value": .2
    }
    assert config.reinfordement_elimination == .1 
    assert config.shear_elimination == .2
    assert config.total_type_number == 15
    assert config.stack_type_number == 3
    assert config.shear_type_number == 4
    assert config.additional_rebar_type == RebarType(25)
    assert config.typical_rebar_type == RebarType(20)
    assert config.thermal_rebar_type == RebarType(14)
    assert config.shear_rebar_type == RebarType(16)
    assert config.typical_exceptions == [
        {'name': 'CSA2', 'method': 'COUNT', 'value': 12, 'diameter': 14},
        {'name': 'CSA3', 'method': 'INTERVAL', 'value': 0.2, 'diameter': 16}
    ]