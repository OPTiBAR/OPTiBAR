from typing import override
from .utilities import round_down, round_up

class Period():
    def __init__(self,start=None, end=None):
        self.start = start
        self.end = end

    @override
    def __eq__(self, other):
        return round(self.start,3) == round(other.start,3) and round(self.end,3) == round(other.end,3)

    @override
    def __str__(self):
        return f"[{round(self.start,3)}, {round(self.end,3)}]"

    def get_length(self) -> float:
        if (self.start is None) or (self.end is None):
            raise ValueError("start and end should be assigned first.")
        return (self.end - self.start)

    def is_subset_of(self, other: Period) -> bool:
        """determines if this period is subset of the other period
        the inequalities are not strict

        Args:
            other (Period): other period

        Returns:
            bool: returns True if this one is subset if the other period
        """
        return (round_up(self.start,0.001) >= round_down(other.start,0.001)) and (round_down(self.end,0.001) <= round_up(other.end,0.001))

    def has_intersection_with(self, other: Period) -> bool:
        """determines if this period has intersection with the other period
        it is assumed that self.start < other.start

        Args:
            other (Period): other period

        Returns:
            bool: returns True if these two periods have intersection
        """
        if self.start > other.start:
            print(f'self: start {self.start} end {self.end} length {round(self.get_length(),3)}')
            print(f'other: start {other.start} end {other.end} length {round(other.get_length(),3)}')
        #     raise ValueError("START_ORDER:the first period should start befor the second one.")
        return (round_down(self.end,.001) >= round_up(other.start,0.001))
