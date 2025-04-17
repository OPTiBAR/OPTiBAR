from __future__ import annotations
from enum import Enum
from typing import List, NoReturn
from core.src.components.collections import Stack
from core.src.components.period import Period

class StackMinimization():
    """gets a list of lengths in ascending order and two lengths d and Ld.
    and returns the selected lengths and status of the domination.
    """
    def __init__(self, lengths: List[float], d_length: float, ld_length: float):
        """[summary]

        Args:
            lengths (List[float]): list of lengths in ascending order
            d_length (float): efficient depth of foundation
            ld_length (float): Ld length
        """
        self.d_length = d_length
        self.ld_length = ld_length
        self.lengths = lengths # ascending
        self._run()
        self._retrieve_selected_lengths()
    
    class Pair():
        """helper class for dynamic programming algorithm
        """
        def __init__(self):
            self.value = None
            self.ref = None
            self.domination: DominationType = None
        
        def __eq__(self, other: object) -> bool:
            return all((
                round(self.value,3) == round(other.value,3),
                self.ref == other.ref,
                self.domination == other.domination
            ))
        
        def __str__(self):
            return (f"Pair: [value: {self.value}, ref: {self.ref}, domination: {self.domination}]")
    
    class SelectedLength():
        """helper class for retrieving new lengths from calculation results
        """
        def __init__(self, index: int, domination: DominationType):
            self.index: int = index
            self.domination: DominationType = domination
        def __eq__(self, other: object):
            return all((
                self.index == other.index,
                self.domination == other.domination
            ))
        def __str__(self):
            return (f"SelectedLength: [index: {self.index}, domination: {self.domination}]")
    
    def _run(self) -> NoReturn:
        lengths = self.lengths # local ref for clarity
        container = []
        self._container = container
        for i in range(len(lengths)):
            row = []
            container.append(row)
            for j in range(len(lengths)):
                if j < i:
                    row.append(None)
                else:
                    row.append(self.Pair())
        for i in range(len(lengths)):
            for j in range(i,len(lengths)):
                if i == 0:
                    container[i][j].value = max(self.ld_length, lengths[j]+self.d_length) * (j+1)
                    if self.ld_length > lengths[j]+self.d_length:
                        domination = DominationType.LD
                    else:
                        domination = DominationType.D
                    container[i][j].domination = domination
                else:
                    min_value = float("inf")
                    min_index = None
                    min_domination = None
                    for k in range(i-1, j): # doesn't include j
                        value = container[i-1][k].value + (j-k) * max(lengths[k]+self.ld_length, lengths[j]+self.d_length)
                        if lengths[k]+self.ld_length > lengths[j]+self.d_length:
                            domination = DominationType.LD
                        else:
                            domination = DominationType.D
                        if value < min_value:
                            min_value = value
                            min_index = k
                            min_domination = domination
                    container[i][j].value = min_value
                    container[i][j].ref = min_index
                    container[i][j].domination = min_domination
                        
    def _retrieve_selected_lengths(self) -> None:
        """returns the list of indices that results in the minimum total length
        and the domination status of each one
        """
        min_value = float("inf")
        min_index = None
        for i in range(len(self.lengths)):
            if self._container[i][len(self.lengths)-1].value < min_value:
                min_value = self._container[i][len(self.lengths)-1].value
                min_index = i
        
        row_index = min_index
        col_index = len(self.lengths)-1
        selected_lengths = []
        while (row_index >= 0):
            selected_length = self.SelectedLength(index=col_index, domination=self._container[row_index][col_index].domination)
            selected_lengths.append(selected_length)
            col_index = self._container[row_index][col_index].ref
            row_index -= 1
        self._selected_lengths = selected_lengths
    
    def get_results(self) -> List[IncreasedLength]:
        increased_lengths = []
        selected_lengths = list(reversed(self._selected_lengths))
        i = 0
        for j,selected_length in enumerate(selected_lengths):
            base_length = None
            if selected_length.domination == DominationType.LD:
                if j == 0:
                    base_length = self.ld_length
                else:
                    base_length = self.ld_length + self.lengths[selected_lengths[j-1].index]
            else:
                base_length = self.d_length + self.lengths[selected_length.index]
            for k in range(i,selected_length.index+1):
                increased_length = IncreasedLength(addition = base_length - self.lengths[k], domination=selected_length.domination)
                increased_lengths.append(increased_length)  
            i = selected_length.index+1
        return increased_lengths

class IncreasedLength():
    def __init__(self, addition: float, domination: DominationType):
        self.addition = addition
        self.domination = domination
    def __eq__(self, other: IncreasedLength):
        return all((
            round(self.addition,3) == round(other.addition,3),
            self.domination == other.domination
        ))
    def __str__(self):
        return (f"IncreasedLength: [addition: {self.addition}, domination: {self.domination}]")
            
class DominationType(Enum):
    D = 0
    LD = 1

class PieceDomination():
    def __init__(self, start=None, end=None):
        self.start = start
        self.end = end
    def __eq__(self, other: PieceDomination) -> bool:
        return all((
            self.start == other.start,
            self.end == other.end
        ))
    def __str__(self):
        return f"Piece Domination:({self.start}, {self.end})"


class PracticalOptimization():
    def __init__(self, stack: Stack, d_length: float, ld_length: float):
        self.stack = stack
        self.d_length = d_length
        self.ld_length = ld_length
        self._run()

    def _extract_lengths(self, side: str) -> List[float]:
        """extracts list of lengths for each side of the stack

        Args:
            side (str): it could be "start" or "end"

        Returns:
            List[float]: list of lengths in ascending order
        """
        lengths = []
        for piece in self.stack.get_pieces():
            lengths.append(abs(self.stack.peak_station - getattr(piece.theoretical,side)))
        return lengths

    def _initialize_practical(self) -> None:
        """initializes practical period and domination for each piece of stack
        """
        for piece in self.stack.get_pieces():
            if piece.practical is None:
                piece.practical = Period()
                piece.domination = PieceDomination()

    def _set_practical(self, side:str, increased_lengths: List[IncreasedLength])->None:
        """sets the practical period value for each side according to the given
        increased lengths.

        Args:
            side (str): could be "start" or "end"
            increased_lengths (List[IncreasedLength]): containing the addition value and the domination status
        """
        for i in range(len(self.stack)):
            station = None
            piece = self.stack.get_pieces()[i]
            if side == "start":
                station = getattr(piece.theoretical, side) - increased_lengths[i].addition
                if piece.practical.start is not None:
                    station = min(station, piece.practical.start)
            else:
                station = getattr(piece.theoretical, side) + increased_lengths[i].addition
                if piece.practical.end is not None:
                    station = max(station, piece.practical.end)

            setattr(piece.practical, side, station)
            setattr(piece.domination, side, increased_lengths[i].domination)
    
    def _set_side(self, side) -> None:
        """sets the practical length for each side of the stack

        Args:
            side ([type]): [description]
        """
        lengths = self._extract_lengths(side)
        optimization = StackMinimization(lengths=lengths, d_length=self.d_length, ld_length=self.ld_length)
        increased_lengths = optimization.get_results()
        self._set_practical(side=side, increased_lengths=increased_lengths)
    
    def _run(self) -> None:
        self._initialize_practical()
        self._set_side("start")
        self._set_side("end")