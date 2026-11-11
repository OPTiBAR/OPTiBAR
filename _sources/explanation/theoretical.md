Theoretical Length
===================================
To obtain the theoretical lengths of the pieces, it is necessary to first determine the cross-sectional steel area required along the length of the strip. Then, by reducing step by step, the required amount of steel, the theoretical length, and the location of the pieces are obtained.

Note that this algorithm is only applicable when all the pieces obtained in one stage of the algorithm have the same diameter.

In regions where a concrete column is present, it is sufficient to satisfy the required steel on each of the two faces of the column: the required steel diagram is replaced by a straight line between the faces, see [Columns](../reference/detailing-rules.md#columns).

```{warning}
The code clause for this rule is not documented yet.
```

The required steel diagram is corrected at the columns with the following algorithm (`Diagram.linearize_period`). The column sides come from the column sizes, see [Columns](../reference/detailing-rules.md#columns).

```{prf:algorithm} Reducing the required steel at the column sides
:label: column-side-reduction

**Inputs**
* $stationList$: the stations of the strip, in ascending order
* $AsList$: the required steel at each station of $stationList$
* $ColumnSideStationsList$: pairs of stations $(sideStart, sideEnd)$, the faces of each column

**Output** The corrected $stationList$ and $AsList$

1. For each $(sideStart, sideEnd) \in ColumnSideStationsList$:
    1. If $sideStart < stationList[0]$: $sideStart \leftarrow stationList[0]$
    2. If $sideEnd > stationList[end]$: $sideEnd \leftarrow stationList[end]$
    3. For each $side \in \{sideStart, sideEnd\}$ that falls between two stations: add $side$ to $stationList$, and its $As$, interpolated between the two stations, to $AsList$.
    4. Remove every station strictly between $sideStart$ and $sideEnd$, with its $As$.
```

(theoretical-typical)=
Typical rebars
--------------

There are four methods for placing the typical rebars, which are as follows:

- **Minimum ratio (`MIN_RATIO`):** the minimum steel is placed in each strip, $A_s = 0.0018\,b\,h$, rounded up to whole bars.
- **Count (`COUNT`):** the given number of bars is placed. If it is less than the minimum steel, a warning is reported, see [Detailing Rules](../reference/detailing-rules.md#typical-rebars).
- **Interval (`INTERVAL`):** the strip width divided by the interval, rounded up.
- **Smart (`SMART`):** The minimum steel is placed. If the distance from the first station with zero steel demand to any of the edges is more than the foundation thickness, or if the distance between two consecutive zero-demand intermediate stations is more than twice the foundation thickness, the placement is completed. Otherwise, another bar is placed.

The app uses `INTERVAL`, and `COUNT` for the strips set on the **Strips** page.

The area of the typical rebars is subtracted from the required steel diagram (`Diagram.insert_typical`), with {prf:ref}`reduce-as`.
If the diagram is still positive somewhere, the rest is covered by additional rebars.

Additional rebars
-----------------

The additional rebars are found row by row (`Mesh._insert_additional`):

1. Find the parts of the strip where the remaining required steel is more than zero ({prf:ref}`theoretical-piece`). Each part is the **theoretical** length of one bar; together they form a **row**.
2. Subtract the area of one additional rebar from the diagram ({prf:ref}`reduce-as`).
3. Repeat while the diagram is positive anywhere.

The first row holds the longest bars, at the bottom of the stacks; every following row is shorter and lies above.
Bars with a theoretical length shorter than **Elimination, Additional** are left out of their row.

```{prf:algorithm} Theoretical pieces of one row
:label: theoretical-piece

**Inputs**
* $stationList$: the stations of the strip, in ascending order
* $AsList$: the remaining required steel at each station of $stationList$, never negative

**Output** $rowList$: the list of $(start, end)$ periods of the pieces of the row

1. $drawingFlag \leftarrow False$, $rowList \leftarrow []$
2. For each $i \in \{0, \ldots, len(stationList)-1\}$:
    1. If $drawingFlag = False$:
        1. If $(i = 0$ and $AsList[i] > 0)$ or $(i < len(AsList)-1$ and $AsList[i+1] > 0)$:
            1. $drawingFlag \leftarrow True$
            2. $start \leftarrow stationList[i]$
    2. Else:
        1. If $i = len(stationList)-1$ or $(AsList[i] = 0$ and $AsList[i+1] = 0)$:
            1. $drawingFlag \leftarrow False$
            2. $end \leftarrow stationList[i]$
            3. $rowList.append((start, end))$
3. Return $rowList$
```

A piece ends at the first of two consecutive zero stations, so a single zero station between two positive parts does not split the piece; {prf:ref}`reduce-as` keeps a single zero station where the diagram crosses zero and removes the ones in between.

```{prf:algorithm} Reducing the As diagram
:label: reduce-as

**Inputs**
* $stationList$: the stations of the strip, in ascending order
* $AsList$: the required steel at each station of $stationList$
* $rebarAs$: the area to subtract, one additional rebar, or all the typical rebars

**Output** The revised $stationList$ and $AsList$

1. For each $i$: $AsList[i] \leftarrow AsList[i] - rebarAs$
2. For each pair of neighbouring stations $i$, $i+1$ with $AsList[i] \cdot AsList[i+1] < 0$: find the station where the line between $(stationList[i], AsList[i])$ and $(stationList[i+1], AsList[i+1])$ crosses zero, and insert it with $As = 0$.
3. For each $i$: if $AsList[i] < 0$ then $AsList[i] \leftarrow 0$
4. Remove every zero station whose two neighbours are also zero.
```
