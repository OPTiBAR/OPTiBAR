Shear Rebars
===================================

In this chapter, we explore the cutting algorithm and design an algorithm for placing shear reinforcement.

The required amount of shear steel for each section is given per unit area. Considering the constraints outlined in (this section should be completed), there is no need to place steel in the intersection region of two sections. Additionally, there is no need for steel under each column, considering the depth of the section from the column on both sides.

The designed algorithm for placing shear reinforcement is as follows:

* Find regions with positive values of the required shear steel.
* Find the maximum required steel in each of these regions.
* Find a specified number (user-input) of unit densities along the length so that the minimum amount of shear steel is used by increasing the density in each region. This is done similarly to increasing the length of segments with a dynamic programming algorithm.
* For each selected density, generate a shear type using Algorithm shear_type_alg and assign it to each region.



```{prf:algorithm} Ford–Fulkerson
:label: my-algorithm

**Inputs** Given a Network $G=(V,E)$ with flow capacity $c$, a source node $s$, and a sink node $t$

**Output** Compute a flow $f$ from $s$ to $t$ of maximum value

1. $f(u, v) \leftarrow 0$ for all edges $(u,v)$
2. While there is a path $p$ from $s$ to $t$ in $G_{f}$ such that $c_{f}(u,v)>0$
	for all edges $(u,v) \in p$:

	1. Find $c_{f}(p)= \min \{c_{f}(u,v):(u,v)\in p\}$
	2. For each edge $(u,v) \in p$

		1. $f(u,v) \leftarrow f(u,v) + c_{f}(p)$ *(Send flow along the path)*
		2. $f(u,v) \leftarrow f(u,v) - c_{f}(p)$ *(The flow might be "returned" later)*
```
