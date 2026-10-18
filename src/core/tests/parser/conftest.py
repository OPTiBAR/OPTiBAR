import pytest
import pathlib
from core.parser.parse import V16Parser

DATA_PATH = pathlib.Path(__file__).parent.joinpath('data_files')


def open_parser(*parts):
    parser = V16Parser(str(DATA_PATH.joinpath(*parts)))
    yield parser
    parser.close()

@pytest.fixture(scope='class')
def tonf_m_parser():
    yield from open_parser('tonf_m.accdb')

@pytest.fixture(scope='class')
def tonf_m_mdb_parser():
    yield from open_parser('tonf_m.mdb')

@pytest.fixture(scope='class')
def error_fc_parser():
    yield from open_parser('Error_fc.accdb')

@pytest.fixture(scope='class')
def error_fy_parser():
    yield from open_parser('Error_fy.accdb')
