Practical Length
===================================



$$
    \text{len}(p,q) = \left\{
    \begin{array}{lr}
    \min_{i=p-1,\ldots,q-1}\left\{ \text{len}(p-1,i) + \sum^{q-1}_{j=i+1} (L_q - L_j)N_j\right\}, & p>1 \\
    \sum^{q-1}_{j=1}(L_q- L_j)N_j ,& p=1
    \end{array}
    \right.
$$

$$
    \text{ref}(p,q) = \left\{
    \begin{array}{lr}
    \text{arg}\,\min_{i=p-1,\ldots,q-1}\left\{ \text{len}(p-1,i) + \sum^{q-1}_{j=i+1} (L_q - L_j)N_j\right\}, & p>1 \\
    \varnothing ,& p=1
    \end{array}
    \right.
$$


$$
    f(x) = \left\{
    \begin{array}{lr}
    \infty, & x > 0 \\
    1 ,& x \leq 0
    \end{array}
    \right.
$$

$$
    \text{len}(p,q) = \left\{
    \begin{array}{lr}
    \min_{i=p-1,\ldots,q-1}\left\{ \text{len}(p-1,i) + \sum^{q-1}_{j=i+1} (L_q - L_j)N_j f(L_q-\overline{L}_j)\right\}, & p>1 \\
    \sum^{q-1}_{j=1}(L_q- L_j)N_j f(L_q-\overline{L}_j) ,& p=1
    \end{array}
    \right.
$$

$$
    \text{ref}(p,q) = \left\{
    \begin{array}{lr}
    \text{arg}\min_{i=p-1,\ldots,q-1}\left\{ \text{len}(p-1,i) + \sum^{q-1}_{j=i+1} (L_q - L_j)N_j f(L_q-\overline{L}_j)\right\}, & p>1 \\
    \varnothing ,& p=1
    \end{array}
    \right.
$$
