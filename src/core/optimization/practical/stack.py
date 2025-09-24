from core.components.period import Period
from core.components.collections import Stack
from .errors import NotEnoughTypes
import copy

class StackAlgorithm():
    def __init__(
            self,
            stack: Stack,
            selected_lengths: list[float]
        ):
        self._stack = stack
        self._selected_lengths = sorted(selected_lengths)
        self._run()
        self._type_dict = self._get_selected_lengths()

    def _run(self):
        container = []
        self._container = container
        selected_lengths = self._selected_lengths
        pieces = sorted(self._stack.get_pieces(), key = lambda piece: piece.shortest_piece_length)
        for i in range(len(selected_lengths)):
            row = []
            container.append(row)
            for j in range(len(selected_lengths)):
                if j < i:
                    row.append(None)
                else:
                    row.append(Cell())
        for i in range(len(selected_lengths)):
            for j in range(i,len(selected_lengths)):
                if i == 0:
                    sum = 0
                    type_counter = TypeCounter()
                    for piece in pieces:
                        if (piece.shortest_piece_length <= selected_lengths[j]):
                            if (piece.length_upper_bound >= selected_lengths[j]):
                                sum += selected_lengths[j] - piece.shortest_piece_length
                                type_counter.add_piece(num_of_pieces= piece.get_num_of_pieces("required"),new_length= selected_lengths[j])
                            else:
                                sum = None
                                break
                    container[i][j].value = sum
                    container[i][j].type_counter = type_counter
                else: # i > 0
                    min_value = float("inf")
                    min_index = None
                    min_type_counter = None

                    for k in range(i-1, j):
                        if container[i-1][k].value is None:
                            continue
                        sum = container[i-1][k].value
                        type_counter = copy.copy(container[i-1][k].type_counter)
                        for piece in pieces:
                            if (piece.shortest_piece_length <= selected_lengths[j]) and \
                                (piece.shortest_piece_length > selected_lengths[k]):
                                if (piece.length_upper_bound >= selected_lengths[j]):
                                    sum += selected_lengths[j] - piece.shortest_piece_length
                                    type_counter.add_piece(piece.get_num_of_pieces("required"), selected_lengths[j])
                                else:
                                    sum = None
                                    break
                        if sum is not None and sum < min_value:
                            min_value = sum
                            min_index = k
                            min_type_counter = type_counter
                    if min_index is not None:
                        container[i][j].value = min_value
                        container[i][j].ref = min_index
                        container[i][j].type_counter = min_type_counter
        # for row in container:
        #     print("row:   ")
        #     for cell in row:
        #         print(cell)

    def _get_selected_lengths(self) -> dict[int, list[float]]:
        container = self._container
        lengths = self._selected_lengths
        max_piece_length = max(map(lambda piece: piece.shortest_piece_length,self._stack.get_pieces()))
        type_dict = {} # key: num_of_types , value: dict referencing the min cell in container
        for i in range(len(lengths)):
            for j in range(i, len(lengths)):
                if (container[i][j].value is not None) and (lengths[j] >= max_piece_length):
                    if container[i][j].type_counter.get_num_of_types() in type_dict:
                        temp = type_dict[container[i][j].type_counter.get_num_of_types()]
                        if container[i][j].value < temp['min_value']:
                            temp['min_value'] = container[i][j].value
                            temp['min_row_index'] = i
                            temp['min_col_index'] = j
                    else:
                        type_dict[container[i][j].type_counter.get_num_of_types()] = {
                            'min_value': container[i][j].value,
                            'min_row_index': i,
                            'min_col_index': j
                        }
        output_dict = {} # key: num_of_types, value: selected lengths
        for num in type_dict:
            selected_lengths = []
            col_index = type_dict[num]['min_col_index']
            row_index = type_dict[num]['min_row_index']
            while(row_index >= 0):
                selected_lengths.append(lengths[col_index])
                col_index = container[row_index][col_index].ref
                row_index -= 1
            output_dict[num] = selected_lengths
            # if num == 2 and selected_lengths == [12]:
            # if container[type_dict[num]['min_col_index']][type_dict[num]['min_row_index']] is None:
                # print(container[type_dict[num]['min_row_index']][type_dict[num]['min_col_index']])
                # print(container[1][-1])
                # print(sorted(list(set(map(lambda p: p.shortest_piece_length, self.__stack.get_pieces())))))
                # print(sorted(list(set(map(lambda p: p.length_upper_bound, self.__stack.get_pieces())))))


        return output_dict

    def _adjust_lengths(self, selected_lengths: list[float]) -> None:
        pieces = sorted(self._stack.get_pieces(), key=lambda piece: piece.shortest_piece_length)
        selected_lengths = sorted(selected_lengths)
        i = 0
        j = 0
        while i < len(pieces) and j < len(selected_lengths):
            if pieces[i].shortest_piece_length <= selected_lengths[j]:
                if pieces[i].length_upper_bound < selected_lengths[j]:
                    raise ValueError("the upper bound is not ...") # could be removed
                else:
                    # if pieces[i].theoretical == Period(1.383,11.602):
                    #     print(pieces[i].shortest_piece_length)
                    #     print(selected_lengths)
                    pieces[i].shortest_piece_length = selected_lengths[j]
                    i += 1
            else:
                j += 1
        # investigate exit condition
        if i < len(pieces):
            raise ValueError("the longest selected length is too short") # could be removed !

    def set_lengths(self, num_of_types: int) -> None:
        type_dict = self._type_dict
        # for num in type_dict:
        #     print(type_dict[num])
        if num_of_types not in type_dict:
            if num_of_types > max(type_dict.keys()):
                # print(type_dict[max(type_dict.keys())])
                self._adjust_lengths(type_dict[max(type_dict.keys())])
            elif num_of_types < min(type_dict.keys()):
                raise NotEnoughTypes("stack: there is no-feasible solution for this number of types", min(type_dict.keys()))
            else:
                for i in sorted(type_dict.keys(), reverse=True):
                    if i < num_of_types:
                        self._adjust_lengths(type_dict[i])
                        break
        else:
            self._adjust_lengths(type_dict[num_of_types])

class TypeCounter():
    """holds a dict
            key: number of subpieces
            value: set of the lengths of the pieces
    """
    def __init__(self):
        self._counter = {}

    def add(self, other_type_counter: TypeCounter)-> None:
        """combines another type counter with self
        adds new number_of_pieces and new lengths in each of length lists

        Args:
            other_type_counter (TypeCounter): another type counter
        """
        for num_of_pieces in other_type_counter._counter.keys():
            if num_of_pieces in self._counter.keys():
                self._counter[num_of_pieces] = self._counter[num_of_pieces].union(other_type_counter._counter[num_of_pieces])
            else:
                self._counter[num_of_pieces] = copy.copy(other_type_counter._counter[num_of_pieces])

    def add_piece(self, num_of_pieces: int, new_length: float):
        if num_of_pieces in self._counter.keys():
            self._counter[num_of_pieces].add(new_length)
        else:
            self._counter[num_of_pieces] = {new_length}

    def get_num_of_types(self) -> int:
        return sum(map(len,self._counter.values()))

    def __eq__(self, other: TypeCounter) -> bool:
        is_equal = True
        for num_of_pieces in self._counter:
            if num_of_pieces in other._counter:
                if self._counter[num_of_pieces] != other._counter[num_of_pieces]:
                    is_equal = False
                    break
            else:
                is_equal = False
                break
        return is_equal

    def __copy__(self):
        tc = TypeCounter()
        tc.add(self)
        return tc

    def __str__(self):
        output = "TypeCounter: [\n"
        for num_of_pieces in self._counter:
            output += f"\t{num_of_pieces}: {self._counter[num_of_pieces]}\n"
        output += "]"
        return output

class Cell():
    def __init__(self):
        self.value = None
        self.ref = None
        self.type_counter = TypeCounter()

    def __eq__(self, other: Cell):
        value_equality = None
        if self.value is None or other.value is None:
            value_equality = (self.value == other.value)
        else:
            value_equality = (round(self.value,2) == round(other.value,2))

        return all((
            value_equality,
            self.ref == other.ref,
            self.type_counter == other.type_counter
        ))
    def __str__(self):
        return (
            f"Cell: [value: {self.value}, ref: {self.ref}, {self.type_counter}]"
        )
