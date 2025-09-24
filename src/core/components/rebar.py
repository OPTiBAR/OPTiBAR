from enum import Enum
import math
from typing import override
from .utilities import round_up
from core.setting import (
    REBAR_90_BEND_COEFFICIENT,
    REBAR_135_BEND_COEFFICIENT,
    REBAR_BEND_ROUND_UNIT,
    REBAR_LD_ROUND_UNIT,
    REBAR_OVERLAP_ROUND_UNIT
)

class Rebar():
    special_lengths = None

    def __init__(self, rebar_type: RebarType, fc: float = None, fy: float = None, level: str = None) -> None:
        self.rebar_type = rebar_type
        if not any((fc is None, fy is None, level is None)):
            self._ld_length = Rebar.calc_ld(fc, fy, rebar_type, level)
        else:
            self._ld_length = None

    @classmethod
    def calc_ld(cls, fc: float, fy: float, rebar_type: RebarType, level: str) -> float:
        """ level should be "top" or "bottom" """
        if cls.special_lengths is not None:
            return cls.special_lengths['ld'][level][cls.special_lengths['diameters'].index(rebar_type.value)]
        ld = None
        diameter = rebar_type.value
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

    @classmethod
    def calc_bend_legth(cls, rebar_type: RebarType, degree: float) -> float:
        if cls.special_lengths is not None:
            return cls.special_lengths['bend']['B'+str(degree)][cls.special_lengths['diameters'].index(rebar_type.value)]
        # divide by 1000 to convert mm to m
        if degree == 90:
            return round_up((rebar_type.value/1000) * REBAR_90_BEND_COEFFICIENT, REBAR_BEND_ROUND_UNIT)
        elif degree == 135:
            return round_up((rebar_type.value/1000) * REBAR_135_BEND_COEFFICIENT, REBAR_BEND_ROUND_UNIT)
        else:
            raise ValueError("degree should be 90 or 135")


    @classmethod
    def calc_overlap_length(cls, fc: float, fy: float, rebar_type: RebarType, level: str) -> None:
        if cls.special_lengths is not None:
            return cls.special_lengths['overlap'][level][cls.special_lengths['diameters'].index(rebar_type.value)]
        return round_up(1.3 * Rebar.calc_ld(fc, fy, rebar_type, level), REBAR_OVERLAP_ROUND_UNIT)

    def get_area(self) -> float:
        diameter: int = self.rebar_type.value
        return (math.pi * (diameter ** 2))/(4 * 1e6)

    def get_ld(self) -> float:
        return self._ld_length

    def get_overlap_length(self) -> float:
        return round_up(self._ld_length * 1.3, REBAR_OVERLAP_ROUND_UNIT)

    def get_bend_length(self, degree: float = 90) -> float:
        return Rebar.calc_bend_legth(self.rebar_type, degree)

    def get_diameter_mm(self) -> int:
        return self.rebar_type.value

    @override
    def __eq__(self, o: object) -> bool:
        return all((
            self.rebar_type == o.rebar_type,
            self._ld_length == o._ld_length
        ))

class RebarType(Enum):
    T8 = 8
    T10 = 10
    T12 = 12
    T14 = 14
    T16 = 16
    T18 = 18
    T20 = 20
    T22 = 22
    T25 = 25
    T28 = 28
    T32 = 32
