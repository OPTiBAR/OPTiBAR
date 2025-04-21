from __future__ import annotations
from functools import lru_cache
from pprint import pprint
from typing import Dict, Union, List, Tuple, Set
import pyodbc
import os
from .errors import TableMissingError, MultipleMaterialError


class V16Parser():
    def __init__(self, file_path: str) -> None:
        if not os.path.isfile(file_path):
            raise IOError("database file is not available")
        # if not file_path.endswith('.accdb'):
        #     raise IOError('file format is not accdb')
        self.conn = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' +
            file_path  + ';')
        self.cursor = self.conn.cursor()
    
    def __del__(self):
        self.cursor.close()
        self.conn.close()
        
    
    @lru_cache
    def _extract_unit_conversion(self) -> Dict[str, float]:
        data_dict = {}
        table_name = '[Program Control]'
        column_names = ','.join(['CurrUnits'])
        try:
            self.cursor.execute('select ' + column_names + ' from '+ table_name)
        except :
            raise TableMissingError(table_name)
        (force_unit_str, length_unit_str, _) =  tuple(map(str.strip, self.cursor.fetchone()[0].split(",")))
        def get_force_coeff(force_unit_str):
            return {
                'lb': 0.000453592,
                'Kip': 0.453592,
                'KN': 0.10197162,
                'Kgf': 0.001,
                'N': 0.00010197162,
                'Tonf': 1,
                'Kgf': 0.001,
            }[force_unit_str]
        def get_length_coeff(length_unit_str):
            return {
                'in': 0.0254,
                'ft': 0.3048,
                'm': 1,
                'cm': 0.01,
                'mm': 0.001,
            }[length_unit_str]
        data_dict['length'] = get_length_coeff(length_unit_str)
        data_dict['force'] = get_force_coeff(force_unit_str)
        return data_dict
    
    def _extract_grid(self) -> Dict[str, List[Dict[str,Union(float,str)]]]:
        """extracts grid lines

        Raises:
            ValueError: Grid Lines Table is not available
            ValueError: Axis direction should be 'X' or 'Y'

        Returns:
            Dict[str, List[Dict[str,Union(float,str)]]]: 
            key: 'X' or 'Y'
            value: list of grid line dicts
                key: 'name' or 'ordinate'
                value: name of ordinate value
        """
        unit_conversion = self._extract_unit_conversion()
        data_dict = {}
        table_name = '[Grid Lines]'
        column_names = ','.join(['AxisDir', 'GridID', 'Ordinate'])
        try:
            self.cursor.execute('select ' + column_names + ' from '+ table_name)
        except :
            raise TableMissingError(table_name)
        data_dict['X'] = []
        data_dict['Y'] = []
        for row_tuple in self.cursor.fetchall():
            axis_dir = row_tuple[0]
            grid_id = str(row_tuple[1])
            ordinate = unit_conversion['length'] * row_tuple[2]
            axis = {"name": grid_id, "ordinate": ordinate}
            if axis_dir == 'X':
                data_dict['X'].append(axis)
            elif axis_dir == 'Y':
                data_dict['Y'].append(axis)
            else:
                raise ValueError("Axis direction should be 'X' or 'Y'")
        return data_dict

    def _extract_flexural_shear_data(self) -> Dict[str, Dict[str, Union(str,List[float])]]:
        """extracts flextural and shear data

        Raises:
            ValueError: Concrete Slab Design 01 - Flexural And Shear Data Table is not available

        Returns:
            Dict[str, Dict[str, float]]:
            key: strip name
            value: a dict
                key: 'name', 'station_list' , 'width', 'As_top_list', 'As_bottom_list', 'moment_top_list', 'moment_bottom_list', 'As_shear_list'
                value: str, List[float]

        """
        unit_conversion = self._extract_unit_conversion()
        data_dict = {}
        table_name = '[Concrete Slab Design 01 - Flexural And Shear Data]'
        column_names = ','.join(['Strip','Station','ConcWidth','FTopArea','FBotArea','FTopMoment','FBotMoment','VArea'])

        try:
            self.cursor.execute('select ' + column_names + ' from '+ table_name)
        except :
            raise TableMissingError(table_name)
        
        for row_tuple in self.cursor.fetchall():
            strip_name = row_tuple[0]
            station = row_tuple[1] * unit_conversion['length']
            width = row_tuple[2] * unit_conversion['length']
            top_area = row_tuple[3] * (unit_conversion['length'] ** 2)
            bottom_area = row_tuple[4] * (unit_conversion['length'] ** 2)
            top_moment = row_tuple[5] * (unit_conversion['length'] * unit_conversion['force'])
            bottom_moment = row_tuple[6] * (unit_conversion['length'] * unit_conversion['force'])
            shear_area = row_tuple[7] * unit_conversion['length']

            # finding a new strip initialize the data field
            if not strip_name in data_dict.keys():
                data_dict[strip_name] = {
                    'name':strip_name,
                    'station_list':[],
                    'As_top_list':[],
                    'As_bottom_list':[],
                    'As_shear_list':[],
                    'moment_top_list':[],
                    'moment_bottom_list':[],
                    'widths':[],
                }
            data_dict[strip_name]['station_list'].append(station)
            data_dict[strip_name]['widths'].append(width)
            data_dict[strip_name]['As_top_list'].append(top_area)
            data_dict[strip_name]['As_bottom_list'].append(bottom_area)
            data_dict[strip_name]['moment_top_list'].append(top_moment)
            data_dict[strip_name]['moment_bottom_list'].append(bottom_moment)
            data_dict[strip_name]['As_shear_list'].append(shear_area)            
        return data_dict
    
    def _extract_strip_geometry(self) -> Dict[str, List[Dict[str, Tuple[float, float]]]]:
        """extracts the geometry of the strip area
        strip may contain more than 2 points.
        and it will return the midline and the width of each point.

        Raises:
            ValueError: Object Geometry - Design Strips Table is not availabe

        Returns:
            Dict: 
                key: strip name
                value: list of dicts
                    key: 'point', 'margin'
                    value: Tuple[float, float]
        """
        unit_conversion = self._extract_unit_conversion()
        data_dict = {}
        table_name = '[Object Geometry - Design Strips]'
        column_names = ','.join(['Strip','GlobalX','GlobalY','WBLeft','WBRight','WALeft','WARight'])
        try:
            self.cursor.execute('select ' + column_names + ' from '+ table_name)
        except Exception:
            raise TableMissingError(table_name)

        for row_tuple in self.cursor.fetchall():
            strip_name = row_tuple[0]
            x = row_tuple[1] * unit_conversion['length']
            y = row_tuple[2] * unit_conversion['length']
            end_left = row_tuple[3] * unit_conversion['length'] if not row_tuple[3] is None else None
            end_right = row_tuple[4] * unit_conversion['length'] if not row_tuple[4] is None else None
            start_left = row_tuple[5] * unit_conversion['length'] if not row_tuple[5] is None else None
            start_right = row_tuple[6] * unit_conversion['length'] if not row_tuple[6] is None else None

            # finding a new strip initialize the data field
            if not strip_name in data_dict.keys():
                data_dict[strip_name] = []
            
            break_point = {}
            break_point['point'] = [x,y]
            data_dict[strip_name].append(break_point)
            if end_left is not None:
                break_point['margin'] = [end_left, end_right]
            elif start_left is not None:
                break_point['margin'] = [start_left, start_right]
            else:
                raise ValueError('one of two ends should have margin')
        return data_dict
    
    def _extract_concrete_material(self) -> Dict[str, float]:
        """returns the dictionary of concrete names and their fc.

        Raises:
            ValueError: if Material Properties 03 - Concrete Table is not available.

        Returns:
            Dict[str, float]: key is the name of the material and value is the fc of the material.
        """
        unit_conversion = self._extract_unit_conversion()
        data_dict = {}
        table_name = '[Material Properties 03 - Concrete]'
        column_names = ','.join(['Material','Fc'])
        try:
            self.cursor.execute('select ' + column_names + ' from '+ table_name)
        except :
            raise TableMissingError(table_name)
        for row_tuple in self.cursor.fetchall():
            material_name = row_tuple[0]
            FC = row_tuple[1] * unit_conversion['force'] / (unit_conversion['length'] ** 2)
            data_dict[material_name] = FC
        return data_dict

    def _extract_rebar_material(self) -> Dict[str, float]:
        """returns the dictionary of steel names and their fy.

        Raises:
            ValueError: if Material Properties 04 - Rebar Table is not available.

        Returns:
            Dict[str, float]: key is the name of material and value is the fy of the material.
        """
        unit_conversion = self._extract_unit_conversion()
        data_dict = {}
        table_name = '[Material Properties 04 - Rebar]'
        column_names = ','.join(['Material','Fy'])
        try:
            self.cursor.execute('select ' + column_names + ' from '+ table_name)
        except :
            raise TableMissingError(table_name)
        for row_tuple in self.cursor.fetchall():
            material_name = row_tuple[0]
            FY = row_tuple[1] * unit_conversion['force'] / (unit_conversion['length'] ** 2)
            data_dict[material_name] = FY
        return data_dict

    def _extract_strip_prop(self):
        """returns the dictionary of strip names and rebar material name.

        Raises:
            ValueError: if Slab Design Overwrites 01 - Strip Based Table is not available

        """
        unit_conversion = self._extract_unit_conversion()
        data_dict = {}
        table_name = '[Slab Design Overwrites 01 - Strip Based]'
        # column_names = ','.join(['Strip','RebarMat'])
        try:
            self.cursor.execute('select  * from '+ table_name)
        except :
            raise TableMissingError(table_name)
        for row_tuple in self.cursor.fetchall():
            strip_name = row_tuple[0]
            rebar_name = row_tuple[6]
            data_dict[strip_name] = {'rebar':rebar_name}
            if row_tuple[7] == 'Preferences':
                data_dict[strip_name]['covers'] = None
            else:
                data_dict[strip_name]['covers'] = {
                    'top': row_tuple[8] * unit_conversion['length'],
                    'bottom': row_tuple[8] * unit_conversion['length'],
                }
        return data_dict
    
    def _extract_cover_preferences(self):
        unit_conversion = self._extract_unit_conversion()
        data_dict = {}
        table_name = '[Design Preferences 02 - Rebar Cover - Slabs]'
        column_names = ','.join(['CoverTop','CoverBot'])
        try:
            self.cursor.execute('select ' + column_names + ' from '+ table_name)
        except :
            raise TableMissingError(table_name)
        row_tuple = self.cursor.fetchone()
        data_dict['top'] = row_tuple[0] * unit_conversion['length']
        data_dict['bottom'] = row_tuple[1] * unit_conversion['length']
        return data_dict

    def _get_strip_prop(self):
        rebar_dict = self._extract_rebar_material()
        prop_dict = self._extract_strip_prop()
        cover_dict = self._extract_cover_preferences()
        data_dict = {}
        for strip in prop_dict:
            data_dict[strip] = {}
            if prop_dict[strip]['covers'] is None:
                data_dict[strip]['covers'] = cover_dict.copy()
            else:
                data_dict[strip]['covers'] =  prop_dict[strip]['covers']
            data_dict[strip]['fy'] = rebar_dict[prop_dict[strip]['rebar']]
        return data_dict

    def _extract_slab_properties(self) -> Dict[str, Dict[str, Union(float, str)]]:
        """extracts the properties of each slab. the properties are
        thickness and material proprty.

        Raises:
            ValueError: if Slab Properties 02 Table is not available.

        Returns:
            Dict[str, Dict[str, Union(float, str)]]: the key is the name of the slab
            and the the value is a dict containing two properties and their corresponding values. 
        """
        unit_conversion = self._extract_unit_conversion()
        data_dict = {}
        table_name = '[Slab Properties 02 - Solid Slabs]'
        column_names = ','.join(['Slab','Thickness','MatProp'])
        try:
            self.cursor.execute('select ' + column_names + ' from '+ table_name)
        except :
            raise TableMissingError(table_name)
        
        for row_tuple in self.cursor.fetchall():
            slab_name = row_tuple[0]
            thickness = row_tuple[1] * unit_conversion['length']
            concrete_material = row_tuple[2]
            data_dict[slab_name] = {'thickness':thickness, 'concrete_material':concrete_material}
        return data_dict
    
    def _extract_slab_prop_assignment(self) -> Dict[str, str]:
        """assigns properties of each area based on the slab name.

        Raises:
            ValueError: if Slab Property Assignments Table is not available.
        
        Returns:
            Dict[int, str]: the key is the index of the area and the value is the corresponding slab's name.
        """
        data_dict = {}
        table_name = '[Slab Property Assignments]'
        column_names = ','.join(['Area','SlabProp'])
        try:
            self.cursor.execute('select ' + column_names + ' from '+ table_name)
        except Exception:
            raise TableMissingError(table_name)

        for row_tuple in self.cursor.fetchall():
            area_index = row_tuple[0]
            slab_name = row_tuple[1]
            # if slab name is not available line None ! insert the thickest value
            if slab_name == 'None':
                data_dict[area_index] = None
            else:
                data_dict[area_index] = slab_name
        return data_dict
    
    def _extract_point_coordinates(self) -> Dict[int, List[float]]:
        """extracts the coordinate of the points based on their ID.

        Raises:
            ValueError: if Object Geometry - Point Coordinates Table is not available.

        Returns:
            Dict[str, Dict[str, float]]: the key is the index of the point and the value is a dict with two keys ,x and y.
        """
        unit_conversion = self._extract_unit_conversion()
        data_dict = {}
        table_name = '[Object Geometry - Point Coordinates]'
        column_names = ','.join(['Point','GlobalX','GlobalY'])
        try:
            self.cursor.execute('select ' + column_names + ' from '+ table_name)
        except Exception:
            raise TableMissingError(table_name)
        
        for row_tuple in self.cursor.fetchall():
            point_index = row_tuple[0]
            x = row_tuple[1] * unit_conversion['length']
            y = row_tuple[2] * unit_conversion['length']
            data_dict[point_index] = [x,y]
        
        return data_dict
    
    def _extract_point_load_geometry(self) -> Dict[int, List[float]]:
        """extract the geometry of the columns

        Raises:
            ValueError: if Load Assignments - Point Loads Table is not available.

        Returns:
            Dict[int, Dict[str,float]]: the key is the index of the point and the value is a dict with two keys xdim and ydim.
        """
        unit_conversion = self._extract_unit_conversion()
        data_dict = {}
        table_name = '[Load Assignments - Point Loads]'
        column_names = ','.join(['Point','XDim','YDim'])
        try:
            self.cursor.execute('select ' + column_names + ' from '+ table_name)
        except Exception:
            raise TableMissingError(table_name)
        for row_tuple in self.cursor.fetchall():
            point = row_tuple[0]
            xdim = row_tuple[1] * unit_conversion['length']
            ydim = row_tuple[2] * unit_conversion['length']
            if xdim > 0.05 and ydim > 0.05:
                data_dict[point] = [xdim, ydim]
        return data_dict

    def _extract_area_geometry(self) -> Dict[int, List[int]]:
        """extract the areas

        Raises:
            ValueError: Object Geometry - Areas 01 Table is not available

        Returns:
            Dict[int, List[int]]: the key is the index of the area and the value is a list of point index.
        """
        data_dict = {}
        table_name = '[Object Geometry - Areas 01 - General]'
        # AreaType is added for Slab
        column_names = ','.join(['Area','NumPoints','Point1','Point2','Point3','Point4','AreaType'])
        try:
            self.cursor.execute('select ' + column_names + ' from '+ table_name)
        except Exception:
            raise TableMissingError(table_name)
        
        for row_tuple in self.cursor.fetchall():
            # added for slabs
            if row_tuple[6] == 'Wall':
                continue
            area = row_tuple[0]
            num_points = row_tuple[1]
            row_point_list = row_tuple[2:-1]
            if area not in data_dict.keys():
                data_dict[area] = []
            for point in row_point_list:
                if point is not None:
                    data_dict[area].append(point)
        return data_dict

    def _get_columns(self) -> List[Dict[str,Tuple[float, float]]]:
        """getting column point and dimension

        Returns:
            List[Dict[str,Tuple[float, float]]]:
                key: 'point' or 'dim'
                value: Tuple(float,float)
        """
        data_list = []
        load_dict = self._extract_point_load_geometry()
        point_dict = self._extract_point_coordinates()
        for point in load_dict:
            data_list.append({
                "point": point_dict[point],
                "dim": load_dict[point]
            })
        return data_list

    def _get_grid(self) -> Dict[str, List[Dict[str,Union(float,str)]]]:
        """get grid dict
        """
        grid_dict = self._extract_grid()
        return grid_dict
    
    def _get_area_geometry(self):
        point_dict = self._extract_point_coordinates()
        area_dict = self._extract_area_geometry()
        output = {}
        for area in area_dict:
            point_list = []
            point_index_list = area_dict[area]
            for point_index in point_index_list:
                point_list.append(point_dict[point_index])
            output[area] = point_list
        return output
    
    def _get_slab_prop(self):
        """
        return a dictionary of slab properties
        key: slab_name
        value: dict of properties
        """
        concrete_dict = self._extract_concrete_material()
        slab_dict = self._extract_slab_properties()
        output = {}
        for slab in slab_dict:
            output[slab] = {
                'thickness': slab_dict[slab]['thickness'],
                'fc': concrete_dict[slab_dict[slab]['concrete_material']]
            }
        return output

    def _get_area_prop(self):
        """
        returns a dictionary of area properties
        key: area_name
        value: dict of properties
        """
        area_dict = self._extract_slab_prop_assignment()
        slab_prop_dict = self._get_slab_prop()
        output = {}
        for area in area_dict:
            if area_dict[area] is None:
                output[area] = None
            else:
                output[area] = slab_prop_dict[area_dict[area]]
        return output
    
    def _get_areas(self):
        geometry_dict = self._get_area_geometry()
        prop_dict = self._get_area_prop()
        data_list = []
        for area in geometry_dict:
            area_dict = {"name": area}
            area_dict['corners'] = geometry_dict[area]
            if prop_dict[area] is not None:
                area_dict["prop"] = prop_dict[area]
                area_dict['is_opening'] = False
            else:
                area_dict['is_opening'] = True
            data_list.append(area_dict)
        return data_list

    @lru_cache
    def _get_strips(self):
        flexural_dict = self._extract_flexural_shear_data()
        geometry_dict = self._extract_strip_geometry()
        prop_dict = self._get_strip_prop()
        data_list = []
        for strip in geometry_dict:
            strip_dict = {"name": strip}
            strip_dict["stations"] = flexural_dict[strip]['station_list']
            strip_dict["design"] = {}
            strip_dict["design"]["shear"] = flexural_dict[strip]['As_shear_list']
            strip_dict["design"]["flexural"] = {}
            strip_dict["design"]["flexural"]["top"] = flexural_dict[strip]['As_top_list']
            strip_dict["design"]["flexural"]["bottom"] = flexural_dict[strip]['As_bottom_list']
            strip_dict["design"]["moment"] = {}
            strip_dict["design"]["moment"]["top"] = flexural_dict[strip]['moment_top_list']
            strip_dict["design"]["moment"]["bottom"] = flexural_dict[strip]['moment_bottom_list']
            strip_dict["geometry"] = {}
            strip_dict["geometry"]["widths"] = flexural_dict[strip]['widths']
            strip_dict["geometry"]["line_points"] = geometry_dict[strip]
            strip_dict["geometry"]["covers"] = prop_dict[strip]['covers']
            strip_dict["fy"] = prop_dict[strip]['fy']
            data_list.append(strip_dict)
        return data_list
            
    def _get_foundation(self) -> Dict:
        strips = self._get_strips()
        areas = self._get_areas()
        columns = self._get_columns()
        grid = self._get_grid()
        
        output =  {
            "version": 1,
            "strips": strips,
            "areas": areas,
            "columns": columns,
            "grid": grid
        }
        return output
    
    def get_foundation(self) -> Dict:
        output = self._foundation = self._get_foundation()
        return output

    def get_steel_volume(self) -> float:
        """total flexural steel volumn in cubic meter

        Returns:
            float: volume of flexural steel in cubic meter
        """
        strips = self._get_strips()
        total = 0
        for strip in strips:
            stations = strip['stations']
            top_areas = strip["design"]["flexural"]["top"]
            bottom_areas = strip["design"]["flexural"]["bottom"]
            for i in range(len(stations)-1):
                distance = stations[i+1]-stations[i]
                top_area = (top_areas[i+1] + top_areas[i])/2
                bottom_area = (bottom_areas[i+1] + bottom_areas[i])/2
                total += (top_area + bottom_area) * distance
        return total



    def get_steel_set(self) -> Set[float]:
        """returns used fy"""
        return set([strip["fy"] for strip in self._foundation["strips"]])

    def get_concrete_set(self) -> bool:
        """does it use multiple concrete material

        Returns:
            bool: true of uses multiple concrete material
        """
        fc = []
        for area in self._foundation["areas"]:
            if not area['is_opening']:
                fc.append(area["prop"]["fc"])
        return set(fc)

    def get_cover_set(self) -> Dict[str, Set[float]]:
        """does it use multiple covers for different strips

        Returns:
            bool: true of uses multiple covers
        """
        top = []
        bottom = []
        for strip in self._foundation["strips"]:
            top.append(strip["geometry"]["covers"]["top"])
            bottom.append(strip["geometry"]["covers"]["bottom"])
        return {
            'top': set(top),
            'bottom': set(bottom),
        }

