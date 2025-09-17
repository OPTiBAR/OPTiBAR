Practical Length
===================================


.. math::

    \text{len}(p,q) = \left\{
    \begin{array}{lr}
    \min_{i=p-1,\ldots,q-1}\left\{ \text{len}(p-1,i) + \sum^{q-1}_{j=i+1} (L_q - L_j)N_j\right\}, & p>1 \\
    \sum^{q-1}_{j=1}(L_q- L_j)N_j ,& p=1
    \end{array} 
    \right.

.. math::
    \text{ref}(p,q) = \left\{
    \begin{array}{lr}
    \text{arg}\,\min_{i=p-1,\ldots,q-1}\left\{ \text{len}(p-1,i) + \sum^{q-1}_{j=i+1} (L_q - L_j)N_j\right\}, & p>1 \\
    \varnothing ,& p=1
    \end{array} 
    \right.

.. math::
    f(x) = \left\{
    \begin{array}{lr}
    \infty, & x > 0 \\
    1 ,& x \leq 0
    \end{array} 
    \right.


.. math::
    \text{len}(p,q) = \left\{
    \begin{array}{lr}
    \min_{i=p-1,\ldots,q-1}\left\{ \text{len}(p-1,i) + \sum^{q-1}_{j=i+1} (L_q - L_j)N_j f(L_q-\overline{L}_j)\right\}, & p>1 \\
    \sum^{q-1}_{j=1}(L_q- L_j)N_j f(L_q-\overline{L}_j) ,& p=1
    \end{array} 
    \right.

.. math::
    \text{ref}(p,q) = \left\{
    \begin{array}{lr}
    \text{arg}\min_{i=p-1,\ldots,q-1}\left\{ \text{len}(p-1,i) + \sum^{q-1}_{j=i+1} (L_q - L_j)N_j f(L_q-\overline{L}_j)\right\}, & p>1 \\
    \varnothing ,& p=1
    \end{array} 
    \right.

.. code-block:: python

    def decrease_col_side(stations: List[Station], cols_sides: List[Tuple[int,int]]):
        """
        Decrease the required steel under the columns
        stations: list of station, each satation is a Station object and has two fields x and as 
        cols_sides: list of column sides, each element is a tuple (start, end) stations
        """