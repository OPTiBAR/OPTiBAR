from __future__ import annotations
from typing import List
from .diagram import Diagram
from .collections import Container, Stack
from .piece import Piece, Bend
from .rebar import Rebar
from optibar.core.optimization.required import DominationType, RequiredOptimization
from .period import Period
from .utilities import round_down, round_up
import math
from typing import Union, Iterator
from optibar.core.setting import MAX_REBAR_GAP, MIN_RATIO, THERMAL_MIN_RATIO, ROUND_UNIT, STANDARD_LENGTH, MIN_REBAR_GAP
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
            arrangement: dict[str,str|float]
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
        the process of generating practical lengths is called here.

        Args:
            additional_rebar (Rebar): rebar

        """
        self.additional_rebar = additional_rebar
        self._insert_additional(additional_elimination)
        self._theoretical_to_practical()

    def get_typical_piece(self) -> Piece:
        period = self._get_bounds()
        period.start -= self.typical_rebar.get_bend_length()
        period.end += self.typical_rebar.get_bend_length()
        # period.end = period.start + round_down(period.end - period.start, ROUND_UNIT)
        piece = Piece(self.typical_rebar, period)
        piece.bend.start = self.typical_rebar.get_bend_length()
        piece.bend.end = self.typical_rebar.get_bend_length()
        piece.required = period
        self._set_piece_upper_bound(piece)
        self._round_piece(piece)
        self._set_piece_practical(piece)
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

    def _set_required(self) -> None:
        """gets stacks from container and adds optimized required lengths to them.
        """
        for stack in self.container.get_stacks("theoretical"):
            RequiredOptimization(stack, d_length=self.section.effective_thickness, ld_length=self.additional_rebar.get_ld())

    def _bend(self) -> None:
        """if theoretical length has exceeded the bounds it should be bended
        if required length has exceeded the bounds, if domination is Ld it should be bended
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
            piece.required.start = piece.theoretical.start
        if piece.theoretical.end > bounds.end:
            piece.bend.end = bend_length
            piece.theoretical.end = bounds.end + bend_length
            piece.required.end = piece.theoretical.end
        # required exceed
        if piece.required.start < bounds.start and piece.bend.start == 0:
            if piece.domination.start == DominationType.D:
                piece.required.start = bounds.start
            else: # piece.domination.start == Domination.LD
                piece.bend.start = bend_length
                piece.required.start = bounds.start - bend_length
        if piece.required.end > bounds.end and piece.bend.end == 0:
            if piece.domination.end == DominationType.D:
                piece.required.end = bounds.end
            else: # piece.domination.end == Domination.LD
                piece.bend.end = bend_length
                piece.required.end = bounds.end + bend_length

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
                    piece.required.start = piece.theoretical.start
                if piece.theoretical.end > bounds.end:
                    piece.bend.end = bend_length
                    piece.theoretical.end = bounds.end + bend_length
                    piece.required.end = piece.theoretical.end
                # required exceed
                if (piece.required.start < bounds.start and piece.bend.start == 0):
                    if piece.domination.start == DominationType.LD or (i > 0 and pieces[i-1].bend.start > 0):
                        piece.bend.start = bend_length
                        piece.required.start = bounds.start - bend_length
                    else:
                        piece.required.start = bounds.start

                if (piece.required.end > bounds.end and piece.bend.end == 0):
                    if piece.domination.end == DominationType.LD or (i > 0 and pieces[i-1].bend.end > 0):
                        piece.bend.end = bend_length
                        piece.required.end = bounds.end + bend_length
                    else:
                        piece.required.end = bounds.end

    def _set_upper_bound(self) -> None:
        """sets the upper bound property for all the pieces
        """
        for piece in self.container.get_pieces():
            self._set_piece_upper_bound(piece)

    def _set_piece_upper_bound(self, piece:Piece) -> None:
        """sets the length_upper_bound property
        """
        if piece.get_num_of_pieces("required") > 1:
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
        length = piece.get_shortest_piece_length("required")
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
            by (str): could be required or practical
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
            by (str): could be required or practical
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

    def _set_practical(self, by: str):
        """sets practical period of all pieces, based on their shortest piece length
        and considers stack of pieces according to their <by>(required or practical) property.

        Args:
            by (str): could be required or practical
        """
        for stack in self.container.get_stacks(by=by):
            pieces = list(reversed(stack.get_pieces())) # longer to shorter
            for i in range(len(stack)):
                if i == 0:
                    self._set_piece_practical(piece= pieces[i])
                else:
                    self._set_piece_practical(piece= pieces[i], base_piece= pieces[i-1])

    def _set_piece_practical(self, piece: Piece, base_piece: Piece= None):
        """set practical period based on shortest_piece_length property.
        See the "Adjusting the length of a piece" algorithm in docs/source/explanation/practical.md.

        A piece or base piece bent only at the end is mirrored (x -> -x) so that
        `_place_piece` only has to handle bends at the start.

        Args:
            base_piece (Piece, optional): the base piece to be considered to revise length.
                Defaults to None.
        """
        delta = piece.shortest_piece_length - piece.get_shortest_piece_length("required")
        required = piece.required

        if piece.bend.start > 0 and piece.bend.end > 0:
            # bent at both ends: already as long as it can be, so it can only get shorter
            if delta <= 0:
                required.end += delta
            piece.practical = Period(required.start, required.end)
            return

        if piece.bend.start == 0 and piece.bend.end == 0 and delta < 0:
            # not bent, shorter: take the same amount off both ends
            start = required.start - delta/2
            end = required.end + delta/2
            required.start = start
            required.end = end
            if piece.theoretical.start < start:
                piece.theoretical.start = start
            if piece.theoretical.end > end:
                piece.theoretical.end = end
            piece.practical = Period(start, end)
            return

        base_bend = base_piece.bend if base_piece is not None else Bend()
        flip = piece.bend.end > 0 or (
            piece.bend.start == 0 and base_bend.start == 0 and base_bend.end > 0)
        if flip:
            frame = lambda p: Period(-p.end, -p.start)
            swap = lambda b: Bend(b.end, b.start)
        else:
            frame = lambda p: Period(p.start, p.end)
            swap = lambda b: Bend(b.start, b.end)

        local_required = frame(required)
        local_bend = swap(piece.bend)
        practical, takes_base_length = _place_piece(
            required=local_required,
            bend=local_bend,
            delta=delta,
            bounds=frame(self._get_bounds()),
            base=frame(base_piece.practical) if base_piece is not None else None,
            base_bend=swap(base_bend),
            bend_length=piece.rebar.get_bend_length(),
        )

        # write back in place: required may be the same object as theoretical
        new_required = frame(local_required)
        required.start, required.end = new_required.start, new_required.end
        new_bend = swap(local_bend)
        piece.bend.start, piece.bend.end = new_bend.start, new_bend.end
        if takes_base_length:
            piece.shortest_piece_length = base_piece.shortest_piece_length
        piece.practical = frame(practical)

    def get_stacks(self) -> list[Stack]:
        """returns list if stacks based on their practical period
        """
        return self.container.get_stacks(by="practical")

    def get_additional_pieces(self) -> Iterator[Piece]:
        """return an Iterator over all the pieces

        Returns:
            List[Piece]: list of pieces
        """
        return self.container.get_pieces()

    def get_piece_rows(self) -> list[list[Piece]]:
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
                stations = [piece.practical.end - piece.rebar.get_ld(), piece.practical.end]
            elif piece.bend.start == 0 and piece.bend.end > 0:
                stations = [piece.practical.start, piece.practical.start + piece.rebar.get_ld()]
            else: # piece.bend.start == 0 and piece.bend.end == 0
                stations = [
                    piece.practical.start, piece.practical.start + piece.rebar.get_ld(),
                    piece.practical.end - piece.rebar.get_ld(), piece.practical.end
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
            widths: list[float],
            stations: list[float],
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

    def _theoretical_to_practical(self):
        """process theoretical pieces to practical ones
        after this process they are ready to reduce their length type
        """
        def sub_process():
            """inserts required and unifies until no unification happens.
            """
            while True:
                self._set_required()
                is_unified = self._unify(by="required")
                if is_unified:
                    self._refresh()
                else:
                    break
        # first set required
        # then round and unify
        while True:
            sub_process()
            self._bend_stack_base()
            self._set_upper_bound()
            self._round()
            self._set_practical(by="required")
            is_unified = self._unify(by="practical")
            if is_unified:
                self._refresh()
            else:
                break

    def refresh(self) -> None:
        self._refresh()
        self._theoretical_to_practical()

    def adjust_reduced_type_lengths(self) -> bool:
        """it is assumed that the length types are reduced and shortest piece length
        property is assigned.
        """
        self._set_practical(by="practical")
        is_unified = self._unify(by="practical")
        return is_unified

    def _get_min_gap(self):
        # get max station of original diagram
        max_station = self.diagram.get_max_point(self._get_bounds()).station
        # calculate number of additional rebars in max station
        additional_rebar_num = 0 # number of additional rebars
        for piece in self.container.get_pieces():
            if piece.practical.start <= max_station <= piece.practical.end:
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
            if piece.practical.start <= min_station <= piece.practical.end:
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


def _snap_or_center(required: Period, delta: float, limits: Period) -> Period:
    """lengthens `required` by `delta` inside `limits`.
    If adding all of `delta` to one end reaches that limit, the piece is aligned
    with it and the rest goes to the other end; otherwise both ends get delta/2.
    """
    length = required.get_length()
    if required.start - delta <= limits.start:
        start = limits.start
        return Period(start, min(start + length + delta, limits.end))
    if required.end + delta >= limits.end:
        end = limits.end
        return Period(max(end - length - delta, limits.start), end)
    return Period(required.start - delta/2, required.end + delta/2)


def _place_piece(
        required: Period,
        bend: Bend,
        delta: float,
        bounds: Period,
        base: Period | None,
        base_bend: Bend,
        bend_length: float,
    ) -> tuple[Period, bool]:
    """places a piece that is not bent at its end, and whose base piece, if the piece
    is not bent, is not bent only at its end. The caller mirrors the other cases.
    Changes `required` and `bend` in place where the piece gets bent.

    Returns:
        the practical period, and whether the piece takes the length of the base piece.
    """
    length = required.get_length()

    if bend.start > 0:
        # bent at the start: only the end moves
        if delta < 0:
            required.end += delta
            return Period(required.start, required.end), False
        if base is None:
            return Period(required.start, min(required.end + delta, bounds.end)), False
        if base_bend.end > 0:
            if required.end + delta >= base.end:
                # reaches the bent end of the base piece: bend there too
                bend.end = bend_length
                required.end = base.end
                return Period(required.start, base.end), False
            return Period(required.start, min(required.end + delta, bounds.end)), False
        return Period(required.start, min(required.end + delta, base.end, bounds.end)), False

    # not bent, longer
    if base is None or (base_bend.start > 0 and base_bend.end > 0):
        return _snap_or_center(required, delta, bounds), False
    if base_bend.start == 0:
        return _snap_or_center(required, delta, base), False

    # the base piece is bent only at the start
    reaches_base_end = required.end + delta >= base.end
    if reaches_base_end and base.end - length - delta >= bounds.start:
        # align with the unbent end of the base piece
        return Period(base.end - length - delta, base.end), False
    if required.start - delta <= bounds.start - bend_length:
        # long enough to reach the side and be bent there
        bend.start = bend_length
        start = bounds.start - bend_length
        required.start = start
        return Period(start, min(start + length + delta, base.end)), False
    if reaches_base_end:
        # aligned with the base piece it would pass the side: copy the base piece
        bend.start = bend_length
        required.start = base.start
        return Period(base.start, base.end), True
    # reaches neither end
    if required.start - delta/2 >= bounds.start:
        return Period(required.start - delta/2, required.end + delta/2), False
    start = bounds.start
    return Period(start, start + length + delta), False
