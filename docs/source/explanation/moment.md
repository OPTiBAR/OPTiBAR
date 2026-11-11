Resistant Moment
===================================

The design of a strip for flexure is checked by SAFE, but the detailing changes the steel along the strip: the theoretical lengths are extended to required lengths, and these are rounded and unified to practical lengths.
To show that the detailed strip still carries its loads, OPTiBAR draws the resisting moment $\phi M_n$ of every strip, top and bottom, next to the factored moment $M_u$ from SAFE.
$\phi M_n$ should be above $M_u$ everywhere.

![The resisting moment of a cantilever follows its bars; within $L_d$ of a cut bar end it rises linearly](../_static/images/resisting_moment.png)

Effective steel area
--------------------

A bar only counts fully in a section where it is developed, that is, where it runs at least $L_d$ into the concrete on that side.
If a section is at a distance $x < L_d$ from the end of a bar, only the part $\dfrac{x}{L_d} A_b$ of its area is counted.

So the effective steel area along a level of a strip is:

* the typical rebars, fully along the strip,
* plus every additional rebar, rising linearly from zero at each straight end to its full area at $L_d$ from that end.

Bent (hooked) ends count fully, as the hook anchors the bar.
Since the area changes linearly near the bar ends, and the moment depends almost linearly on the area, the resisting moment changes almost linearly there too.

```{note}
Only the tension steel is counted, so $\phi M_n$ is a little less than the real resisting moment of the section.
```

Between the faces of a column, the factored moment is taken as a straight line between its values at the faces, as the required steel is, see [Columns](../reference/detailing-rules.md#columns).

Resisting moment of a section
-----------------------------

Each section is a rectangle of width $b$, the width of the strip there, and effective depth $d$, with a steel area $A_s$.

ACI-318 table 22.2.2.4.3

$$
  \beta_1 = \left\{
  \begin{array}{lr}
  0.85, & 17 \leq f'_c \leq 28 \\
  0.85 - \frac{0.05(f'_c-28)}{7}, & 28 < f'_c < 55 \\
  0.65, & f'_c \geq 55
  \end{array}
  \right.
$$

When the steel ratio $\rho = \dfrac{A_s}{b d}$ is less than the balanced ratio $\rho_b = 0.85 \beta_1 \dfrac{f'_c}{f_y} \dfrac{600}{600 + f_y}$, the steel yields:

$$
  \begin{align*}
  a &= \frac{As f_y}{0.85 f'_c b} \\
  M_n &= As f_y \left( d - \frac{As f_y}{1.7 b f'_c} \right)
  \end{align*}
$$

Otherwise $a$ is found from the strain compatibility of the section with $E_s = 200$ GPa, and $M_n = 0.85 f'_c a b \left(d - \frac{a}{2}\right)$.
Then

$$
  \begin{align*}
  c &= \frac{a}{\beta_1} \\
  \epsilon_t &= 0.003 \frac{d-c}{c}
  \end{align*}
$$

and the strength reduction factor follows ACI-318 table 21.2.2, with $\epsilon_{ty} = 0.002$:

$$
  \phi = \left\{
  \begin{array}{lr}
  0.65, & \epsilon_t \leq \epsilon_{ty} \\
  0.65 + 0.25 \frac{\epsilon_t - \epsilon_{ty}}{0.005-\epsilon_{ty}}, & \epsilon_{ty} < \epsilon_{t} < 0.005 \\
  0.9, & \epsilon_{t} \geq 0.005
  \end{array}
  \right.
$$

$$
  \phi M_n = \phi As f_y \left( d - \frac{As f_y}{1.7 b f'_c} \right)
$$
