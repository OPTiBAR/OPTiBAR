from shapely.geometry import Polygon, LineString, Point
from typing import Any
import math
from core.setting import MIN_COLUMN_DIM
from copy import deepcopy

class InputInterpreter():
    """converts input data from parsing accdb file to usaable data for feeding foundation class
    """
    def __init__(self, parsed_data: Dict) -> None:
        self.parsed_data = parsed_data
        self._area_polygons = self._get_area_polygons()
        self._strip_polygons = self._get_strip_polygons()
        self._strip_props = self._get_strip_props()
        self._strip_line_strings = self._get_strip_line_strings()

    def _get_strip_polygons(self) -> list[Polygon]:
        def get_corners(line_points):
            pair_points = [] # list of pair of points
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
                pair_points.append((
                    (point[0] + margin[0] * counterclock_wise_unit_vector[0], point[1] + margin[0] * counterclock_wise_unit_vector[1]),
                    (point[0] + margin[1] * clock_wise_unit_vector[0], point[1] + margin[1] * clock_wise_unit_vector[1])
                ))
            corners = []
            for pair in pair_points:
                corners.append(pair[0])
            for pair in reversed(pair_points):
                corners.append(pair[1])
            return corners

        polygons = []
        for strip in self.parsed_data["strips"]:
            line_points = strip["geometry"]["line_points"]
            corners = get_corners(line_points)
            polygons.append(Polygon(corners))
        return polygons

    def _get_area_polygons(self) -> list[Polygon]:
        polygons = []
        for area in self.parsed_data["areas"]:
            polygons.append(Polygon(area["corners"]))
        return polygons

    def _get_strip_props(self): #list[dict]
        props = []
        for i,strip_polygon in enumerate(self._strip_polygons):
            fy = self.parsed_data["strips"][i]["fy"]
            max_intersection_area = float("-inf")
            max_area_index = None
            for j,area_polygon in enumerate(self._area_polygons):
                if self.parsed_data["areas"][j]["is_opening"]:
                    continue
                intersection_area = area_polygon.intersection(strip_polygon).area
                if intersection_area > max_intersection_area:
                    max_intersection_area = intersection_area
                    max_area_index = j
            fc = self.parsed_data["areas"][max_area_index]["prop"]["fc"]
            thickness = self.parsed_data["areas"][max_area_index]["prop"]["thickness"]
            props.append({
                "fy": fy,
                "fc": fc,
                "thickness": thickness
            })
        return props

    def _get_strip_line_strings(self):
        line_strings = []
        for strip in self.parsed_data["strips"]:
            points = [point["point"] for point in strip["geometry"]["line_points"]]
            line_strings.append(LineString(points))
        return line_strings

    def _get_strip_column_sides(self):
        """returns a list each item belongs to one strip
        each item is a list containing column side pair stations
        """
        column_corners = []
        column_centers = []
        for column in self.parsed_data["columns"]:
            center = column["point"]
            dim = column["dim"]
            if dim[0] < MIN_COLUMN_DIM or dim[1] < MIN_COLUMN_DIM:
                continue
            corners = [
                Point(center[0] - dim[0]/2, center[1] - dim[1]/2),
                Point(center[0] - dim[0]/2, center[1] + dim[1]/2),
                Point(center[0] + dim[0]/2, center[1] + dim[1]/2),
                Point(center[0] + dim[0]/2, center[1] - dim[1]/2),
            ]
            column_centers.append(Point(center))
            column_corners.append(corners)
        strip_column_sides = []
        for i,strip_polygon in enumerate(self._strip_polygons):
            column_sides = [] # contains column side stations of the strip
            for j,center in enumerate(column_centers):
                if center.within(strip_polygon):
                    projections = [self._strip_line_strings[i].project(point) for point in column_corners[j]]
                    column_sides.append((min(projections), max(projections)))
            strip_column_sides.append(column_sides)
        return strip_column_sides

    def _get_strip_trim_sides(self):
        strip_trim_sides = []
        for i,line_string in enumerate(self._strip_line_strings):
            trim_sides = []
            for j,polygon in enumerate(self._strip_polygons):
                if i == j:
                    continue
                inter = line_string.intersection(polygon)
                if isinstance(inter,LineString) and not inter.is_empty:
                    station1 = line_string.project(Point(inter.coords[0]))
                    station2 = line_string.project(Point(inter.coords[1]))
                    trim_sides.append((station1,station2) if station1 < station2 else (station2,station1))
            strip_trim_sides.append(trim_sides)
        return strip_trim_sides

    def get_strips(self):
        strips = deepcopy(self.parsed_data["strips"])
        strip_column_sides = self._get_strip_column_sides()
        strip_trim_sides = self._get_strip_trim_sides()
        for i,strip in enumerate(strips):
            del strip["fy"]
            strip["prop"] = self._strip_props[i]
            strip["column_sides"] = strip_column_sides[i]
            strip["strip_sides"] = strip_trim_sides[i]
        return strips

    def get_min_thickness(self):
        return min(prop["thickness"] for prop in self._strip_props)
