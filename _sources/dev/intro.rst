Basic Concepts
===================================

In this chapter, the problem is defined, and its inputs and outputs are specified. Then, the main algorithm for solving it is presented, and its constituent parts are generally described.

The input to this problem is the required cross-sectional steel area in stations along a design strip. These values are provided for all design strips and upper and lower pile networks. This input can be extracted from the output of analytical software such as \textit{CSI SAFE}. In addition to this, the required cross-sectional area of shear reinforcement in these sections is also observable in the output of some design software. The input values are more precisely described in the following list:

* Material types for steel and concrete
* Design strips
  
  * Depth
  * Coordinates of stations
  * Coordinates of columns
  * Formwork shear for each column (!)
    
    * Cross-sectional steel area in the upper network
    * Cross-sectional steel area in the lower network
    * Shear steel cross-sectional area (!)

Items marked with (!) may not be available in the output of some `CSI SAFE` software versions.

By using the steel quantity at each station, the lengths of the required rebars can be calculated. These lengths are referred to as the `theoretical` lengths of the components.

The provided steel quantities in the input represent the theoretical steel values, and according to the Iranian and American codes, certain values must be added to satisfy the code requirements. These values will be explained further. After adding the lengths mentioned in the code, the allowable lengths of the rebars are obtained. These lengths are called `practical` lengths.

The map drawn based on practical lengths is not executable for two reasons:

* Non-roundness of lengths.
* The variety of lengths used in the entire pile. This complexity makes the maps and the rebar cutting process excessively intricate.
* The abundance of lengths used side by side in a section of the strip. This complicates map reading and execution for the contractor and makes it difficult for the supervisor to check.

To solve this problem, it is possible to reduce the number of lengths by increasing the length of a set of components. The large number of possible cases for this process necessitates an intelligent algorithm to achieve the goal of reducing the number of lengths with the least increase in length.

The lengths obtained after this stage are called `executive` lengths. The main stages of the algorithm are shown in Figure \ref{mainalg}.

In the following chapters, each of these stages will be examined.


Notations
-----------

* :math:`d`: depth of the strip.
* :math:`L_d`: 