Shear Rebars
===================================

In this chapter, we explore the algorithm for placing shear reinforcement.

Where the one-way shear of a strip is more than the concrete can carry, SAFE gives the required shear steel along the strip, as an area per unit length.
OPTiBAR connects these values at the stations of the strip linearly, and then:

* Sets the required shear steel to zero inside the columns and inside the strips that cross the strip, since no shear rebars are placed there.
* Near the faces of the columns and crossing strips, within one foundation thickness of the face, caps the required steel at its value at the face. So the critical section is at one thickness from the face.

A **shear zone** is a part of the strip where the required shear steel is more than zero.
Zones shorter than **Elimination, Shear** get no shear rebars.
Each zone is designed for the largest required steel in it.

```{warning}
The code clauses for these rules are not documented yet.
OPTiBAR takes the critical section at one foundation thickness from the face; design codes usually take it at the effective depth $d$, which is a little closer to the face.
```

The designed algorithm for placing shear reinforcement is as follows:

* Find regions with positive values of the required shear steel.
* Find the maximum required steel in each of these regions.
* Find a specified number (user-input) of unit densities along the length so that the minimum amount of shear steel is used by increasing the density in each region. This is done similarly to increasing the length of segments with a dynamic programming algorithm.
* For each selected density, generate a shear type using the algorithm below and assign it to each region.

Choosing the shear types
------------------------

The number of shear types in the foundation is set by **Number of Types, Shear**.
Sort the distinct required densities of the zones, $\rho_1 < \rho_2 < \ldots < \rho_n$, and let $\ell_i$ be the total length of the zones with density $\rho_i$.
If $\rho_k$ is a selected density, every zone with a density between the previous selected density and $\rho_k$ gets the type of $\rho_k$.
The steel used is $\sum_i \ell_i \rho_{s(i)}$, where $\rho_{s(i)}$ is the selected density zone $i$ is assigned to.
The densities with the least steel are found by dynamic programming, like the practical lengths:

$$
    \text{steel}(p,q) = \left\{
    \begin{array}{lr}
    \min_{k=p-1,\ldots,q-1}\left\{ \text{steel}(p-1,k) + \rho_q \sum^{q}_{i=k+1} \ell_i \right\}, & p>1 \\
    \rho_q \sum^{q}_{i=1} \ell_i ,& p=1
    \end{array}
    \right.
$$

where $\text{steel}(p,q)$ is the least steel for the zones up to $\rho_q$ with $p$ types, the largest of which is $\rho_q$.
The largest density is always selected, so every zone gets a type.

```{prf:algorithm} Shear type of a density
:label: shear-type-alg

**Inputs** A density $\rho$, the area $A_b$ of the shear rebar, the minimum spacing $s_{min} = 15$ cm, and the maximum spacing $s_{max} = h_{min}/2$, half the smallest thickness of the foundation

**Output** The number of legs $n$ and the spacing $s$ of a shear type

1. $n \leftarrow 1$
2. While $n A_b / \rho < s_{min}$: $n \leftarrow n + 1$
3. $s \leftarrow \min\{ n A_b / \rho \text{, rounded down to 1 cm},\ s_{max} \}$
```

Shear types with the same number of legs and spacing are merged.
A zone of length $L$ gets $n \lceil L / s \rceil$ stirrups.
The length of a stirrup is the thickness of the foundation less the covers, plus a 135° and a 90° hook.

```{warning}
OPTiBAR does not check the minimum shear steel, nor the maximum spacing of the legs across the strip.
Check them against the design code of your project.
```
