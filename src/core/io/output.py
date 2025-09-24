from core.components.utilities import round_down
from core.components.rebar import Rebar, RebarType
from core.components.foundation import Foundation
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from core.setting import SIDE_COVER, STEEL_DENSITY
from core.components.config import Config
import math

class Output():
    def __init__(self, foundation: Foundation) -> None:
        self._parsed_data = foundation.input.parsed_data
        self._config = foundation.config
        self._foundation = foundation

        self._shear_piece_list = None
        self._reinforceent_subpieces = None
        self._typical_subpieces = None
        self._set_pieces()

    def _set_pieces(self):
        self._shear_piece_list = self._foundation.get_shear_piece_list()
        self._reinforceent_subpieces = self._foundation.get_additional_subpieces()
        self._typical_subpieces = self._foundation.get_typical_subpieces()

    # areas
    def _get_areas(self):# -> dict:
        individuals = []
        polygons = []
        opening_polygons = []
        for area in self._parsed_data["areas"]:
            individual = {
                "name": area["name"],
                "corners": area["corners"],
            }
            individuals.append(individual)
            if not area["is_opening"]:
                polygons.append(Polygon(area["corners"]))
                individual["is_opening"] = False
                individual["thickness"] = area["prop"]["thickness"]
            else:
                opening_polygons.append(Polygon(area["corners"]))
                individual["is_opening"] = True

        union_polygon = unary_union(polygons) - unary_union(opening_polygons)
        interiors = []
        exteriors = []
        # make union_polygon iterable
        if isinstance(union_polygon,Polygon): # not iterable multipolygon
            union_polygon = [union_polygon]
        for polygon in union_polygon:
            exteriors.append(list(map(list,polygon.exterior.coords[:])))
            for interior in polygon.interiors:
                interiors.append(list(map(list,interior.coords[:])))

        return {
            "individuals": individuals,
            "union": {
                "exteriors": exteriors,
                "interiors": interiors
            }
        }

    # columns
    def _get_columns(self) -> Dict:

        return self._parsed_data["columns"]

    # technical_spec
    def _get_material(self)-> Dict:
        fy = None
        if len(self._parsed_data["strips"]) > 0:
            fy = self._parsed_data["strips"][0]["fy"]

        fc = None
        for area in self._parsed_data["areas"]:
            if not area['is_opening']:
                fc = area["prop"]["fc"]
                break
        # if len(self._parsed_data["areas"]) > 0:
        #     fc = self._parsed_data["areas"][0]["prop"]["fc"]
        return {
            "fy": fy,
            "fc": fc
        }

    # technical_spec
    def _get_covers(self) -> Dict:
        top = None
        bottom = None
        if len(self._parsed_data["strips"]) > 0:
            top = self._parsed_data["strips"][0]["geometry"]["covers"]["top"]
            bottom = self._parsed_data["strips"][0]["geometry"]["covers"]["bottom"]
        return {
            "side": SIDE_COVER,
            "top": top,
            "bottom": bottom,
        }

    # technical_spec
    def _get_rebars(self) -> Dict:
        # typical = self._config.typical_rebar_type
        # additional = self._config.additional_rebar_type
        # shear = self._config.shear_rebar_type
        # thermal = self._config.thermal_rebar_type
        material = self._get_material()
        def get_dict(rebar_type):
            return {
                "diameter": rebar_type.value,
                "bend": {
                    "B90": Rebar.calc_bend_legth(rebar_type, 90),
                    "B135": Rebar.calc_bend_legth(rebar_type, 135)
                },
                "Ld": {
                    "top": Rebar.calc_ld(material["fc"], material["fy"], rebar_type, "top"),
                    "bottom": Rebar.calc_ld(material["fc"], material["fy"], rebar_type, "bottom")
                },
                "overlap": {
                    "top": Rebar.calc_overlap_length(material["fc"], material["fy"], rebar_type, "top"),
                    "bottom": Rebar.calc_overlap_length(material["fc"], material["fy"], rebar_type, "bottom")
                }
            }
        return [ get_dict(rebar_type) for rebar_type in RebarType]

    # technical_spec
    def _get_length_type(self) -> Dict:
        return {
            "total": self._config.total_type_number,
            "stack": self._config.stack_type_number
        }

    # technical_spec
    def _get_technical_spec(self) -> Dict:
        return {
            "material": self._get_material(),
            "covers": self._get_covers(),
            "rebars": self._get_rebars(),
            "length_type": self._get_length_type()
        }

    # pieces
    def _get_typical_thermal_piece_list(self) -> Dict:
        typical_dict = {}
        thermal_dict = {}
        for strip_dict in self._typical_subpieces:
            for piece_dict in (strip_dict["top"], strip_dict["bottom"]):
                number = piece_dict["number"]
                for subpiece in piece_dict["subpieces"]:
                    length = round(subpiece.executive.get_length(),2)
                    diameter = subpiece.rebar.get_diameter_mm()
                    no_side = 0
                    one_side = 0
                    two_side = 0
                    if subpiece.bend.start > 0 and subpiece.bend.end > 0:
                        two_side += number
                    elif (subpiece.bend.start > 0 and subpiece.bend.end == 0) or (subpiece.bend.start == 0 and subpiece.bend.end > 0):
                        one_side += number
                    else:
                        no_side += number
                    new_dict = {
                        "diameter": diameter,
                        "length": length,
                        "number": 0,
                        "bend": {
                            "one_side": 0,
                            "two_side": 0,
                            "no_side": 0
                        }
                    }
                    if piece_dict["type"] == 'typical' :
                        if length in typical_dict:
                            selected_dict = typical_dict[length]
                        else:
                            typical_dict[length] = new_dict
                            selected_dict = new_dict

                    if piece_dict["type"] == 'thermal':
                        if length in thermal_dict:
                            selected_dict = thermal_dict[length]
                        else:
                            thermal_dict[length] = new_dict
                            selected_dict = new_dict

                    selected_dict["number"] += number
                    selected_dict["bend"]["no_side"] += no_side
                    selected_dict["bend"]["one_side"] += one_side
                    selected_dict["bend"]["two_side"] += two_side

        return {
            "typical": [typical_dict[length] for length in sorted(typical_dict.keys())],
            "thermal": [thermal_dict[length] for length in sorted(thermal_dict.keys())]
        }

    # pieces
    def _get_additional_piece_list(self) -> List:
        piece_dict = {}
        for strip in self._reinforceent_subpieces:
            for row in strip["top"]+strip["bottom"]:
                for subpiece in row:
                    diameter = subpiece.rebar.rebar_type.value
                    length = round(subpiece.executive.get_length(),2)
                    no_side = 0
                    one_side = 0
                    two_side = 0
                    if subpiece.bend.start > 0 and subpiece.bend.end > 0:
                        two_side += 1
                    elif (subpiece.bend.start > 0 and subpiece.bend.end == 0) or (subpiece.bend.start == 0 and subpiece.bend.end > 0):
                        one_side = 1
                    else:
                        no_side += 1

                    new_dict = {
                        "diameter": diameter,
                        "length": length,
                        "number": 0,
                        "bend": {
                            "one_side": 0,
                            "two_side": 0,
                            "no_side": 0
                        }
                    }

                    if length in piece_dict:
                        selected_dict = piece_dict[length]
                    else:
                        piece_dict[length] = new_dict
                        selected_dict = new_dict
                    selected_dict["number"] += 1
                    selected_dict["bend"]["no_side"] += no_side
                    selected_dict["bend"]["one_side"] += one_side
                    selected_dict["bend"]["two_side"] += two_side
        return [piece_dict[length] for length in sorted(piece_dict.keys())]

    # pieces
    def _get_shear_piece_list(self) -> List:
        piece_dict = {}
        for shear_zone in self._shear_piece_list:
            rebar = shear_zone["rebar"]
            number = shear_zone["number"]
            length = round(shear_zone["length"],2)
            new_dict = {
                "diameter": rebar.rebar_type.value,
                "number": 0,
                "length": length
            }
            if length in piece_dict:
                selected_dict = piece_dict[length]
            else:
                piece_dict[length] = new_dict
                selected_dict = new_dict
            selected_dict["number"] += number
        return list(piece_dict.values())

    # pieces
    def _get_pieces(self) -> List:
        typical_thermal = self._get_typical_thermal_piece_list()
        additional = self._get_additional_piece_list()
        shear = self._get_shear_piece_list()
        return {
            "typical": typical_thermal["typical"],
            "thermal": typical_thermal["thermal"],
            "additional": additional,
            "shear": shear
        }

    # summery
    def _get_concrete_volume(self) -> float:
        volume = 0
        for area in self._parsed_data["areas"]:
            if not area["is_opening"]:
                volume += Polygon(area["corners"]).area * area["prop"]["thickness"]
        return round(volume,1)

    # summery
    def _get_additional_mass(self) -> Dict[str,float]:
        """returns mass in ton with three decimal digits

        Returns:
            Dict[str,float]: mass of top and bottom additional rebar
        """
        top_mass = 0
        bottom_mass = 0
        for strip_dict in self._reinforceent_subpieces:
            for row in strip_dict["top"]:
                for piece in row:
                    top_mass += piece.rebar.get_area() * piece.executive.get_length() * STEEL_DENSITY
            for row in strip_dict["bottom"]:
                for piece in row:
                    bottom_mass += piece.rebar.get_area() * piece.executive.get_length() * STEEL_DENSITY
        return {
            "top": round(top_mass,3),
            "bottom": round(bottom_mass,3)
        }

    # summery
    def _get_shear_mass(self) -> float:
        """shear rebar mass in ton with three decimal digits
        """
        mass = 0
        for shear_zone in self._shear_piece_list:
            mass += shear_zone["length"] * shear_zone["number"] * shear_zone["rebar"].get_area() * STEEL_DENSITY
        return round(mass,3)

    # summery
    def _get_typical_thermal_mass(self):
        mass_dict = {
            "typical": {
                "top": 0,
                "bottom": 0
            },
            "thermal": {
                "top": 0,
                "bottom": 0
            }
        }
        for strip_dict in self._typical_subpieces:
            for piece in strip_dict["top"]["subpieces"]:
                piece_mass = piece.rebar.get_area() * piece.executive.get_length() * strip_dict["top"]["number"] * STEEL_DENSITY
                if strip_dict["top"]["type"] == 'typical':
                    mass_dict["typical"]["top"] += piece_mass
                elif strip_dict["top"]["type"] == 'thermal':
                    mass_dict["thermal"]["top"] += piece_mass
                else:
                    raise ValueError(f'not defined rebar type {strip_dict["top"]["type"]}')
            for piece in strip_dict["bottom"]["subpieces"]:
                piece_mass = piece.rebar.get_area() * piece.executive.get_length() * strip_dict["bottom"]["number"] * STEEL_DENSITY
                if strip_dict["bottom"]["type"] == 'typical':
                    mass_dict["typical"]["bottom"] += piece_mass
                elif strip_dict["bottom"]["type"] == 'thermal':
                    mass_dict["thermal"]["bottom"] += piece_mass
                else:
                    raise ValueError(f'not defined rebar type {strip_dict["bottom"]["type"]}')

            # round to kg
            mass_dict["typical"]["top"] = round(mass_dict["typical"]["top"],3)
            mass_dict["typical"]["bottom"] = round(mass_dict["typical"]["bottom"],3)
            mass_dict["thermal"]["top"] = round(mass_dict["thermal"]["top"],3)
            mass_dict["thermal"]["bottom"] = round(mass_dict["thermal"]["bottom"],3)
        return mass_dict

    # summery
    def _get_rebar_mass(self):
        additional = self._get_additional_mass()
        shear = self._get_shear_mass()
        typical_thermal = self._get_typical_thermal_mass()
        return {
            "typical": typical_thermal["typical"],
            "thermal": typical_thermal["thermal"],
            "additional": additional,
            "shear": shear
        }

    # summery
    def _get_summary(self):
        return {
            "rebar": self._get_rebar_mass(),
            "concrete": self._get_concrete_volume()
        }

    # shear_types
    def _get_shear_types(self) -> List[Dict]:
        shera_types = self._foundation.get_shear_types()
        return [
            {
                "id": shear_type.id,
                "interval": shear_type.interval,
                "number": shear_type.number,
                "diameter": shear_type.rebar.get_diameter_mm()
            } for shear_type in shera_types
        ]

    #strips
    def _get_strips_name(self):
        strips = []
        for strip in self._parsed_data["strips"]:
            strips.append(strip["name"])
        return strips

    #strips
    def _get_strips_covers(self):
        strips = []
        for strip in self._parsed_data["strips"]:
            strips.append(strip["geometry"]["covers"])
        return strips

    #strips
    def _get_strips_midline(self):
        strips = []
        for strip in self._parsed_data["strips"]:
            line_points = strip["geometry"]["line_points"]
            mid_line = [] # list of pair of points
            for i in range(len(line_points)):
                if i == 0:
                    start_index = i
                    end_index = i + 1
                else:
                    start_index = i-1
                    end_index = i
                start_point = line_points[start_index]["point"]
                end_point =  line_points[end_index]["point"]
                vector = (end_point[0]-start_point[0], end_point[1]-start_point[1])
                vector_length = math.sqrt(vector[0] ** 2 + vector[1] ** 2)
                unit_vector = (vector[0]/vector_length, vector[1]/vector_length)
                clock_wise_unit_vector = (unit_vector[1], -unit_vector[0])
                counterclock_wise_unit_vector = (-unit_vector[1], unit_vector[0])
                point = line_points[i]["point"]
                margin = line_points[i]["margin"]
                mid_line_point = [
                    (point[0] + margin[0] * counterclock_wise_unit_vector[0] + point[0] + margin[1] * clock_wise_unit_vector[0])/2,
                    (point[1] + margin[0] * counterclock_wise_unit_vector[1] + point[1] + margin[1] * clock_wise_unit_vector[1])/2
                ]
                mid_line_width = margin[0] + margin[1]
                mid_line.append(
                    {
                        "point": mid_line_point,
                        "width": mid_line_width
                    }
                )
            strips.append(mid_line)
        return strips

    #strips
    def _get_strips_geometry(self):
        mid_lines = self._get_strips_midline()
        covers = self._get_strips_covers()
        return [
            {
                "mid_line": mid_lines[i],
                "covers": covers[i]
            } for i in range(len(mid_lines))
        ]

    #strips
    def _get_strips_typical_mesh(self):
        strips = []
        for strip_typical in self._typical_subpieces:
            strips.append(
                {
                    "top": [
                        {
                            "diameter": subpiece.rebar.get_diameter_mm(),
                            "number": strip_typical["top"]["number"],
                            "stations": [subpiece.executive.start, subpiece.executive.end],
                            "bends": [subpiece.bend.start, subpiece.bend.end],
                        }
                        for subpiece in strip_typical["top"]["subpieces"]
                    ],
                    "bottom": [
                        {
                            "diameter": subpiece.rebar.get_diameter_mm(),
                            "number": strip_typical["bottom"]["number"],
                            "stations": [subpiece.executive.start, subpiece.executive.end],
                            "bends": [subpiece.bend.start, subpiece.bend.end],
                        }
                        for subpiece in strip_typical["bottom"]["subpieces"]
                    ],
                }
            )
        return strips

    #strips
    def _get_strips_additional_mesh(self):
        strips = []
        for strip_drawing_data in self._foundation.get_drawing_data():
            strips.append(
                {
                    "top":[

                        [
                            [
                                {
                                    "number": bunch.get_count(),
                                    "diameter": bunch.get_pieces()[0].rebar.get_diameter_mm(),
                                    "stations": [subpiece.executive.start, subpiece.executive.end],
                                    "bends": [subpiece.bend.start, subpiece.bend.end],
                                } for subpiece in bunch.get_pieces()[0].get_subpieces()
                            ] for bunch in row
                        ] for row in strip_drawing_data["top"]
                    ],
                    "bottom": [
                        [
                            [
                                {
                                    "number": bunch.get_count(),
                                    "diameter": bunch.get_pieces()[0].rebar.get_diameter_mm(),
                                    "stations": [subpiece.executive.start, subpiece.executive.end],
                                    "bends": [subpiece.bend.start, subpiece.bend.end],
                                } for subpiece in bunch.get_pieces()[0].get_subpieces()
                            ] for bunch in row
                        ] for row in strip_drawing_data["bottom"]
                    ],
                }
            )
        return strips

    #strips
    def _get_strips_mesh(self):
        strips = []
        strips_typical = self._get_strips_typical_mesh()
        strips_additional = self._get_strips_additional_mesh()
        return [
            {
                "typical": strips_typical[i],
                "additional": strips_additional[i],
            }
            for i in range(len(strips_additional))
        ]

    #strips
    def _get_strips_shear_zones(self):
        strips = []
        for strip_shear_zones in self._foundation.get_strip_shear_zones():
            strips.append(
                [
                    {
                        "period": (shear_zone.period.start, shear_zone.period.end),
                        "id": shear_zone.shear_type.id
                    } for shear_zone in strip_shear_zones
                ]
            )
        return strips

    #strips
    def _get_strips_moment(self) -> List[Dict]:
        strips_resistance_moment = self._foundation.get_strips_resistance_moment()
        strips_ultimate_moment = self._foundation.get_strips_ultimate_moment()
        # for strip in self._parsed_data["strips"]:
        #     strips_ultimate_moment.append({
        #         "top": {
        #             "stations": strip["stations"],
        #             "values": strip["design"]["moment"]["top"]
        #         },
        #         "bottom": {
        #             "stations": strip["stations"],
        #             "values": strip["design"]["moment"]["bottom"]
        #         }
        #     })
        return [
            {
                "resistance": strips_resistance_moment[i],
                "ultimate": strips_ultimate_moment[i]
            } for i in range(len(strips_resistance_moment))
        ]

    #strips
    def _get_strips(self):
        strips = []
        names = self._get_strips_name()
        geometries = self._get_strips_geometry()
        meshes = self._get_strips_mesh()
        strips_shear_zones = self._get_strips_shear_zones()
        moments = self._get_strips_moment()
        return [
            {
                "name": names[i],
                "geometry": geometries[i],
                "mesh": meshes[i],
                "shear_zones": strips_shear_zones[i],
                "moment": moments[i]
            } for i in range(len(names))
        ]

    def _get_grid(self) -> Dict[str, List[float]]:
        return self._parsed_data["grid"]

    def get_output(self):
        output = {}
        if self._foundation.errors == {}:
            output['data'] = {
                "version": 1,
                "language": "En",
                "areas": self._get_areas(),
                "columns": self._get_columns(),
                "technical_spec": self._get_technical_spec(),
                "pieces": self._get_pieces(),
                "summary": self._get_summary(),
                "shear_types": self._get_shear_types(),
                "strips": self._get_strips(),
                "grid": self._get_grid(),
                "cut": []
            }
            if self._foundation.warnings != {}:
                output['warnings'] = self._foundation.warnings
        else:
            output['errors'] = self._foundation.errors

        return output
