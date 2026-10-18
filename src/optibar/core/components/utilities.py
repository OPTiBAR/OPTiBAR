import math

def round_up(length, round_unit):
    coeff = 1/round_unit
    return math.ceil(length * coeff)/coeff

def round_down(length, round_unit):
    coeff = 1/round_unit
    return math.floor(length * coeff)/coeff