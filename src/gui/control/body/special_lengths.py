import math
from typing import List,Dict

def round_up(length, round_unit):
    coeff = 1/round_unit
    return math.ceil(length * coeff)/coeff

from src.setting import (
    REBAR_90_BEND_COEFFICIENT,
    REBAR_135_BEND_COEFFICIENT,
    REBAR_BEND_ROUND_UNIT,
    REBAR_LD_ROUND_UNIT,
    REBAR_OVERLAP_ROUND_UNIT,
    REBAR_LIST
)


class Rebar():
    @staticmethod
    def calc_ld(fc: float, fy: float, rebar_diameter: int, level: str) -> float:
        """ level should be "top" or "bottom" """
        ld = None
        diameter = rebar_diameter
        if diameter < 20:
            ld = (diameter/1000)*((fy*9.81/1000)/(math.sqrt(fc*9.81/1000) * 2.1))
        else:
            ld = (diameter/1000)*((fy*9.81/1000)/(math.sqrt(fc*9.81/1000) * 1.7))
        if level == "top" :
            ld *= 1.3
        elif level == "bottom" :
            pass
        else:
            raise ValueError("level should be top or bottom")
        return round_up(ld, REBAR_LD_ROUND_UNIT)

    @staticmethod
    def calc_bend_legth( rebar_diameter: int, degree: float) -> float:
        # divide by 1000 to convert mm to m
        if degree == 'B90':
            return round_up((rebar_diameter/1000) * REBAR_90_BEND_COEFFICIENT, REBAR_BEND_ROUND_UNIT)
        elif degree == 'B135':
            return round_up((rebar_diameter/1000) * REBAR_135_BEND_COEFFICIENT, REBAR_BEND_ROUND_UNIT)
        else:
            raise ValueError("degree should be 90 or 135")

    @staticmethod
    def calc_overlap_length(fc: float, fy: float, rebar_diameter: int, level: str) -> None:
        return round_up(1.3 * Rebar.calc_ld(fc, fy, rebar_diameter, level), REBAR_OVERLAP_ROUND_UNIT)
    
    def get_values(fc: float, fy: float):
        output = {
            'ld': {
                'top':{},
                'bottom': {},
            },
            'overlap': {
                'top': {},
                'bottom': {},
            },
            'bend': {
                'B90': {},
                'B135': {},
            }
        }
        for level in output['ld']:
            for d in REBAR_LIST:
                ld = Rebar.calc_ld(fc, fy, d, level)
                output['ld'][level][d] = ld
        
        for level in output['overlap']:
            for d in REBAR_LIST:
                overlap = Rebar.calc_overlap_length(fc, fy, d, level)
                output['overlap'][level][d] = overlap
        
        for degree in output['bend']:
            for d in REBAR_LIST:
                bend = Rebar.calc_bend_legth(d, degree)
                output['bend'][degree][d] = bend
        return output
    
    @staticmethod
    def calc_automatic(ld_bottom: List[float]) -> Dict[str, Dict[str, Dict[int, int]]]:
        output = {
            'ld': {
                'top': {}
            },
            'overlap': {
                'bottom': {},
                'top': {}
            }
        }
        for i,rebar in enumerate(REBAR_LIST):
            output['ld']['top'][rebar] = round_up(1.3 * ld_bottom[i], REBAR_LD_ROUND_UNIT)
            output['overlap']['bottom'][rebar] = round_up(1.3 * ld_bottom[i], REBAR_OVERLAP_ROUND_UNIT)
            output['overlap']['top'][rebar] = round_up(1.3 * 1.3 * ld_bottom[i], REBAR_OVERLAP_ROUND_UNIT)
        return output


        
