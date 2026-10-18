from .period import Period
from .mesh import Mesh, Section
from core.optimization.practical.stack import Stack
from .diagram import Diagram
from .rebar import Rebar, RebarType
from .piece import Piece
from .shear import ShearZone
import statistics

class Strip():
    def __init__(self,data_dict: dict):
        self.name = data_dict["name"]
        top_diagram = Diagram(data_dict["stations"], data_dict["design"]["flexural"]["top"])
        bottom_diagram = Diagram(data_dict["stations"], data_dict["design"]["flexural"]["bottom"])
        top_section = Section(
            statistics.median(data_dict["geometry"]["widths"]),
            data_dict["prop"]["thickness"],
            data_dict["prop"]["thickness"] - data_dict["geometry"]["covers"]["top"]
        )
        bottom_section = Section(
            statistics.median(data_dict["geometry"]["widths"]),
            data_dict["prop"]["thickness"],
            data_dict["prop"]["thickness"] - data_dict["geometry"]["covers"]["bottom"]
        )
        shear_diagram = Diagram(data_dict["stations"], data_dict["design"]["shear"])
        self._linearize_period(top_diagram, data_dict["column_sides"])
        self._linearize_period(bottom_diagram, data_dict["column_sides"])

        self._trim_period(shear_diagram, data_dict["strip_sides"], offset=data_dict["prop"]["thickness"])
        self._trim_period(shear_diagram, data_dict["column_sides"], offset=data_dict["prop"]["thickness"])

        self._linearize_period(top_diagram, data_dict["column_sides"])
        self._linearize_period(bottom_diagram, data_dict["column_sides"])

        self._top_ultimate_moment_diagram = Diagram(data_dict["stations"], data_dict["design"]["moment"]["top"])
        self._bottom_ultimate_moment_diagram = Diagram(data_dict["stations"], data_dict["design"]["moment"]["bottom"])
        self._linearize_period(self._top_ultimate_moment_diagram, data_dict["column_sides"])
        self._linearize_period(self._bottom_ultimate_moment_diagram, data_dict["column_sides"])

        self._material = {
            "fy": data_dict["prop"]["fy"],
            "fc": data_dict["prop"]["fc"],
        }

        self._geometry = {
            "thickness": data_dict["prop"]["thickness"] - data_dict["geometry"]["covers"]["bottom"] - data_dict["geometry"]["covers"]["top"],
            "widths": data_dict["geometry"]["widths"],
            "stations": data_dict["stations"]
        }

        self._shear_diagram = shear_diagram
        self._top_mesh = Mesh(top_diagram, top_section)
        self._bottom_mesh = Mesh(bottom_diagram, bottom_section)
        self._shear_zones = []

    def _linearize_period(self, diagram: Diagram, column_sides: list[list[float]]) -> None:
        for sides in column_sides:
            diagram.linearize_period(Period(sides[0], sides[1]))

    def _trim_period(self, diagram: Diagram, station_pairs: list[list[float]], offset: float) -> None:
        """reduces the given period to zero and minimizes the offsets to the value of each side
        Args:
            diagram (Diagram): [description]
            station_pairs (List[List[float]]): [description]
            offset (float): [description]
        """
        for pair in station_pairs:
            start = max(pair[0], diagram.get_bounds().start)
            end = min(pair[1], diagram.get_bounds().end)
            diagram.trim_period(Period(start, end))
            start_offset = max(pair[0] - offset, diagram.get_bounds().start)
            end_offset = min(pair[1] + offset, diagram.get_bounds().end)
            diagram.minimize_period(Period(start_offset, start), side="start")
            diagram.minimize_period(Period(end, end_offset), side="end")

    def set_side_cover(self, side_cover:float) -> None:
        self._bottom_mesh.set_side_cover(side_cover)
        self._top_mesh.set_side_cover(side_cover)

    def set_typical_rebar(
            self,
            data
        ) -> None:
        """
        Args:
            typical (RebarType): [description]
            additional (RebarType): [description]
        """
        material = self._material
        top_thermal_rebar = Rebar(data['top']['thermal_rebar_type'],material["fc"], material["fy"], "top")
        bottom_thermal_rebar = Rebar(data['bottom']['thermal_rebar_type'],material["fc"], material["fy"], "bottom")
        top_typical_rebar = Rebar(data['top']['typical_rebar_type'],material["fc"], material["fy"], "top")
        bottom_typical_rebar = Rebar(data['bottom']['typical_rebar_type'], material["fc"], material["fy"], "bottom")
        self._top_mesh.set_typical_rebar(top_typical_rebar, top_thermal_rebar, data['bottom']['method'])
        self._bottom_mesh.set_typical_rebar(bottom_typical_rebar, bottom_thermal_rebar, data['top']['method'])

    def set_additional_rebar(self, rebar_type: Rebar, elimination: float) -> None:
        material = self._material
        top_rebar = Rebar(rebar_type, material["fc"], material["fy"], "top")
        bottom_rebar = Rebar(rebar_type, material["fc"], material["fy"], "bottom")
        self._top_mesh.set_additional_rebar(top_rebar, elimination)
        self._bottom_mesh.set_additional_rebar(bottom_rebar, elimination)

    def get_additional_pieces(self) -> Iterator[Piece]:
        for pieces in (self._top_mesh.get_additional_pieces(), self._bottom_mesh.get_additional_pieces()):
            for piece in pieces:
                yield piece

    def get_stacks(self) -> Iterator[Stack]:
        return {
            "top": self._top_mesh.get_stacks(),
            "bottom": self._bottom_mesh.get_stacks(),
        }

    def refresh(self):
        self._top_mesh.refresh()
        self._bottom_mesh.refresh()

    def set_shear(self, elimination: float) -> None:
        periods = self._shear_diagram.get_periods()
        for period in periods:
            if period.get_length() > elimination:
                self._shear_zones.append(ShearZone(period, self._shear_diagram.get_max_point(period).area, self._geometry["thickness"]))

    def get_shear_zones(self) -> List[ShearZone]:
        return self._shear_zones

    def adjust_reduced_type_lengths(self) -> bool:
        return any((
            self._top_mesh.adjust_reduced_type_lengths(),
            self._bottom_mesh.adjust_reduced_type_lengths()
        ))

    def get_resistance_moment(self) -> dict:
        top_diagram = self._top_mesh.get_resistance_moment_diagram(self._geometry["widths"], self._geometry["stations"], self._material["fy"], self._material["fc"])
        bottom_diagram = self._bottom_mesh.get_resistance_moment_diagram(self._geometry["widths"], self._geometry["stations"], self._material["fy"], self._material["fc"])
        return {
            "top": {
                "stations": top_diagram.get_stations(),
                "values": top_diagram.get_values()
            },
            "bottom": {
                "stations": bottom_diagram.get_stations(),
                "values": bottom_diagram.get_values()
            }
        }

    def get_ultimate_moment(self) -> dict:
        top_diagram = self._top_ultimate_moment_diagram
        bottom_diagram = self._bottom_ultimate_moment_diagram
        return {
            "top": {
                "stations": top_diagram.get_stations(),
                "values": top_diagram.get_values()
            },
            "bottom": {
                "stations": bottom_diagram.get_stations(),
                "values": bottom_diagram.get_values()
            }
        }

    def get_additional_piece_rows(self) -> dict:
        return {
            "top": self._top_mesh.get_piece_rows(),
            "bottom": self._bottom_mesh.get_piece_rows()
        }

    def get_drawing_data(self) -> dict:
        return {
            "top": self._top_mesh.get_drawing_data(),
            "bottom": self._bottom_mesh.get_drawing_data()
        }

    def get_typical_pieces(self) -> dict:
        return {
            "top": {
                "piece": self._top_mesh.get_typical_piece(),
                "number": self._top_mesh.typical_rebar_num,
                "type": self._top_mesh.typical_type
            },
            "bottom": {
                "piece": self._bottom_mesh.get_typical_piece(),
                "number": self._bottom_mesh.typical_rebar_num,
                "type": self._bottom_mesh.typical_type
            }
        }

    def get_min_gap_warning(self):
        return {
            "top": self._top_mesh.get_min_gap_warning(),
            "bottom": self._bottom_mesh.get_min_gap_warning()
        }

    def get_min_ratio_warning(self):
        return {
            'top': self._top_mesh.get_min_ratio_warning(),
            'bottom': self._bottom_mesh.get_min_ratio_warning()
        }

    def get_max_gap_warning(self):
        return {
            'top': self._top_mesh.get_max_gap_warning(),
            'bottom': self._bottom_mesh.get_max_gap_warning(),
        }
