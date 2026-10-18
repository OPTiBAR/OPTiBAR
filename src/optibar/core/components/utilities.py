import math

# float noise (e.g. 1.1 * 100 = 110.00000000000001) must not push a value a whole unit
PRECISION = 6

def round_up(length, round_unit):
    coeff = 1/round_unit
    return round(math.ceil(round(length * coeff, PRECISION))/coeff, PRECISION)

def round_down(length, round_unit):
    coeff = 1/round_unit
    return round(math.floor(round(length * coeff, PRECISION))/coeff, PRECISION)
