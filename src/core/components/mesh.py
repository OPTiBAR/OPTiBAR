from __future__ import annotations

from .diagram import Diagram
from .collections import Container, Stack
from .piece import Piece
from .rebar import Rebar
from core.src.optimization.practical import DominationType, PracticalOptimization
from .period import Period
from .utilities import round_down, round_up
import math
from typing import Dict, List, Union, Iterator
from core.setting import MAX_REBAR_GAP, MIN_RATIO, THERMAL_MIN_RATIO, ROUND_UNIT, STANDARD_LENGTH, MIN_REBAR_GAP
import warnings
import numpy as np

class Section():
    def __init__(self, width, thickness, effective_thickness):
        self.width = width
        self.thickness = thickness
        self.effective_thickness = effective_thickness

class Mesh():
    def __init__(self, diagram: Diagram, section: Section):
        self.diagram = diagram
        self.container = Container(diagram)
        self.section = section
        self.typical_rebar_num = None
        self.side_cover = None

    def set_side_cover(self, side_cover: float) -> None:
        self.side_cover = side_cover
    
    def set_typical_rebar(
            self,
            typical_rebar: Rebar,
            thermal_rebar: Rebar,
            arrangement: Dict[str,Union(str,float)]
        ) -> None:
        """inserts typical rebar and reduces the needed steel diagram

        Args:
            typical_rebar (Rebar): typical rebar
            thermal_rebar (Rebar): thermal rebar
            method (Dict): "method" : "MIN_RATIO" | "COUNT" | "INTERVAL" | "SMART"
                                    "count": int (if type == "COUNT")
                                    "interval": float (if type == "INTERVAL")
            arrangement (Dict[str]): the setting of typical rebar insertion
        """
        if self.diagram.is_positive():
            self.typical_type = 'typical'
            self.typical_rebar = typical_rebar            
            min_ratio_area = self.section.width * self.section.thickness * MIN_RATIO
            min_ratio_num = math.ceil(min_ratio_area/self.typical_rebar.get_area())
            
            if arrangement["method"] == "MIN_RATIO":
                self.typical_rebar_num = min_ratio_num
                amount = self.typical_rebar_num * self.typical_rebar.get_area()
                self.diagram.insert_typical(amount)
            elif arrangement["method"] == "COUNT":
                self.typical_rebar_num = arrangement["value"]
                amount = self.typical_rebar_num * self.typical_rebar.get_area()
                self.diagram.insert_typical(amount)
            elif arrangement["method"] == "INTERVAL":
                interval_num = math.ceil((round(self.section.width,2))/arrangement["value"])
                self.typical_rebar_num = interval_num
                amount = self.typical_rebar_num * self.typical_rebar.get_area()
                self.diagram.insert_typical(amount)
            elif arrangement["method"] == "SMART":
                self.typical_rebar_num = min_ratio_num
                amount = self.typical_rebar_num * self.typical_rebar.get_area()
                self.diagram.insert_typical(amount)
                d = self.section.thickness
                while (self.diagram.get_side_distance() < d) and (self.diagram.get_middle_distance() < 2*d):
                    self.typical_rebar_num += 1
                    self.diagram.insert_typical(self.typical_rebar.get_area())
            else: 
                raise ValueError("typical method type should be one of MIN_RATIO, COUNT,INTERVAL, SMART")
        else: # self.diagram.is_positive() == False
            self.typical_type = 'thermal'
            self.typical_rebar = thermal_rebar
            min_ratio_area = self.section.width * self.section.thickness * THERMAL_MIN_RATIO
            rebar_num = math.ceil(min_ratio_area/self.typical_rebar.get_area())
            while True:
                gap = (self.section.width - 2 * self.side_cover - rebar_num * (thermal_rebar.get_diameter_mm()/1000)) / (rebar_num - 1)
                if gap < MAX_REBAR_GAP:
                    break
                else:
                    rebar_num += 1
            self.typical_rebar_num = rebar_num
            amount = self.typical_rebar_num * self.typical_rebar.get_area()
            self.diagram.insert_typical(amount)

    def set_additional_rebar(self, additional_rebar: Rebar, additional_elimination: float) -> None:
        """inserts additional rebar and keeps them in the container.
        the process of generating executive lengths is called here.

        Args:
            additional_rebar (Rebar): rebar

        """
        self.additional_rebar = additional_rebar
        self._insert_additional(additional_elimination)
        self._theoretical_to_executive()
          
    def get_typical_piece(self) -> Piece:
        period = self._get_bounds()
        period.start -= self.typical_rebar.get_bend_length()
        period.end += self.typical_rebar.get_bend_length()
        # period.end = period.start + round_down(period.end - period.start, ROUND_UNIT)
        piece = Piece(self.typical_rebar, period)
        piece.bend.start = self.typical_rebar.get_bend_length()
        piece.bend.end = self.typical_rebar.get_bend_length()
        piece.practical = period
        self._set_piece_upper_bound(piece)
        self._round_piece(piece)
        self._set_piece_executive(piece)
        return piece

    def _get_bounds(self) -> Period:
        bounds = self.diagram.get_bounds()
        bounds.start += self.side_cover
        bounds.end -= self.side_cover
        return bounds
    
    def _insert_additional(self, additional_elimination) -> None:
        """inserts additional rebars and initializes the theoretical periods
        if period length is less than the ELIMINATION_LENGTH it should be eliminated.
        the resulting pieces are stored in container.
        """
        while self.diagram.is_positive():
            periods = self.diagram.insert_additional(self.additional_rebar.get_area())
            row = [] # row of pieces
            for period in periods:
                if period.get_length() > additional_elimination:
                    piece = Piece(rebar=self.additional_rebar, theoretical=period)
                    row.append(piece)
            if len(row) > 0:
                self.container.add_row(row)
    
    def _set_practical(self) -> None:
        """gets stacks from container and adds optimized practical lengths to them.
        """
        for stack in self.container.get_stacks("theoretical"):
            PracticalOptimization(stack, d_length=self.section.effective_thickness, ld_length=self.additional_rebar.get_ld())
    
    def _bend(self) -> None:
        """if theoretical length has exceeded the bounds it should be bended
        if practical length has exceeded the bounds, if domination is Ld it should be bended
        if domination is d it should be cut.
        """
        for piece in self.container.get_pieces():
            self._bend_piece(piece)
            
    def _bend_piece(self, piece: Piece) -> None:
        bend_length = piece.rebar.get_bend_length()
        bounds = self._get_bounds()
        # theoretical exceed
        if piece.theoretical.start < bounds.start:
            piece.bend.start = bend_length
            piece.theoretical.start = bounds.start - bend_length
            piece.practical.start = piece.theoretical.start
        if piece.theoretical.end > bounds.end:
            piece.bend.end = bend_length
            piece.theoretical.end = bounds.end + bend_length
            piece.practical.end = piece.theoretical.end
        # practical exceed
        if piece.practical.start < bounds.start and piece.bend.start == 0:
            if piece.domination.start == DominationType.D:
                piece.practical.start = bounds.start
            else: # piece.domination.start == Domination.LD
                piece.bend.start = bend_length
                piece.practical.start = bounds.start - bend_length
        if piece.practical.end > bounds.end and piece.bend.end == 0:
            if piece.domination.end == DominationType.D:
                piece.practical.end = bounds.end
            else: # piece.domination.end == Domination.LD
                piece.bend.end = bend_length
                piece.practical.end = bounds.end + bend_length
    
    def _bend_stack_base(self):
        bounds = self._get_bounds()
        stacks = self.container.get_stacks("theoretical")
        for stack in stacks:
            pieces = stack.get_pieces()
            for i,piece in enumerate(pieces):
                bend_length = piece.rebar.get_bend_length()
                # theoretical exceed
                if piece.theoretical.start < bounds.start:
                    piece.bend.start = bend_length
                    piece.theoretical.start = bounds.start - bend_length
                    piece.practical.start = piece.theoretical.start
                if piece.theoretical.end > bounds.end:
                    piece.bend.end = bend_length
                    piece.theoretical.end = bounds.end + bend_length
                    piece.practical.end = piece.theoretical.end
                # practical exceed
                if (piece.practical.start < bounds.start and piece.bend.start == 0):
                    if piece.domination.start == DominationType.LD or (i > 0 and pieces[i-1].bend.start > 0):
                        piece.bend.start = bend_length
                        piece.practical.start = bounds.start - bend_length
                    else:
                        piece.practical.start = bounds.start
                        
                if (piece.practical.end > bounds.end and piece.bend.end == 0):
                    if piece.domination.end == DominationType.LD or (i > 0 and pieces[i-1].bend.end > 0):
                        piece.bend.end = bend_length
                        piece.practical.end = bounds.end + bend_length
                    else:
                        piece.practical.end = bounds.end
    
    def _set_upper_bound(self) -> None:
        """sets the upper bound property for all the pieces
        """
        for piece in self.container.get_pieces():
            self._set_piece_upper_bound(piece)
            
    def _set_piece_upper_bound(self, piece:Piece) -> None:
        """sets the length_upper_bound property
        """
        if piece.get_num_of_pieces("practical") > 1:
            piece.length_upper_bound = STANDARD_LENGTH
        else:
            piece_upper_bound = self._get_bounds().get_length() + piece.bend.start + piece.bend.end
            piece.length_upper_bound = min(piece_upper_bound, STANDARD_LENGTH)

    def _refresh(self) -> None:
        """refreshes all the pieces to their initial status
        """
        for piece in self.container.get_pieces():
            piece.refresh()

    def _round_piece(self, piece: Piece):
        """the length of the smallest subpiece of each piece should be rounded to 5cm
        first try to round up if not possible try to round down.
        set the shortest_piece_length property of the piece.
        """
        length = piece.get_shortest_piece_length("practical")
        revised_length = None
        if round_up(length, ROUND_UNIT) <= piece.length_upper_bound:
            revised_length = round_up(length, ROUND_UNIT)
        else:
            revised_length = round_down(length, ROUND_UNIT)
        piece.shortest_piece_length = revised_length

    def _round(self):
        for piece in self.container.get_pieces():
            self._round_piece(piece)

    def _unify(self, by: str) -> bool:
        """try to unify all intersecting pieces based on their <by> lengths in the container
        Args:
            by (str): could be practical or executive
        Returns:
            bool: if any pieces are unified, return True else return False.
        """
        stacks = self.container.get_stacks(by)
        banned_stack_pairs = []

        is_unified = False
        for row in self.container.get_rows():
            row_piece_stacks = []
            for piece in row:
                piece_stacks = []
                for stack in stacks:
                    if piece in stack.get_pieces():
                        piece_stacks.append(stack)
                row_piece_stacks.append(piece_stacks)
            if self._unify_row(row,by, row_piece_stacks, banned_stack_pairs):
                is_unified = True
        return is_unified

    def _unify_row(self, row: List[Piece], by: str, row_piece_stacks, banned_stack_pairs) -> bool:
        """
        try to unify all intersecting pieces based on their <by> lengths in a row
        try all possible partitionings and choose the best.
        Args:
            by (str): could be practical or executive
        Returns:
            bool: if any pieces are unified, return True else return False.
        """
        def partition(collection: List[object]) -> List[List[object]]:
            """returns all partitions of the input collection

            Args:
                collection (List[object]): list of any object

            Returns:
                List[List[object]]: [description]

            Yields:
                Iterator[List[List[object]]]: partitition of the input collection
            """
            if len(collection) == 1:
                yield [ collection ]
                return

            first = collection[0]
            for smaller in partition(collection[1:]):
                # insert `first` in first subpartition's subsets
                yield [[ first ] + smaller[0]] + smaller[1:]
                # put `first` in its own subset 
                yield [ [ first ] ] + smaller
        rebar = self.additional_rebar
        sublist = []
        is_unified = False
        i = 0
        while i < len(row):
            sublist.append(i)
            if i < len(row)-1 and getattr(row[i],by).has_intersection_with(getattr(row[i+1],by)) and \
                not any([row[i] in pair[0].get_pieces() and row[i+1] in pair[1].get_pieces() for pair in banned_stack_pairs]):
                i += 1
                continue
            if len(sublist) == 1:
                sublist = []
                i += 1
                continue                
            # find the min partitioning
            min_value = float("inf")
            min_parts = None
            for parts in partition(sublist):
                length_sum = 0
                for part in parts: # part : List[Piece]
                    length = getattr(row[part[-1]],by).end - getattr(row[part[0]],by).start
                    length_sum += Piece.get_net_length(length, rebar.get_overlap_length())
                if length_sum < min_value:
                    min_value = length_sum
                    min_parts = parts
            # determine not unified pieces and add them to the stack ban list
            # to prevent aggregation of these stacks in upper rows
            for j in range(len(min_parts)-1):
                for start_index in min_parts[j]:
                    for end_index in min_parts[j+1]:
                        for stack_start in row_piece_stacks[start_index]:
                            for stack_end in row_piece_stacks[end_index]:
                                pair = (stack_start, stack_end)
                                if pair not in banned_stack_pairs:
                                    banned_stack_pairs.append(pair)

            # aggregate pieces and replace
            if max(map(len, min_parts)) > 1: # if partition has a sublist of length greater than one
                pieces = [] # new pieces
                for part in min_parts:
                    period = Period(row[part[0]].theoretical.start, row[part[-1]].theoretical.end)
                    pieces.append(Piece(rebar= rebar, theoretical= period))
                # replace new pieces and assign correct index to i
                del row[sublist[0]: sublist[-1]+1] # delete aggregated
                row[sublist[0]:sublist[0]] = pieces
                is_unified = True
            i += 1 - sum(list(map(lambda x: len(x)-1, min_parts)))
            sublist = []
        return is_unified
        
    def _set_executive(self, by: str):
        """sets executive period of all pieces, based on their shortest piece length
        and considers stack of pieces according to their <by>(practical or executive) property.

        Args:
            by (str): could be practical or executive
        """
        for stack in self.container.get_stacks(by=by):
            pieces = list(reversed(stack.get_pieces())) # longer to shorter
            for i in range(len(stack)):
                if i == 0:
                    self._set_piece_executive(piece= pieces[i])
                else:    
                    self._set_piece_executive(piece= pieces[i], base_piece= pieces[i-1])
    
    def _set_piece_executive(self, piece: Piece, base_piece: Piece= None):
        """set executive period based on shortest_piece_length property.
        Args:
            base_piece (Piece, optional): the base piece to be considered to revise length.
                Defaults to None.
        """
        bounds = self._get_bounds()
        length_change = piece.shortest_piece_length - piece.get_shortest_piece_length("practical")
        bend_length = piece.rebar.get_bend_length()
        start = None
        end = None

        if piece.bend.start == 0 and piece.bend.end == 0: # no bend
            if length_change < 0:
                start = piece.practical.start - length_change/2
                end = piece.practical.end + length_change/2
                piece.practical.start = start
                piece.practical.end = end
                if piece.theoretical.start < start:
                    piece.theoretical.start = start
                if piece.theoretical.end > end:
                    piece.theoretical.end = end
            else: # length_change >= 0
                if base_piece is None:
                    if piece.practical.start - length_change <= bounds.start:
                        start = bounds.start
                        end  = min(start + piece.practical.get_length() + length_change, bounds.end)
                    elif piece.practical.end + length_change >= bounds.end:
                        end = bounds.end
                        start = max(end - piece.practical.get_length() - length_change, bounds.start)
                    else: # doesn't reach any of two sides
                        start = piece.practical.start - length_change/2
                        end  = piece.practical.end + length_change/2
                else: # base piece is not None
                    if base_piece.bend.start == 0 and base_piece.bend.end == 0:
                        # base piece is not bended in neighter of it's ends
                        if piece.practical.start - length_change <= base_piece.executive.start:
                            # reach start of base_piece
                            start = base_piece.executive.start
                            end = min(start + piece.practical.get_length() + length_change, base_piece.executive.end)
                        elif piece.practical.end + length_change >= base_piece.executive.end:
                            # reach end of base_piece
                            end = base_piece.executive.end
                            start = max(end - piece.practical.get_length() - length_change, base_piece.executive.start)
                        else: # doesn't reach any of two sides of the base piece
                            start = piece.practical.start - length_change/2
                            end = piece.practical.end + length_change/2
                    elif base_piece.bend.start > 0 and base_piece.bend.end == 0:
                        # base piece is just bended in the start side
                        if (piece.practical.end + length_change >= base_piece.executive.end) and \
                            (base_piece.executive.end - piece.practical.get_length() - length_change >= bounds.start):
                            # reaches end of base piece and doesn't exceed the start bound
                            end = base_piece.executive.end
                            start = base_piece.executive.end - piece.practical.get_length() - length_change
                        elif piece.practical.start - length_change <= bounds.start - bend_length:
                            # reaches start to be bended and the addition length is sufficient
                            piece.bend.start = bend_length
                            start = bounds.start - bend_length
                            end = min(start + piece.practical.get_length() + length_change, base_piece.executive.end)                            
                            piece.practical.start = start
                            
                        elif (piece.practical.end + length_change >= base_piece.executive.end) and \
                            (base_piece.executive.end - piece.practical.get_length() - length_change < bounds.start): 
                            # reaches not bended end of the base piece but ecxeeds the start bound
                            # the piece length should be increased to the base piece length
                            piece.shortest_piece_length = base_piece.shortest_piece_length
                            piece.bend.start = bend_length
                            start = base_piece.executive.start
                            end = base_piece.executive.end
                            piece.practical.start = start
                        elif (piece.practical.end + length_change < base_piece.executive.end) and \
                            (piece.practical.start - length_change > bounds.start - bend_length): 
                            # doesn't reach any of two ends
                            if piece.practical.start - length_change/2 >= bounds.start:
                                # doesn't proceed start bound
                                start = piece.practical.start - length_change/2
                                end = piece.practical.end + length_change/2
                            else:
                                start = bounds.start
                                end = start + piece.practical.get_length() + length_change
                    elif base_piece.bend.start == 0 and base_piece.bend.end > 0:
                        # base piece is just bended in the end side
                        if (piece.practical.start - length_change <= base_piece.executive.start) and \
                            (base_piece.executive.start + piece.practical.get_length() + length_change <= bounds.end):
                            # reaches start of base piece and doesn't exceed the end bound
                            start = base_piece.executive.start 
                            end = start + piece.practical.get_length() + length_change
                        elif piece.practical.end + length_change >= bounds.end + bend_length:
                            # reaches end to be bended and the addition length is sufficient
                            piece.bend.end = bend_length
                            end = bounds.end + bend_length
                            start = max(end - piece.practical.get_length() - length_change, base_piece.executive.start)
                            piece.practical.end = end
                        elif (piece.practical.start - length_change < base_piece.executive.start) and \
                            (base_piece.executive.start + piece.practical.get_length() + length_change > bounds.end): 
                            # reaches not bended end of the base piece but ecxeeds the end bound
                            # the piece length should be increased to the base piace length
                            piece.shortest_piece_length = base_piece.shortest_piece_length
                            piece.bend.end = bend_length
                            start = base_piece.executive.start
                            end = base_piece.executive.end
                            piece.practical.end = end
                        elif (piece.practical.end + length_change < bounds.end + bend_length) and \
                            (piece.practical.start - length_change > base_piece.executive.start):  
                            # doesn't reach any of two ends
                            if piece.practical.end + length_change/2 <= bounds.end:
                                # doesn't proceed end bound
                                start = piece.practical.start - length_change/2
                                end = piece.practical.end + length_change/2
                            else:
                                end = bounds.end
                                start = end - piece.practical.get_length() - length_change
                    else: # base_piece.bend.start > 0 and base_piece.bend.end > 0
                        if piece.practical.start - length_change <= bounds.start:
                            start = bounds.start
                            end = bounds.start + piece.practical.get_length() + length_change
                        elif piece.practical.end + length_change >= bounds.end:
                            end = bounds.end
                            start = bounds.end - piece.practical.get_length() - length_change
                        else:
                            start = piece.practical.start - length_change/2
                            end = piece.practical.end + length_change/2
        elif piece.bend.start > 0 and piece.bend.end == 0: # start bend
            if length_change < 0:
                piece.practical.end += length_change
                start = piece.practical.start
                end = piece.practical.end
            else: # lenght_change > 0
                if base_piece is None:
                    end = min(piece.practical.end + length_change, bounds.end)
                    start = piece.practical.start
                else: # base_piece is not None
                    if base_piece.bend.end > 0:
                        if piece.practical.end + length_change >= base_piece.executive.end:
                            end = base_piece.executive.end
                            start = piece.practical.start
                            piece.bend.end = bend_length
                            piece.practical.end = base_piece.executive.end
                        else:
                            end = min(piece.practical.end + length_change, bounds.end)
                            start = piece.practical.start
                    else:
                        end = min(piece.practical.end + length_change, base_piece.executive.end, bounds.end)
                        start = piece.practical.start
        elif piece.bend.start == 0 and piece.bend.end > 0: # end bend
            if length_change < 0:
                piece.practical.start -= length_change
                start = piece.practical.start
                end = piece.practical.end
            else: # lenght_change > 0
                if base_piece is None:
                    start = max(piece.practical.start - length_change, bounds.start)
                    end = piece.practical.end
                else: # base_piece is not None
                    if base_piece.bend.start > 0:
                        if piece.practical.start - length_change <= base_piece.executive.start:
                            start = base_piece.executive.start
                            end = piece.practical.end
                            piece.bend.start = bend_length
                            piece.practical.start = base_piece.executive.start
                        else:
                            start = max(piece.practical.start - length_change, bounds.start)
                            end = piece.practical.end
                    else:
                        start = max(piece.practical.start - length_change, base_piece.executive.start, bounds.start)
                        end = piece.practical.end
        else: # both sides are bended
            if length_change <= 0:
                piece.practical.end += length_change
                start = piece.practical.start
                end = piece.practical.end
            else:  # lenght_change > 0
                start = piece.practical.start
                end = piece.practical.end

        piece.executive = Period(start, end)
        
    def get_stacks(self) -> List[Stack]:
        """returns list if stacks based on their executive period
        """
        return self.container.get_stacks(by="executive")
    
    def get_additional_pieces(self) -> Iterator[Piece]:
        """return an Iterator over all the pieces

        Returns:
            List[Piece]: list of pieces
        """
        return self.container.get_pieces()

    def get_piece_rows(self) -> List[List[Piece]]:
        return reversed(self.container.get_rows())
        
    def _get_effective_area_diagram(self) -> Diagram:
        """return diagram of the effective As area of the rebar

        Returns:
            Diagram: diagram of effective area of the rebar
        """
        # initialize diagram
        diagram = Diagram(
            stations = [self.diagram.get_bounds().start, self.diagram.get_bounds().end],
            areas = [0,0]
        )
        # add additional rebars
        for piece in self.container.get_pieces():
            bends = {
                "start":piece.bend.start > 0 ,
                "end": piece.bend.end > 0
            }
            stations = None
            if piece.bend.start > 0 and piece.bend.end > 0:
                stations = []
            elif piece.bend.start > 0 and piece.bend.end == 0:
                stations = [piece.executive.end - piece.rebar.get_ld(), piece.executive.end]
            elif piece.bend.start == 0 and piece.bend.end > 0:
                stations = [piece.executive.start, piece.executive.start + piece.rebar.get_ld()]
            else: # piece.bend.start == 0 and piece.bend.end == 0
                stations = [
                    piece.executive.start, piece.executive.start + piece.rebar.get_ld(),
                    piece.executive.end - piece.rebar.get_ld(), piece.executive.end
                ]
            value = piece.rebar.get_area()
            diagram.increase_area(bends=bends, stations=stations, value=value)
        # add typical rebars
        diagram.increase_area(
            bends = {"start": True, "end": True},
            stations = [],
            value = self.typical_rebar.get_area() * self.typical_rebar_num
        )
        return diagram

    def get_resistance_moment_diagram(
            self,
            widths: List[float],
            stations: List[float],
            fy: float,
            fc: float
        ) -> Diagram:
        """returns the 

        Args:
            fy (float): yield resistance of the steel
            fc (float): yield resistance of the concrete

        Returns:
            Diagram: diagram of the resistance moment
        """
        area_diagram = self._get_effective_area_diagram()
        area_diagram_stations = area_diagram.get_stations()
        areas_diagram_values = area_diagram.get_values()
        extended_stations = sorted(list(set(stations + area_diagram_stations)))
        interpolated_areas = np.interp(extended_stations, area_diagram_stations, areas_diagram_values)
        interpolated_widths = np.interp(extended_stations, stations, widths)
        
        def get_moment(As, b, d):
            if b <= 0:
                b = 1e-2 # 
            if fc <= 2800:
                B1 = 0.85
            else:
                B1 = 0.85 - (5e-4 / 7)*(fc-2800)
            Pb = 0.85 * B1 * (fc/fy) * (6e4/(6e4+fy))
            P = As/(b*d)
            def get_Phi():
                Es = 0.003 * (d-c)/c
                if Es<0.002:
                    Phi = 0.65
                elif Es < 0.005:
                    Phi = 0.483 + 83.3 * Es
                else:
                    Phi = 0.9
                return Phi
            if P < Pb:
                a = (As*fy)/(0.85*fc*b)
                Mn =  As*fy*(d-((As*fy)/(1.7*fc*b)))
            else:
                alpha = (6e4 * P *d) / (0.85 * fc)
                a = .5 * (math.sqrt(alpha**2 + 4*B1*d) - alpha)
                Mn = 0.85 * fc * a * b * (d-a/2)
            c = a/B1
            Phi = get_Phi()
            return Mn * Phi

        moments = [get_moment(interpolated_areas[i], interpolated_widths[i], self.section.effective_thickness)  for i in range(len(interpolated_areas))]
        return Diagram(stations=extended_stations, areas=moments)
    
    def get_drawing_data(self):
        return self.container.get_drawing_data()

    def _theoretical_to_executive(self):
        """process theoretical pieces to executive ones
        after this process they are ready to reduce their length type
        """
        def sub_process():
            """inserts practical and unifies until no unification happens.
            """
            while True:
                self._set_practical()
                is_unified = self._unify(by="practical")
                if is_unified:
                    self._refresh()
                else:
                    break
        # first set practical
        # then round and unify
        while True:
            sub_process()
            self._bend_stack_base()
            self._set_upper_bound()
            self._round()
            self._set_executive(by="practical")
            is_unified = self._unify(by="executive")
            if is_unified:
                self._refresh()
            else:
                break
    
    def refresh(self) -> None:
        self._refresh()
        self._theoretical_to_executive()

    def adjust_reduced_type_lengths(self) -> bool:
        """it is assumed that the length types are reduced and shortest piece length
        property is assigned.
        """
        self._set_executive(by="executive")
        is_unified = self._unify(by="executive")
        return is_unified
        
    def _get_min_gap(self):
        # get max station of original diagram
        max_station = self.diagram.get_max_point(self._get_bounds()).station
        # calculate number of additional rebars in max station
        additional_rebar_num = 0 # number of additional rebars
        for piece in self.container.get_pieces():
            if piece.executive.start <= max_station <= piece.executive.end:
                additional_rebar_num += 1
        # calculate min gap between rebars
        width = self.section.width - 2 * self.side_cover
        gap_length = max(0,width - (additional_rebar_num * (self.additional_rebar.get_diameter_mm() / 1000)) - (self.typical_rebar_num * (self.typical_rebar.get_diameter_mm() / 1000)))
        gap_num = self.typical_rebar_num + additional_rebar_num - 1
        if gap_num > 0:
            return gap_length / gap_num
        else:
            return float('inf')
    
    def _get_max_gap(self):
        # get min station of original diagram
        min_station = self.diagram.get_min_point(self._get_bounds()).station
        # calculate number of additional rebars in max station
        additional_rebar_num = 0 # number of additional rebars
        for piece in self.container.get_pieces():
            if piece.executive.start <= min_station <= piece.executive.end:
                additional_rebar_num += 1
        # calculate min gap between rebars
        width = self.section.width - 2 * self.side_cover
        gap_length = width - (additional_rebar_num * (self.additional_rebar.get_diameter_mm() / 1000)) - (self.typical_rebar_num * (self.typical_rebar.get_diameter_mm() / 1000))
        gap_num = self.typical_rebar_num + additional_rebar_num - 1
        if gap_num > 0:
            return gap_length / gap_num
        else:
            return float('-inf')
    
    def get_max_gap_warning(self):
        max_gap = round(self._get_max_gap(), 3)
        if max_gap > MAX_REBAR_GAP:
            return {
                'gap': max_gap,
                'max_gap': MAX_REBAR_GAP,
            }
        else:
            return None

    def get_min_gap_warning(self):
        min_gap = round(self._get_min_gap(),3) # in mm 
        output = {'gap': round(min_gap,3)}
        if min_gap < MIN_REBAR_GAP:
            output['error_type'] = 'MIN_GAP'
            output['min_gap'] = MIN_REBAR_GAP
        elif min_gap < min(self.typical_rebar.get_diameter_mm() /1000, self.additional_rebar.get_diameter_mm() /1000):
            output['error_type'] = 'REBAR_DIAMETER'
            output['min_gap'] = min(self.typical_rebar.get_diameter_mm() /1000, self.additional_rebar.get_diameter_mm() /1000)
        else:
            output['error_type'] = None
        return output
    
    def get_min_ratio_warning(self):
        if self.typical_type == 'typical':
            min_ratio_area = self.section.width * self.section.thickness * MIN_RATIO
            min_ratio_num = math.ceil(min_ratio_area/self.typical_rebar.get_area())
            if self.typical_rebar_num < min_ratio_num:
                return {
                    'num': self.typical_rebar_num,
                    'min_num': min_ratio_num
                }
            else:
                return None            
        else:
            return None
        
        


    