import pathlib
import os

# DOMAIN = 'http://192.168.1.100:8000/'
# DOMAIN = 'http://10.0.2.2:8000/'

DOMAIN = 'https://api.optibar.ir/'

REBAR_LIST = (8,10,12,14,16,18,20,22,25,28,32)

# REBAR
REBAR_90_BEND_COEFFICIENT = 13.7
REBAR_135_BEND_COEFFICIENT = 11
REBAR_BEND_ROUND_UNIT = 0.05
REBAR_LD_ROUND_UNIT = 0.01
REBAR_OVERLAP_ROUND_UNIT = 0.05
STEEL_DENSITY = 7.850 # ton/m^3

STORAGE_PATH = pathlib.Path(os.getenv('AppData')).joinpath('OPTIBAR')


CONTACTS = {
    'telegram': 'https://t.me/optibar_contact',
    'whatsapp': 'https://wa.me/989025738993',
    'instagram': 'https://www.instagram.com/optibar.ir/',
    'email': DOMAIN + 'contacts/email/',
    'linkedin': 'https://www.linkedin.com/company/optibar-cad',
    'telephone': DOMAIN + 'contacts/telephone/',
}


VERSION = '0.2.2'