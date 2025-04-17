from __future__ import annotations
from typing import Iterator, List, Dict
from .piece import Piece
from .diagram import Diagram

class Stack():
    """Stack is a list of pieces that are subset of each other consequently
    """
    def __init__(self, peak_station: float):
        self.peak_station = peak_station
        self._pieces = []

    def add_piece(self, piece: Piece) -> None:
        """adds piece to the stack. pieces are added from top to bottom.

        Args:
            piece (Piece): the piece that should be added to the stack
        """
        self._pieces.append(piece)
    
    def get_pieces(self) -> List[Piece]:
        return self._pieces
    
    def __len__(self):
        return len(self._pieces)
    
    def __eq__(self, other: Stack):
        return all((
            self._pieces == other.get_pieces(),
            self.peak_station == other.peak_station
        ))
    def __str__(self):
        str_output = "Stack:" + f"\t peak station: {self.peak_station}\n"
        for piece in self._pieces():
            str_output += str(piece)
            str_output += "\n"
        return str_output
class Bunch():
    """bunch of identical pieces
    """
    def __init__(self):
        self._pieces = []
    
    def add(self, piece: Piece) -> None:
        """adds new piece to the bunch and updates count

        Args:
            piece (Piece): the new piece to be added
        """
        self._pieces.append(piece)

    def get_pieces(self):
        return self._pieces
        
    def get_count(self):
        return len(self._pieces)

    def __str__(self):
        str_out = "Bunch: \n"
        str_out += f"\tCount: {self.get_count()}\n"
        if len(self._pieces)>0:
            str_out += "\t" + str(self._pieces[0]) + "\n"
        str_out += "\n"
        return str_out
    
    # def __eq__(self):
        # should not be defined
        # it harms the get_drawing_data method of the Container class

class Container():
    """Holds pieces row by row
    """
    def __init__(self, diagram: Diagram):
        self._rows = []
        self._diagram = diagram
    
    def add_row(self, row: List[Piece]) -> None:
        """add rows from bottom to the top

        Args:
            row (List[Piece]): row of pieces
        """
        self._rows.append(row)
    
    def get_rows(self) -> List[List[Piece]]:
        return self._rows
    
    def get_pieces(self) -> Iterator[Piece, None, None]:
        """generator returning all the pieces

        Yields:
            Generator[Piece, None, None]: returns piece
        """
        for row in self._rows:
            for piece in row:
                yield(piece)

    def get_stacks(self, by: str) -> List[Stack]:
        """returns stacks of pieces in the container

        Args:
            by (str): can be one of these values "theoretical", "practical" or "executive"

        Returns:
            List[Stack]: list of stacks
        """
        stacks = []
        for row in reversed(self._rows): # rows from top to bottom
            for piece in row:
                added = False
                for stack in stacks:
                    if (len(stack)>0) and \
                        (getattr(stack.get_pieces()[-1], by).is_subset_of(getattr(piece, by))):
                        added = True
                        stack.add_piece(piece)
                if not added:
                    new_stack = Stack(self._diagram.get_max_point(getattr(piece,by)).station)
                    new_stack.add_piece(piece)
                    stacks.append(new_stack)
        return stacks
        
    
            
    def get_drawing_data(self) -> List[List[Bunch]]:
        """returns bunch of piece in list of list
        the first list contains bunches of the first row and are sorted from start to end
        """
        def get_bunch_list(piece_list: List[Dict[str,object]]) -> List[Dict[str,object]]:
            """gets pieces of one stack and returns bunches

            Args:
                piece_list (List[Dict[str,object]]): list of piece dictionaries

            Returns:
                List[Dict[str,object]]: list of bunch dictionaries
            """
            bunch_list = []
            referenced_bunches = []
            row_index = 0
            for piece_dict in piece_list:
                if piece_dict["bunch_ref"] is None:
                    if len(bunch_list) > 0 and round(bunch_list[-1]["bunch"].get_pieces()[-1].executive.get_length(),3) == round(piece_dict["piece"].executive.get_length(),3):
                        bunch_list[-1]["bunch"].add(piece_dict["piece"])
                        piece_dict["bunch_ref"] = bunch_list[-1]["bunch"]
                    else:
                        bunch = Bunch()
                        bunch.add(piece_dict["piece"])
                        bunch_list.append({
                            "bunch": bunch,
                            "row_index": row_index
                        })
                        piece_dict["bunch_ref"] = bunch
                        row_index += 1
                else:
                    if piece_dict["bunch_ref"] not in referenced_bunches:
                        row_index += 1
                        referenced_bunches.append(piece_dict["bunch_ref"])
            return bunch_list
        
        # initializing list of piece_dict
        piece_list = []
        for piece in self.get_pieces():
            piece_list.append({
                "piece": piece,
                "bunch_ref": None
            })
        # initializing list of stack_dict
        stack_list = []
        for stack in self.get_stacks("executive"):
            stack_list.append({
                "stack": stack, # ref to stack object
                # list of piece_dicts of the stack
                "piece_list": [next(filter(lambda piece_dict: piece_dict["piece"] is piece, piece_list)) for piece in reversed(stack.get_pieces()) ],
                # list of bunch_dicts of this stack
                "bunch_list": None
            })
        # initialize the value of bunch_list
        for stack_dict in stack_list:
            stack_dict["bunch_list"] = get_bunch_list(stack_dict["piece_list"])
            # if (len(stack_dict["bunch_list"])==6):
            #     for bunch in stack_dict["bunch_list"]:
            #         print(bunch["bunch"])
            #         print(bunch["bunch"].get_pieces()[0].shortest_piece_length)
            
        
        # dict of rows key: row_index and value: list of bunches
        row_dict = {}
        for stack_dict in stack_list:
            for bunch_dict in stack_dict["bunch_list"]:
                row_index = bunch_dict["row_index"]
                if row_index in row_dict:
                    row_dict[row_index].append(bunch_dict["bunch"])
                else:
                    row_dict[row_index] = [bunch_dict["bunch"]]
        # sort bunches of each row by their start station
        for row_index in row_dict:
            row_dict[row_index] = sorted(row_dict[row_index], key=lambda bunch: bunch.get_pieces()[0].executive.start)
        # initializing list of list of bunches, the first list belongs to the first row
        rows = []
        for row_index in sorted(row_dict.keys()):
            rows.append(row_dict[row_index])
        return rows
