from sys import flags, intern
from core.src.components.shear import ShearZone, ShearType
from core.src.components.rebar import Rebar
from typing import List
import math
from core.setting import MIN_SHEAR_INTERVAL

class ShearOptimization():
    def __init__(self, rebar: Rebar, max_interval: float, shear_zones: List[ShearZone], number_of_types: int) -> None:
        """finds the best shear types and assigns them to the shear zones

        Args:
            rebar (Rebar): shear rebar
            max_interval (float): maximum distance between two shear rebar
            shear_zones (List[ShearZone]): list of all shear zones
            number_of_types (int): the number of types that zones should be assigned to
        """
        self._shear_zones = sorted(shear_zones, key=lambda shear_zone: shear_zone.steel_density)
        self._steel_densities = sorted(list(set([shear_zone.steel_density for shear_zone in self._shear_zones])))
        self._max_interval = max_interval
        self._rebar = rebar
        self._container = None
        self._number_of_types = number_of_types
    
    def run(self):
        """finds best shear types and assigne them to the shear zones
        """
        self._run(self._number_of_types)
        selected_densities = self._get_selected_densities(self._number_of_types)
        shear_types = self._get_shear_types(selected_densities)
        self._shear_types = shear_types
        self._set_shear_types(shear_types)
    
    class Pair():
        def __init__(self) -> None:
            self.ref = None
            self.value = None
        def __eq__(self, other: object) -> bool:
            return all((
                self.value == other.value,
                self.ref == other.ref
            ))
        def __str__(self):
            return (f"Pair: [value: {self.value}, ref: {self.ref}]")
    
    def _run(self, number_of_types: int) -> None:
        """filles the container of dynamic programming that will be used for finding the optimum point.

        Args:
            number_of_types (int): number of types that is allowed for shear
        """
        steel_densities = self._steel_densities
        # initialize container
        container = []
        self._container = container
        for i in range(number_of_types):
            row = []
            container.append(row)
            for j in range(len(steel_densities)):
                if j < i:
                    row.append(None)
                else:
                    row.append(self.Pair())
        
        # calculate container cells
        for i in range(number_of_types):
            if i == 0:
                for j in range(i, len(steel_densities)):
                    sum = 0
                    for shear_zone in self._shear_zones:
                        if shear_zone.steel_density <= steel_densities[j]:
                            sum += steel_densities[j] * shear_zone.period.get_length()
                        else:
                            break
                    container[i][j].value = sum
            else:
                for j in range(i, len(steel_densities)):
                    min_sum = float("inf")
                    min_ref = None
                    for k in range(i-1, j):
                        sum = container[i-1][k].value
                        for shear_zone in self._shear_zones:
                            if steel_densities[k] < shear_zone.steel_density <= steel_densities[j]:
                                sum += steel_densities[j] * shear_zone.period.get_length()
                        if sum < min_sum:
                            min_ref = k
                            min_sum = sum
                    container[i][j].value = min_sum
                    container[i][j].ref = min_ref
        
    def _get_selected_densities(self, number_of_types: int) -> List[float]:
        """finds the best chosen points from the available densities.

        Args:
            number_of_types (int): the number of types that zones should be assigned to

        Returns:
            List[float]: returns the chosen densities.
        """
        container = self._container
        steel_densities = self._steel_densities
        row_index = min(number_of_types-1, len(steel_densities)-1)
        col_index = len(steel_densities)-1
        selected_densities = []
        while (row_index >= 0):
            selected_densities.append(steel_densities[col_index])
            col_index = container[row_index][col_index].ref
            row_index -= 1
        return sorted(selected_densities)
    
    def _get_shear_types(self, selected_densities: List[float]) -> List[ShearType]:
        """returns shear types based on the selected denisties in optimization process.

        Args:
            selected_densities (List[float]): selected densities in optimization algorithm
        Returns:
            List[ShearType]: the types of the shear rebars
        """
        rebar = self._rebar
        max_interval = self._max_interval
        shear_types = []
        
        i = 1 # counter for ID number
        for density in selected_densities:
            j = 1
            while True:
                if (j * rebar.get_area()/density) < MIN_SHEAR_INTERVAL:
                    j += 1
                else:
                    # round down to cm
                    interval = min(math.floor(100 * j * rebar.get_area()/density)/100, max_interval)
                    new_shear_type = ShearType(rebar, interval, j, i)
                    if not any([new_shear_type == shear_type for shear_type in shear_types]):
                        shear_types.append(new_shear_type)
                        i += 1
                    break
        return shear_types

    def _set_shear_types(self, shear_types: List[ShearType]) -> None:
        """set shear type of each shear zone

        Args:
            shear_types (List[ShearType]): the generated shear types based on selected densities.
        """
        shear_zones = self._shear_zones
        i = 0 # shear zone counter
        j = 0 # shear type counter
        while i < len(shear_zones):
            if shear_zones[i].steel_density <= shear_types[j].get_density():
                shear_zones[i].shear_type = shear_types[j]
                i += 1
                continue
            else:
                j += 1
    
    def get_shear_types(self) -> List[ShearType]:
        """returns generated shear types based on 

        Returns:
            List[ShearType]: list of shear types
        """
        return self._shear_types

    






            
        
    
                    



