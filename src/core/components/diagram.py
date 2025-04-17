from __future__ import annotations
from .period import Period
from typing import List, Dict
from copy import copy

class Diagram():
    def __init__(self, stations: List[float], areas: List[float]):
        """Initializes Diagram.

        Args:
            stations (List[float]): list of stations
            areas (List[float]): list of areas
        """
        
        if len(stations) != len(areas):
            raise ValueError("stations and areas should have the same length.")
        self._points = []
        for i in range(len(stations)):
            self._points.append(Point(stations[i], areas[i]))
        self._original_points = [copy(point) for point in self._points]
    
    def insert_typical(self, amount: float) -> None:
        """inserts typical rebars, with the given area

        Args:
            amount (float): area of the all inserted rebars
        """
        self._insert(amount)
        
    def insert_additional(self, area: float) -> List[Period]:
        """inserts one row of additional rebar with the given area

        Args:
            area (float): area of the additional rebar

        Returns:
            List[Period]: theoretical periods of the pieces
        """
        periods = self.get_periods()
        self._insert(area)
        return periods

    def get_side_distance(self) -> float:
        """max distance of the first zero station from each side
        it is assumed that there is no zero between two other zero stations.
        consecutive zeros are removed.

        Returns:
            float: distance
        """
        start_dist = 0
        end_dist = 0
        if self._points[0].area == 0 and self._points[1].area == 0:
            start_dist = self._points[1].station - self._points[0].station
        if self._points[-1].area == 0 and self._points[-2].area == 0:
            end_dist = self._points[-1].station - self._points[-2].station
        return max(start_dist, end_dist)
        
    def get_middle_distance(self) -> float:
        """distance of two zero stations not in the start or end of the diagram

        Returns:
            float: distance
        """
        max_dist = float("-inf")
        # first point and last two points are not considered
        for i in range(1,len(self._points)-2):
            if self._points[i].area == self._points[i+1].area == 0:
                dist = self._points[i+1].station - self._points[i].station
                max_dist = max(max_dist, dist)
        if max_dist < float("inf"):
            return max_dist
        else:
            return 0
    
    def get_stations(self) -> List[float]:
        return [point.station for point in self._points]

    def get_values(self) -> List[float]:
        return [point.area for point in self._points]
        
    def _insert(self, amount: float) -> None:
        """inserts given amount of steel

        Args:
            amount (float): amount of steel area
        """
        self._reduce(amount)
        self._add_intersection_points()
        self._increase_nagative_points()
        self._remove_consecutive_zeros()

    def _reduce(self, amount:float) -> None:
        """reduce the area of all points by the given amount

        Args:
            amount (float): amount of reduction
        """
        for point in self._points:
            point.area -= amount
    
    @staticmethod
    def _interpolate_zero_line(point1: Point, point2: Point)-> Point:
        """
        finds the intersection point of the connecting line between point1 and point2
        and the y=0 line.
        it is assumed that (point1.value * point2.value < 0) and 
        (point1.station < poin2.station).

        Args:
            point1 (Point): first point of the line
            point2 (Point): second point of the line

        Returns:
            Point: the interpolation point
        """
        x1 = point1.station
        x2 = point2.station
        y1 = abs(point1.area)
        y2 = abs(point2.area)
        d = (y1*(x2-x1))/(y2+y1)
        return Point(station=(d + x1), area=0)
    
    @staticmethod
    def _interpolate(point_1: Point, point_2: Point, station: float) -> float:
        """returns area of the given station between two points

        Args:
            point_1 (Point): first point
            point_2 (Point): second point
            statation ([float]): satation that its area is required 

        Returns:
            float: area of the point in the given station
        """
        y1 = point_1.area
        y2 = point_2.area
        x1 = point_1.station
        x2 = point_2.station
        return y1 + ((station-x1)/(x2-x1)) * (y2-y1)

    def _add_intersection_points(self) -> None:
        """adds intersection point of diagram and zero line to the list of points
        """
        points = self._points # local reference for clarity
        i = 0 # counter on the list
        while (i < len(points)-1):
            if (points[i].area * points[i+1].area) < 0:
                # the interpolation point should be added
                inter_point = Diagram._interpolate_zero_line(points[i], points[i+1])
                points.insert(i+1, inter_point)
                i += 2 # skip the newly added point
            else:
                i += 1
    
    def _remove_consecutive_zeros(self) -> None:
        """remove the consecutive zero points
        if there is a zero point between two other zeros it should be removed
        """        
        points = self._points
        i = 1 # start from the second point
        while(i < len(points)-1):
            if (points[i-1].area == 0 and points[i].area == 0 and points[i+1].area == 0):
                del points[i]
            else:
                i += 1

    def _increase_nagative_points(self) -> None:
        """increase negative stations to zero
        """
        for point in self._points:
            if point.area < 0:
                point.area = 0

    def get_periods(self) -> List[Period]:
        """finds the intervals that the diagram is strictly above zero line.
        
        Returns:
            List[Period]: returns the list of periods for pieces
        """
        points = self._points # local reference for clarity
        periods = [] # list of periods to be returned
        is_drawing = False
        start = None
        end = None
        for i in range(len(points)): # except the last point
            if not is_drawing:
                if (i==0 and points[i].area>0) or (i<(len(points)-1) and points[i+1].area>0):
                    is_drawing = True
                    start = points[i].station
            else: # is_drawing = True
                if (i == len(points)-1 or (points[i].area == 0 and points[i+1].area == 0)):
                    is_drawing = False
                    end = points[i].station
                    periods.append(Period(start=start, end=end))
        return periods

    def get_bounds(self) -> Period:
        """returns the first and last staion of the strip as a Period

        Returns:
            Period: the first and last station of the strip
        """
        return Period(start=self._points[0].station, end=self._points[-1].station)

    def is_positive(self) -> bool:
        """determines if there is any positve point in the diagram

        Returns:
            bool: True if there is any positive point, False otherwise.
        """
        for point in self._points:
            if point.area > 0 :
                return True
        return False
    
    def get_max_point(self, period: Period) -> Point:
        """returns the point with the maximum area in the given period
        the original diagram is considered.

        Args:
            period (Period): period to be searched for the maximum area

        Returns:
            float: station of the max area
        """
        max_station = None
        max_area = float("-inf")
        for i,point in enumerate(self._original_points):
            if (period.start <= point.station <= period.end) and (point.area > max_area):
                max_area = point.area
                max_station = point.station
            if i<len(self._original_points)-1:
                for station in (period.start, period.end):
                    if self._original_points[i].station < station < self._original_points[i+1].station:
                        area = Diagram._interpolate(self._original_points[i], self._original_points[i+1], station)
                        if area > max_area:
                            max_area = area
                            max_station = station
        return Point(max_station, max_area)
    
    def get_min_point(self, period:Period) -> Point:
        min_station = None
        min_area = float("inf")
        for i,point in enumerate(self._original_points):
            if (period.start <= point.station <= period.end) and (point.area < min_area):
                min_area = point.area
                min_station = point.station
            if i<len(self._original_points)-1:
                for station in (period.start, period.end):
                    if self._original_points[i].station < station < self._original_points[i+1].station:
                        area = Diagram._interpolate(self._original_points[i], self._original_points[i+1], station)
                        if area < min_area:
                            min_area = area
                            min_station = station
        return Point(min_station, min_area)

    def increase_area(self, bends: Dict[str, bool], stations: List[float], value: float) -> None:
        """increases diagram by a trapasoid
        each bended side is increased sharply by the value.
        if both sides are not bended, there are 4 stations.
        if one side is bended there are two points.
        if both sides are bended, stations list is empty. 
        Args:
            bends (Tuple[bool, bool]): a two member tuple indicating the bend status of each end 
            stations (List[float]): stations of the break points of the trapasoid
            value (float): the height of the trapasoid
        """
        
        # adding points
        points = self._points # local reference for clarity
        for station in stations:
            i = 0 # counter on the list
            while (i < len(points)-1):
                if points[i].station < station < points[i+1].station:
                    area = Diagram._interpolate(points[i], points[i+1], station)
                    points.insert(i+1, Point(station, area))
                    break
                else:
                    i += 1
        
        # add constant line value
        # start bend
        if bends["start"] and not bends["end"]:
            i = 0 # counter on the list
            while (i < len(points)):
                if points[i].station <= stations[0]:
                    points[i].area += value
                i += 1
        # end bend
        elif not bends["start"] and bends["end"]:
            i = 0 # counter on the list
            while (i < len(points)):
                if points[i].station >= stations[1]:
                    points[i].area += value
                i += 1
        # both side bend
        elif bends["start"] and bends["end"]:
            i = 0 # counter on the list
            while (i < len(points)):
                points[i].area += value
                i += 1
        # no side bend
        else: # bends["start"]==False and bends["end"]==False
            i = 0 # counter on the list
            while (i < len(points)):
                if stations[1] <= points[i].station <= stations[2]:
                    points[i].area += value
                i += 1
        
        # add sloped line value
        # decreasing slope
        if (bends["start"] and not bends["end"]) or (not bends["start"] and not bends["end"]):
            i = 0 # counter on the list
            while (i < len(points)):
                if stations[-2] < points[i].station < stations[-1]:
                    added_area = value * (stations[-1] - points[i].station)/(stations[-1] - stations[-2])
                    points[i].area += added_area 
                i += 1
        # increasing slope
        if (not bends["start"] and bends["end"]) or (not bends["start"] and not bends["end"]):
            i = 0 # counter on the list
            while (i < len(points)):
                if stations[0] < points[i].station < stations[1]:
                    added_area = value * (points[i].station - stations[0])/(stations[1] - stations[0])
                    points[i].area += added_area 
                i += 1

    def trim_period(self, period: Period) -> None:
        """trim the period section of the diagram and reduces it to zero

        Args:
            period: the period that should be trimed and it should be subset of the diagram bounds
            offset: 
        """
        assert period.is_subset_of(self.get_bounds())
        # add remove stations to the diagram

        stations = (
            period.start,
            period.start + period.get_length()/100,
            period.end - period.get_length()/100,
            period.end
        )
            
        points = self._points
        
        # add points
        for station in stations:
            i = 0
            while i < len(points):
                if points[i].station == station:
                    if station in stations[1:3]:
                        points[i].value = 0
                    break
                elif i < len(points)-1 and points[i].station < station < points[i+1].station:
                    if station in stations[1:3]:
                        area = 0
                    else: # station in (stations[0], stations[3])
                        area = Diagram._interpolate(points[i], points[i+1], station)
                    points.insert(i+1, Point(station, area))
                    break
                i += 1
        
        # delete excess points
        i = 0
        while i < len(points):
            conditions = (
                stations[0] < points[i].station < stations[1],
                stations[1] < points[i].station < stations[2],
                stations[2] < points[i].station < stations[3]
            )
            if any(conditions):
                del points[i]
            else:
                i += 1
        
    def linearize_period(self, period: Period) -> None:
        """linearizes the diagram between two points (practicaly column sides)
        Args:
            period: the period that should be linearized and it should be subset of the diagram bounds.
        """
        if period.start < self.get_bounds().start:
            period.start = self.get_bounds().start
        if period.end > self.get_bounds().end:
            period.end = self.get_bounds().end
        # add the station points
        points = self._points
        for station in (period.start, period.end):
            i = 0
            while i < len(points)-1:
                if points[i].station < station < points[i+1].station:
                    area = Diagram._interpolate(points[i], points[i+1], station)
                    points.insert(i+1, Point(station, area))
                    break
                i += 1

        # delete middle points
        i = 0
        while i < len(points):
            if period.start < points[i].station < period.end:
                del points[i]
            else:
                i += 1
    
    def minimize_period(self, period: Period, side:str) -> None:
        """reduces value of the point in the given period to the minimum of the point's value and
        the interpolated value of the given side of the period

        Args:
            period (Period): period
            side (str): side of the period to be the base for maximum possible value in the period
        """
        station = getattr(period,side)
        points = self._points
        for i in range(len(points)):
            if points[i].station == station:
                max_area = self._points[i].area
                break
            elif points[i].station < station < points[i+1].station:
                max_area = Diagram._interpolate(points[i], points[i+1], station)
                break
        for point in points:
            if period.start <= point.station <= period.end:
                point.value = min(point.area, max_area) 
        # area = Diagram._interpolate(points[i], points[i+1], station)
    
    def __str__(self):
        return "\n".join([str(point) for point in self._points])

class Point():
    """Defines a point in the steel area diagram
    """
    def __init__(self, station, area):
        self.station = station
        self.area = area
    def __eq__(self, other: Point):
        return self.station == other.station and self.area == other.area
    def __copy__(self):
        return Point(self.station, self.area)
    def __str__(self):
        return f"station: {self.station}, area: {self.area}"