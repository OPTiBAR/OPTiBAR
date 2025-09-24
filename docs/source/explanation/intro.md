Basic Concepts
===================================

In this chapter, the problem is defined, and its inputs and outputs are specified. Then, the main algorithm for solving it is presented, and its constituent parts are generally described.

The input to this problem is the required cross-sectional steel area in stations along a design strip.
These values are provided for all design strips and upper and lower meshs.
This input can be extracted from the output of analytical software such as *CSI SAFE*.
In addition to this, the required cross-sectional area of shear reinforcement in these sections is also observable in the output of some design software.
The input values are more precisely described in the following list:

* Material types for rebar and concrete
* Design strips

  * Depth
  * Coordinates of stations
  * Coordinates of columns
  * Shear punch for each column (!)
  * Cross-sectional steel area in the upper network
  * Cross-sectional steel area in the lower network
  * Shear steel cross-sectional area (!)

Items marked with (!) may not be available in the output of some *CSI SAFE* software versions.

By using the steel quantity at each station, the lengths of the required rebars can be calculated. These lengths are referred to as the **theoretical** lengths of the components.

The provided steel quantities in the input represent the theoretical steel values, and according to the CSI-318 codes, certain values must be added to satisfy the code requirements.
These values will be explained further.
After adding the lengths mentioned in the code, the **allowable** lengths of the rebars are obtained.
The map drawn based on allowable lengths is not practical for three reasons:

* The non-roundness of the lengths makes it difficult for workers to cut and locate, and for supervisors to check, for example, a rebar with a length of 3.77 m. The designer may prefer a length of 3.80 m or 4.00 m.
* There may be too many different lengths used throughout the foundation. This complicates the maps and the rebar cutting process.
* The abundance of lengths used side by side in a section of the strip. This complicates map reading and execution for the contractor and makes it difficult for the supervisor to check.

To solve this problem, it is possible to reduce the number of lengths by increasing the length of a set of components.
The lengths obtained after this stage are called **practical** lengths.

In the following chapters, each of these stages will be examined.

```{mermaid}
    ---
    title: Main stages of the algorithm
    ---
    flowchart LR
        id1(Parse the Analysis software output) --> id2(Theoretical Length) --> id3(Allowable Length) --> id4(Calculate <br>Practical Length)
```


Notations
-----------

* $L_d$:
* $d$: Effective depth of the foundation.
* $b$: Width of the foundation.
* $As$: Area of steel in the section.
* $\epsilon_t$: Total strain.
* $\epsilon_{ty}$: Yield strain.
