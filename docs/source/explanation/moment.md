Resistant Moment
===================================


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


ACI-318 table 21.2.2

$$
  \phi = \left\{
  \begin{array}{lr}
  0.65, & \epsilon_t \leq \epsilon_{ty} \\
  0.75 + 0.15 \frac{\epsilon_t - \epsilon_{ty}}{0.005-\epsilon_{ty}}, & \epsilon_{ty} < \epsilon_{t} < 0.005 \\
  0.9, & \epsilon_{t} \geq 0.005
  \end{array}
  \right.
$$

$$
  \begin{align*}
  a &= \frac{As f_y}{0.85 f'_c b} \\
  c &= \frac{a}{\beta_1} \\
  \epsilon_t &= 0.003 \frac{d-c}{c}
  \end{align*}
$$

$$
  M_u = \phi As f_y \left( d - \frac{As f_y}{1.7 b f'_c} \right)
$$
