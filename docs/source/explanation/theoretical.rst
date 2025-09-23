Theoretical Length
===================================
To obtain the theoretical lengths of components, it is necessary to first determine the cross-sectional steel area required along the length of the strip. Then, by reducing step by step, the required amount of steel, the length, and the location of the components are obtained.

Note that this algorithm is only applicable when all the components obtained in one stage of the algorithm have the same diameter.

According to the clause (this part should be completed) of the Iranian code and the clause (this part should be completed) of the American code, in regions where a concrete column is present, it is sufficient to satisfy the maximum required steel on each of the two faces of the column. Also, for steel columns, the mid-height is considered next to the base plate and on the column.

(Note: The placeholders (this part should be completed) indicate that specific information or details need to be filled in based on the actual content of the codes or regulations being referred to.)





There are three methods for placing general reinforcements, which are as follows:

- **Minimum (minRatio):** In this method, the minimum allowable reinforcement according to the code is placed in each strip. 
  (:math:`area = minRatio * width * depth`)
- **Count (count):** If the reinforcement meets the minimum requirement, the desired number of reinforcements is placed. If the minimum reinforcement is not met, the minimum amount of reinforcement is placed.
- **Smart (smart):** The minimum reinforcement is placed. If the distance from the first station with zero steel demand to any of the edges is more than the pile depth, or if the distance between two consecutive zero-demand intermediate stations is more than twice the pile depth, the reinforcement placement is completed. Otherwise, another reinforcement is placed.

Strengthening
---------------

The algorithm is generally depicted in Figure \ref{generalflow}, and each of the stages will be explained in detail in the following.

.. code-block:: python

    def decrease_col_side(stations: List[Station], cols_sides: List[Tuple[int,int]]):
        """
        Decrease the required steel under the columns
        stations: list of station, each satation is a Station object and has two fields x and as 
        cols_sides: list of column sides, each element is a tuple (start, end) stations
        """
        # add sides to the stations
        for col_side in cols_sides:
            for side in col_sides:
                if side >= stations[0].x and side <= stations[-1].x:
                    # add side to stations and find its As with linear interpolation
        for (start,end) in cols_sides:
            if start < stations[0].x:
                start = stations[0].x
            if end > stations[-1].x:
                end = stations[-1].x
            # remove all stations between start and end
  
.. code-block:: python

    def set_additional_rebar(stations: List[Station]):
        """
        Set additional reinforcement
        """
        rows = []
        while max(map(s.x, stations)) > 0:
            flag = False
            row = []
            start = None
            end = None
            for i in range(len(stations)):
                if flag == False:
                    if (i == 0 and stations[i].as > 0) or (i < len(stations)-1 and stations[i+1].as > 0):
                        flag = True
                        start = stations[i].x
                    else: # flag == True
                        if (i == len(stations)-1) or (stations[i].as == 0):
                            flag = False
                            end = stations[i].x
                            row.append((start, end))
            rows.append(row)
        return rows

.. code-block:: python

    def decrease_As(stations: List[Station], y: float):
        """
        lower the curve by y
        """
        for station in stations:
            station.as = station.as - y
        revised_stations = []
        for i in range(len(stations)):
            if i < len(stations) -1 : # all stations except the last one
                if stations[i].as > 0:
                revised_stations.append(stations[i])
                if stations[i+1].as < 0:
                    # find the intersection of zero line and the line between i and i+1 and it to the stations
                elif stations[i].as < 0:
                    revised_stations.append(Station(x=stations[i].x, as=0))
                    if stations[i+1].as > 0:
                        # find the intersection of zero line and the line between i and i+1 and it to the stations
                else: # stations[i].as == 0
                    revised_stations.append(stations[i])
            else: # the last station
                if stations[i].as >= 0:
                    revised_stations.append(stations[i])
                else:
                    revised_stations.append(Station(x=stations[i].x, as=0))
        return revised_stations

