Detailing Rules
===================================

This page lists the rules OPTiBAR follows when it places the longitudinal rebars of a strip: which bars go in, how many, and how far they run.
Every strip has a top and a bottom level, and each level is detailed on its own.

```{warning}
The code clauses behind several rules on this page are not documented yet.
Where a rule has no reference, check it against the design code of your project.
```

Thermal and typical rebars
--------------------------

A level of a strip that needs no flexural steel, where SAFE's required steel area is zero along the whole strip, gets **thermal** rebars.
Any other level gets **typical** rebars.
This is why the cross strips of a mat often get thermal rebars: their moments are small.
A cross strip with a large moment gets typical rebars instead.

```{tip}
To use thermal rebars in a strip that carries a large moment, leave the strip out of the SAFE model and add its rebars to the drawing by hand.
```

### Thermal rebars

The thermal rebars have a steel ratio of 0.0018 of the gross section, half in the top and half in the bottom: each level gets at least $0.0009\,b\,h$, rounded up to whole bars.
Bars are added until the clear spacing is less than 35 cm.

```{warning}
The 35 cm spacing limit is a fixed value in OPTiBAR, not derived from the design code; its source is not documented.
```

(typical-rebars)=
### Typical rebars

The typical rebars ensure the minimum flexural steel in every level that needs flexural steel.
Their number comes from the **Typical Arrangement** setting:

* **Interval**: the strip width divided by the interval, rounded up. A strip 1.10 m wide with an interval of 20 cm gets 6 bars.
* **Number**, per strip and level in the Advanced tab: the given number of bars.

The number is not raised to the minimum: you may place less than the minimum steel.
In that case, and when the spacing is out of range, OPTiBAR places the bars and adds a warning to the report:

* the typical rebars are less than a steel ratio of 0.0018, $A_s < 0.0018\,b\,h$;
* the clear spacing of the bars, typical and additional together, is more than 35 cm where the required steel is smallest;
* the clear spacing is less than 2.5 cm, or less than the bar diameter, where the required steel is largest.

```{warning}
The code clauses for the minimum ratio and the spacing limits are not documented yet.
```

(additional-rebars)=
Additional rebars
-----------------

Where the required steel is more than the typical rebars provide, the rest is covered by **additional** rebars.
SAFE only gives the required steel area, so OPTiBAR first places bars to cover the diagram, which gives their **theoretical** lengths, see [Theoretical Length](../explanation/theoretical.md).
Additional rebars with a theoretical length shorter than **Elimination, Additional** are left out.

Then every bar is extended to its **required** length, so that both conditions below hold at each end:

1. The bar runs past the end of its theoretical length by at least the effective depth $d$.
2. The bar runs at least $L_d$ past the point where it is needed at full strength: the peak of the diagram for the shortest bar of a stack, and the theoretical end of the next shorter bar for the others.

$$
  \text{required end} \geq \max\{\, \text{theoretical end} + d,\ \text{theoretical end of the next shorter bar} + L_d \,\}
$$

Extending a bar can let the next bar of the stack be shorter, so OPTiBAR chooses the extensions of a whole stack together, with the least total length; see [Required Length](../explanation/required.md).

```{warning}
OPTiBAR extends bars past the end of their theoretical length by $d$ only.
ACI 318 asks for at least the larger of $d$ and $12 d_b$, which is longer for bars thicker than $d/12$.
Check this for thin foundations with large bars.
```

At last, the required lengths are rounded, unified and reduced to the numbers of length types you allow, which gives the **practical** lengths, see [Practical Length](../explanation/practical.md).
All the steps run without user input; the settings only set the limits.

Bars that reach the side of the foundation, less the side cover, are bent.

(columns)=
Columns
-------

OPTiBAR reads the column sizes from the **Load Size** of the point loads in SAFE; point loads without a load size, or smaller than 5 cm, are not columns.

Between the faces of a column, the required steel diagram is replaced by a straight line between its values at the two faces.
So the steel needed under the column is the steel needed at its faces, and the peak of SAFE's diagram inside the column is not used.
The same is done for the factored moment diagram, see [Resistant Moment](../explanation/moment.md).

```{warning}
The code clause for taking the steel at the column faces is not documented yet.
```

(special-lengths)=
Special lengths
---------------

The development length $L_d$ is calculated from the concrete and steel of the SAFE model, with ACI 318's simplified expressions for deformed bars in tension, with $\psi_e = \lambda = 1$:

$$
  L_d = \left\{
  \begin{array}{lr}
  \dfrac{f_y\,\psi_t}{2.1\,\sqrt{f'_c}}\, d_b, & d_b < 20\ \text{mm} \\[2ex]
  \dfrac{f_y\,\psi_t}{1.7\,\sqrt{f'_c}}\, d_b, & d_b \geq 20\ \text{mm}
  \end{array}
  \right.
$$

with $f_y$ and $f'_c$ in MPa, $\psi_t = 1.3$ for top bars and $1.0$ for bottom bars, rounded up to 1 cm.
The overlap length is $1.3\,L_d$, rounded up to 5 cm.
The bend length is $13.7\,d_b$ for 90° hooks and $11\,d_b$ for the 135° hooks of shear rebars, rounded up to 5 cm.

All of them can be changed in **Advanced > Special Lengths**, for example when closely spaced bars or shear rebars call for longer lengths; see [Adjust the detailing of a project](../how-to/adjust-detailing.md).
The drawing lists the overlap lengths used in its tables.
