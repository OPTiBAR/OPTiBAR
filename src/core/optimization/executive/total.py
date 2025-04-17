from __future__ import annotations
from typing import List, Dict, NoReturn
from .errors import NotEnoughTypes
from core.src.components.piece import Piece
STANDARD_LENGTH = 12

class TotalAlgorithm():
    def __init__(self, pieces: List[Piece]):
        self._container = None
        input_dict = self._get_inputs(self._get_bunch_dict(pieces))
        self._lengths = input_dict["lengths"]
        self._run(**input_dict)
    
    class Pair():
        def __init__(self):
            self.value = None
            self.ref = None
        def __eq__(self, other: object) -> bool:
            return all((
                self.value == other.value,
                self.ref == other.ref
            ))
        def __str__(self):
            return (f"Pair: [value: {self.value}, ref: {self.ref}]")

    def _get_bunch_dict(self, pieces: List[Piece]) -> Dict[float, Bunch]:
        bunch_dict = {}
        # keys are lengths and values are Bunch with the specified length
        for piece in pieces:
            length = piece.shortest_piece_length
            if length in bunch_dict:
                bunch_dict[length].add_piece(piece)
            else:
                bunch = Bunch(length)
                bunch.add_piece(piece)
                bunch_dict[length] = bunch
        return bunch_dict

    def _get_inputs(self, bunch_dict) -> Dict[str,List[float]]:  
        sorted_bunches = [bunch_dict[length] for length in sorted(bunch_dict.keys())]
        lengths = list(map(lambda bunch: bunch.get_length(),sorted_bunches))
        upper_bounds = list(map(lambda bunch: bunch.get_upper_bound(),sorted_bunches))
        counts = list(map(lambda bunch: bunch.get_count(),sorted_bunches))
        # STANDARD_LENGTH should be added to the candidate lengths
        if STANDARD_LENGTH not in lengths:
            lengths.append(STANDARD_LENGTH)
            upper_bounds.append(STANDARD_LENGTH)
            counts.append(0)
        return {
            "lengths": lengths,
            "upper_bounds": upper_bounds,
            "counts": counts
        }

    def _run(self, lengths, counts, upper_bounds):
        # initialize the container
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
        def f(x):
            if x <= 0:
                return 1
            else:
                return float("inf")
        # algorithm
        for i in range(len(lengths)):
            for j in range(i,len(lengths)):
                if i == 0:
                    sum = 0
                    for k in range(j):
                        sum += counts[k] * (lengths[j] - lengths[k]) * f(lengths[j] - upper_bounds[k])
                    container[i][j].value = sum
                else:
                    min_value = float("inf")
                    min_index = None
                    for m in range(i-1,j):
                        sum = container[i-1][m].value
                        for k in range(m+1,j):
                            sum +=  counts[k] * (lengths[j] - lengths[k]) * f(lengths[j] - upper_bounds[k])
                        if sum < min_value:
                            min_value = sum
                            min_index = m
                    container[i][j].value = min_value
                    container[i][j].ref = min_index
    
    def get_selected_lengths(self, number_of_types: int) -> List[float]:
        """selcted lengths in the total length type reduction algorithm

        Raises:
            NotEnoughTypes: if the number of types is not feasible this error will be raised.

        Returns:
            List[float]: selected lengt of pieces.
        """
        container = self._container
        lengths = self._lengths
        row_index = min(number_of_types-1, len(lengths)-1)
        col_index = len(lengths)-1
        # use value instead of ref == None for zero pieces and one length that is default 12
        if container[row_index][col_index].value == float('inf'):
            for r_index in range(row_index+1, len(lengths)):
                if container[r_index][col_index].value == float('inf'):
                    raise NotEnoughTypes("total: not enough type number", r_index+1)
            raise ValueError("there is no feasible solution, actually it should not happen!")
        selected_lengths = []
        while (row_index >= 0):
            selected_lengths.append(lengths[col_index])
            col_index = container[row_index][col_index].ref
            row_index -= 1
        return selected_lengths

class Bunch():
    def __init__(self, length: float):
        self._length = length
        self._pieces = []
        self._count = 0
    def add_piece(self, piece:Piece) -> NoReturn:
        self._pieces.append(piece)
        self._count += 1
    def get_length(self) -> float:
        return self._length
    def get_pieces(self) -> List[Piece]:
        return self._pieces
    def get_count(self) -> int:
        return self._count
    def get_upper_bound(self) -> float:
        return min(map(lambda piece: getattr(piece, "length_upper_bound"), self._pieces))    
    def __str__(self) -> str:
        return (f"Bunch: [length: {self._length}, count: {self._count}]")
    