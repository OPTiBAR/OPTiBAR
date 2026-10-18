import pathlib
from importlib.metadata import version, PackageNotFoundError

REBAR_LIST = (8,10,12,14,16,18,20,22,25,28,32)

IMAGES_PATH = pathlib.Path(__file__).parent.joinpath('data', 'images')

DOCS_URL = 'https://optibar.readthedocs.io/'
REPO_URL = 'https://github.com/OPTiBAR/OPTiBAR'

try:
    VERSION = version('optibar')
except PackageNotFoundError: # running from a source tree that isn't installed
    VERSION = 'dev'
