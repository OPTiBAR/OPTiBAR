Shear
===================================

In this chapter, we explore the cutting algorithm and design an algorithm for placing shear reinforcement.

The required amount of shear steel for each section is given per unit area. Considering the constraints outlined in (this section should be completed), there is no need to place steel in the intersection region of two sections. Additionally, there is no need for steel under each column, considering the depth of the section from the column on both sides.

The designed algorithm for placing shear reinforcement is as follows:

* Find regions with positive values of the required shear steel.
* Find the maximum required steel in each of these regions.
* Find a specified number (user-input) of unit densities along the length so that the minimum amount of shear steel is used by increasing the density in each region. This is done similarly to increasing the length of segments with a dynamic programming algorithm.
* For each selected density, generate a shear type using Algorithm shear_type_alg and assign it to each region.

