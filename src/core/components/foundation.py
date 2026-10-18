from .config import Config
from .shear import ShearType, ShearZone
from typing import Iterator
from .rebar import RebarType, Rebar
from .strip import Strip
from .piece import Piece
from .collections import Bunch
from core.optimization.practical.practical import ExecutiveOptimization
from core.optimization.practical.errors import NotEnoughTypes
from core.optimization.shear import ShearOptimization, ShearType
from core.io.input import InputInterpreter
from .utilities import round_up
import math

class Foundation():
    def __init__(self, input: InputInterpreter):
        strips = []
        self._strips: List[Strip] = strips
        self._shear_types = []
        self.input = input
        self.config = None

        self.errors: Dict = {}
        self.warnings: Dict = {} # keys may be 'min_gap', 'min_ratio' and 'excess_stack'
        for strip_data in input.get_strips():
            strips.append(Strip(strip_data))

    def _set_side_cover(self, side_cover: float) -> None:
        for strip in self._strips:
            strip.set_side_cover(side_cover)

    def _set_typical_rebar(self, typical_rebar_type: RebarType, thermal_rebar_type: RebarType, typical_arrangement):
        general_method = {
            'method': typical_arrangement['method'],
            'value' : typical_arrangement['value'],
        }
        for strip in self._strips:
            strip_data = {
                'top': {
                    'method':general_method,
                    'typical_rebar_type': typical_rebar_type,
                    'thermal_rebar_type': thermal_rebar_type,
                },
                'bottom': {
                    'method':general_method,
                    'typical_rebar_type': typical_rebar_type,
                    'thermal_rebar_type': thermal_rebar_type,
                },
            }
            if strip.name in typical_arrangement['exceptions']:
                for level in typical_arrangement['exceptions'][strip.name]:
                    special_method = {
                        'method': typical_arrangement['exceptions'][strip.name][level]['method'],
                        'value': typical_arrangement['exceptions'][strip.name][level]['value'],
                    }
                    strip_data[level] = {
                        'method': special_method,
                        'typical_rebar_type': RebarType(typical_arrangement['exceptions'][strip.name][level]['diameter']),
                        'thermal_rebar_type': thermal_rebar_type,
                    }
            strip.set_typical_rebar(strip_data)

    def _set_additional_rebar(self, rebar_type: RebarType, elimination: float):
        for strip in self._strips:
            strip.set_additional_rebar(rebar_type, elimination)

    def _set_shear_rebar(self, rebar_type: RebarType, shear_elimination: float, number_of_types: int):
        max_interval = self.input.get_min_thickness()/2
        shear_rebar = Rebar(rebar_type)
        shear_zones = []
        for strip in self._strips:
            strip.set_shear(shear_elimination)
            shear_zones.extend(strip.get_shear_zones())
        so = ShearOptimization(shear_rebar, max_interval, shear_zones, number_of_types)
        so.run()
        self._shear_types = so.get_shear_types()

    def get_shear_types(self) -> List[ShearType]:
        return self._shear_types

    def get_strip_shear_zones(self) -> List[List[ShearZone]]:
        shear_zones = []
        for strip in self._strips:
            shear_zones.append(strip.get_shear_zones())
        return shear_zones

    def _set_length_type_num(self, total_num_of_types, stack_num_of_types):
        def get_pieces():
            for strip in self._strips:
                for piece in strip.get_additional_pieces():
                    yield piece
        def get_stacks():
            stack_dict = {}
            for strip in self._strips:
                stack_dict[strip.name] = strip.get_stacks()
            return stack_dict
        while True:
            is_unified = False
            eo = ExecutiveOptimization(get_pieces(), get_stacks(), total_num_of_types, stack_num_of_types)
            try:
                stack_excess_list = eo.run()
                if len(stack_excess_list) > 0:
                    self.warnings['excess_stack'] = stack_excess_list
                # if len(excess_stack_type_dict.keys()) > 0:
                #     self.warnings = "Number of length types of some stacks had to be more than the given number: \n" + \
                #         '\n'.join([f"{strip_name}: {' '.join(map(str, excess_stack_type_dict[strip_name]))}"for strip_name in excess_stack_type_dict])
            except NotEnoughTypes as e:
                self.errors['total_type_num'] = {
                    'num': total_num_of_types,
                    'min_feasible_num': e.min_feasible_type_num
                }
                break

            for strip in self._strips:
                if strip.adjust_reduced_type_lengths():
                    is_unified = True
            if is_unified:
                for strip in self._strips:
                    strip.refresh()
            else:
                break

    def get_additional_subpieces(self) -> Iterator[Piece]:
        strips = []
        for i,strip in enumerate(self._strips):
            strip_dict = strip.get_additional_piece_rows()
            strips.append({
                "top": [[subpiece for piece in row for subpiece in piece.get_subpieces()] for row in strip_dict["top"]],
                "bottom": [[subpiece for piece in row for subpiece in piece.get_subpieces()] for row in strip_dict["bottom"]]
            })
        return strips

    def get_drawing_data(self) -> List[Dict[str,List[List[Bunch]]]]:
        return [strip.get_drawing_data() for strip in self._strips]

    def get_typical_subpieces(self) -> Iterator[Piece]:
        strips = []
        for strip in self._strips:
            strip_dict = strip.get_typical_pieces()
            strips.append({
                "top": {
                    "subpieces": strip_dict["top"]["piece"].get_subpieces(),
                    "number": strip_dict["top"]["number"],
                    "type": strip_dict["top"]["type"]
                },
                "bottom": {
                    "subpieces": strip_dict["bottom"]["piece"].get_subpieces(),
                    "number": strip_dict["bottom"]["number"],
                    "type": strip_dict["bottom"]["type"]
                }
            })
        return strips

    def _get_min_gap_warning(self) -> List[Dict]:
        output = []
        for strip in self._strips:
            strip_min_gap_warning = strip.get_min_gap_warning()
            for level in strip_min_gap_warning:
                if strip_min_gap_warning[level]["error_type"] is not None:
                    output.append({
                        'strip_name': strip.name,
                        'level': level,
                        'detail': strip_min_gap_warning[level]
                    })
        return output

    def _set_min_gap_warning(self) -> None:
        min_gap_warnings = self._get_min_gap_warning()
        if len(min_gap_warnings) > 0:
            self.warnings['min_gap'] = min_gap_warnings

    def _get_min_ratio_warning(self) -> List[Dict]:
        output = []
        for strip in self._strips:
            strip_min_ratio_warning = strip.get_min_ratio_warning()
            for level in strip_min_ratio_warning:
                if strip_min_ratio_warning[level] is not None:
                    output.append({
                        'strip_name': strip.name,
                        'level': level,
                        'detail': strip_min_ratio_warning[level]
                    })
        return output

    def _set_min_ratio_warning(self) -> None:
        min_ratio_warnings = self._get_min_ratio_warning()
        if len(min_ratio_warnings) > 0:
            self.warnings['min_ratio'] = min_ratio_warnings

    def _get_max_gap_warning(self):
        output = []
        for strip in self._strips:
            strip_max_gap_warning = strip.get_max_gap_warning()
            for level in strip_max_gap_warning:
                if strip_max_gap_warning[level] is not None:
                    output.append({
                        'strip_name': strip.name,
                        'level': level,
                        'detail': strip_max_gap_warning[level]
                    })
        return output

    def _set_max_gap_warning(self) -> None:
        max_gap_warnings = self._get_max_gap_warning()
        if len(max_gap_warnings) > 0:
            self.warnings['max_gap'] = max_gap_warnings

    def _set_warning(self):
        self._set_max_gap_warning()
        self._set_min_gap_warning()
        self._set_min_ratio_warning()

    def get_shear_piece_list(self):
        piece_list = []
        for shear_zones in self.get_strip_shear_zones():
            for shear_zone in shear_zones:
                bend_length_135 = shear_zone.shear_type.rebar.get_bend_length(degree=135)
                bend_length_90 = shear_zone.shear_type.rebar.get_bend_length(degree=90)
                length = round_up(shear_zone.thickness + bend_length_135 + bend_length_90, 0.01)
                number = shear_zone.shear_type.number * math.ceil(shear_zone.period.get_length()/ shear_zone.shear_type.interval)
                piece_list.append({
                    "rebar": shear_zone.shear_type.rebar,
                    "number": number,
                    "length": length
                })
        return piece_list

    def get_strips_resistance_moment(self):
        strips = []
        for strip in self._strips:
            strips.append(strip.get_resistance_moment())
        return strips

    def get_strips_ultimate_moment(self):
        strips = []
        for strip in self._strips:
            strips.append(strip.get_ultimate_moment())
        return strips


    def run(self, config: Config) -> None:
        self.config = config
        Rebar.special_lengths = config.special_lengths
        self._set_side_cover(config.side_cover)
        self._set_typical_rebar(config.typical_rebar_type, config.thermal_rebar_type, config.typical_arrangement)
        self._set_additional_rebar(config.additional_rebar_type, config.reinfordement_elimination)
        self._set_shear_rebar(config.shear_rebar_type, config.shear_elimination, config.shear_type_number)
        self._set_length_type_num(config.total_type_number, config.stack_type_number)
        self._set_warning()
