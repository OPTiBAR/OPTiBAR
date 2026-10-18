from typing import override
from .period import Period
from .rebar import Rebar

class ShearZone():
    def __init__(self, period: Period, steel_density: float, thickness: float) -> None:
        self.period = period
        self.steel_density = steel_density
        self.shear_type = None
        self.thickness = thickness

    @override
    def __eq__(self, o: object) -> bool:
        return all((
            self.period == o.period,
            self.steel_density == o.steel_density,
            self.shear_type == o.shear_type
        ))

    @override
    def __str__(self) -> str:
        return f"ShearZone: [period: {str(self.period)}, density: {self.steel_density}, shear_type: {None if self.shear_type is None else self.shear_type.id}]"

class ShearType():
    def __init__(self, rebar: Rebar, interval: float, number: int, id:int) -> None:
        self.id = id
        self.rebar = rebar
        self.interval = interval
        self.number = number

    def get_density(self) -> float:
        return self.number * self.rebar.get_area()/self.interval

    @override
    def __eq__(self, other: object) -> bool:
        return all((
            self.rebar == other.rebar,
            self.interval == other.interval,
            self.number == other.number
        ))

    @override
    def __str__(self) -> str:
        return f"ShearType: [rebar_size: {self.rebar.get_diameter_mm()}, interval: {self.interval}, number: {self.number}, id: {self.id}]"
