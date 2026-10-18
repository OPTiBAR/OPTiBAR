import json
import pytest
from jsonschema import Draft7Validator
from optibar.core.components.config import Config
from optibar.core.components.rebar import RebarType
from optibar.core.tests.conftest import SCHEMA_PATH


@pytest.fixture
def config_with_exceptions(config_dict):
    exceptions = [
        {"strip_name": "CSA2", "level": "top", "method": "COUNT", "value": 12, "diameter": 14},
        {"strip_name": "CSA2", "level": "bottom", "method": "INTERVAL", "value": .25, "diameter": 16},
        {"strip_name": "CSA3", "level": "top", "method": "INTERVAL", "value": .2, "diameter": 16},
    ]
    return dict(config_dict, typical_arrangement=dict(config_dict["typical_arrangement"], exceptions=exceptions))


def test_schema(config_with_exceptions):
    with open(SCHEMA_PATH.joinpath('config.json'), 'r') as file:
        schema = json.load(file)
    errors = [f'{list(error.path)}: {error.message}' for error in Draft7Validator(schema).iter_errors(config_with_exceptions)]
    assert errors == []


def test_config(config_with_exceptions):
    config = Config(config_with_exceptions)
    assert config.typical_rebar_type == RebarType(18)
    assert config.additional_rebar_type == RebarType(25)
    assert config.thermal_rebar_type == RebarType(12)
    assert config.shear_rebar_type == RebarType(14)
    assert (config.total_type_number, config.stack_type_number, config.shear_type_number) == (20, 2, 4)
    assert (config.reinfordement_elimination, config.shear_elimination) == (0.2, 2.0)
    assert config.side_cover == 0.05
    assert config.special_lengths is None
    assert config.typical_arrangement == {
        "method": "INTERVAL",
        "value": 0.2,
        "exceptions": {
            "CSA2": {
                "top": {"method": "COUNT", "value": 12, "diameter": RebarType(14)},
                "bottom": {"method": "INTERVAL", "value": .25, "diameter": RebarType(16)},
            },
            "CSA3": {
                "top": {"method": "INTERVAL", "value": .2, "diameter": RebarType(16)},
            },
        },
    }


def test_no_exceptions(config_dict):
    config_dict = dict(config_dict, typical_arrangement={"method": "COUNT", "value": 10})
    assert Config(config_dict).typical_arrangement["exceptions"] == {}
