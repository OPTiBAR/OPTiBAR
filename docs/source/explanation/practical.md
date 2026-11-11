Practical Length
===================================

To make the required lengths buildable, they are rounded, and the number of different lengths is reduced in two sets: in every stack, and in the whole foundation.
Fewer lengths in a stack make the drawing easier to read and to build; fewer lengths in the foundation make the bars easier to cut.
The lengths obtained are the **practical** lengths.

The whole process
-----------------

The lengths of the additional rebars are found with the following algorithm (`Mesh._theoretical_to_practical` and `Foundation._set_length_type_num`):

```{prf:algorithm} Finding the lengths of the pieces
:label: practical-pipeline

**Inputs** The required steel diagrams of the strips and the settings of the calculation

**Output** The practical lengths of all the pieces

1. Place the typical rebars, see [Theoretical Length](theoretical.md#theoretical-typical).
2. Find the theoretical lengths of the additional rebars ({prf:ref}`theoretical-piece`).
3. Add $d$ and $L_d$ to the ends of the pieces in the best way ({prf:ref}`stackify` and [Required Length](required.md)); this gives the required lengths.
4. Merge the pieces that meet ({prf:ref}`merge-pieces`) by their required lengths. If any piece was merged, go to step 3.
5. Correct the pieces that pass the sides of the strip ({prf:ref}`bend-pieces`):
    1. Bend the pieces whose theoretical length passes the side.
    2. Bend the pieces whose required length passes the side where $L_d$ governs; cut them at the side where $d$ governs.
6. Find the upper bound of each piece, and round its length (see [Rounding](#rounding)).
7. Set the practical period of each piece from its rounded length ({prf:ref}`length-adjustment`).
8. Merge the pieces that meet by their practical lengths. If any piece was merged, go to step 3.
9. Reduce the number of length types of the whole foundation ({prf:ref}`total-algorithm`) and of every stack ([integer program](#stack-program)).
10. Set the practical periods again from the reduced lengths and merge the pieces that meet. If any piece was merged, go to step 3 for all the strips and repeat step 9.
```

(rounding)=
Upper bound and rounding
------------------------

Each piece has an **upper bound** on its length: the 12 m stock length for a bar longer than 12 m, and otherwise the length of the strip less the side covers plus the bends of the piece, or 12 m if that is shorter.

The length of a piece is rounded up to 10 cm.
If the rounded length passes the upper bound, it is rounded down to 10 cm instead.

```{warning}
The comment in the code (`Mesh._round_piece`) and the original design both say 5 cm, but the code rounds to 10 cm (`ROUND_UNIT = 0.1` in `setting.py`).
```

(bars-longer-than-12-m)=
Bars longer than 12 m
---------------------

Bars come in 12 m stock lengths, so a bar longer than 12 m is made of several pieces, which overlap by the overlap length $o$ of the bar, see [Special Lengths](../reference/detailing-rules.md#special-lengths).
A bar of length $L > 12$ m needs

$$
  n = \left\lceil \frac{L - o}{12 - o} \right\rceil
$$

pieces, and its **net length**, the length of steel it uses, is $L + (n-1)\,o$.
All the pieces are 12 m long except one, the **shortest piece**, with a length of $L + (n-1)\,o - (n-1) \times 12$.
The shortest piece is at the bent end of the bar, or at the end side when the bar is not bent (`Piece.get_subpieces`).

Rounding and the reduction of length types change only the length of the shortest piece; the 12 m pieces stay as they are.
When the shortest piece is made longer, its overlap with the next piece gets longer than $o$.

Reducing the number of length types
-----------------------------------

### Problem definition

Pieces with lengths $L_1, \ldots, L_n$ are needed, $N_1, \ldots, N_n$ of each, written as $L = [L_1, \ldots, L_n]$ and $N = [N_1, \ldots, N_n]$, with $L_i < L_j$ for $i < j$ and $N_i \neq 0$.
We want fewer lengths, and the only change allowed is to supply a longer piece instead of a needed one.
The task is to limit the lengths to $p < n$ with the least total length of the pieces.

### Greedy algorithm

A simple approach removes one length at each step: the length whose pieces are cheapest to lengthen to the next longer length.

```{prf:algorithm} Greedy algorithm, one step
:label: greedy

**Inputs** The lengths $L = [L_1, \ldots, L_n]$ and the numbers $N = [N_1, \ldots, N_n]$

**Output** The new numbers $\hat{N} = [\hat{N}_1, \ldots, \hat{N}_n]$

1. $p \leftarrow \text{arg}\min_{i=1,\ldots,n-1} \left\{ N_i (L_j - L_i) \mid N_i \neq 0,\ j = \min\{ k > i \mid N_k \neq 0 \} \right\}$
2. $q \leftarrow \min\{ l > p \mid N_l \neq 0 \}$
3. $\hat{N}_i \leftarrow N_i$ for $i = 1, \ldots, n$
4. $\hat{N}_p \leftarrow 0$
5. $\hat{N}_q \leftarrow N_p + N_q$
```

The greedy algorithm doesn't always find the best solution.
For $L = [1,2,3,4]$ and $N = [5,4,7,1]$, limited to two lengths, it removes length 2 in the first step and length 1 in the second, which gives $N = [0,0,16,1]$ and a total length of 52.
Keeping lengths 2 and 4 instead gives $N = [0,9,0,8]$ and a total length of 50.

### Dynamic programming algorithm

The problem is solved directly with dynamic programming, in $O(n^3)$, instead of building an integer model and solving it with a solver.
It is split into two subproblems: first, $P$ lengths are chosen for the whole foundation (**Total**); then, for every stack, $PSUB$ of these $P$ lengths are chosen (**Stack**).

#### Choosing the lengths of the foundation

The best way to choose $p$ lengths out of $1, \ldots, q$ is built from the best ways to choose $p-1$ lengths out of $1, \ldots, q-1$, $1, \ldots, q-2$, …, $1, \ldots, p-1$.
$len(p,q)$ is the least increase of the total length when $p$ lengths are chosen out of $1, \ldots, q$:

$$
    \text{len}(p,q) = \left\{
    \begin{array}{lr}
    \min_{i=p-1,\ldots,q-1}\left\{ \text{len}(p-1,i) + \sum^{q-1}_{j=i+1} (L_q - L_j)N_j\right\}, & p>1 \\
    \sum^{q-1}_{j=1}(L_q- L_j)N_j ,& p=1
    \end{array}
    \right.
$$

If the minimum is reached at $\hat{i}$, the best way to choose $p$ lengths out of $1, \ldots, q$ is to choose $q$, and $p-1$ lengths out of $1, \ldots, \hat{i}$; the lengths $\hat{i}+1, \ldots, q-1$ are not chosen.
$ref(p,q)$ returns $\hat{i}$:

$$
    \text{ref}(p,q) = \left\{
    \begin{array}{lr}
    \text{arg}\,\min_{i=p-1,\ldots,q-1}\left\{ \text{len}(p-1,i) + \sum^{q-1}_{j=i+1} (L_q - L_j)N_j\right\}, & p>1 \\
    \varnothing ,& p=1
    \end{array}
    \right.
$$

As for the required lengths, the values are computed in a table, row by row from the top, and in every row from left to right.
To choose $p$ of the $n$ lengths, read the cell in row $p$ of the last column, and follow $ref$ from there.

**Example.** Let $L = [2,3,7,11,15]$ and $N = [1,5,3,10,4]$. Each cell holds the value of $len$ and of $ref$:

```{list-table} The table of the example
*   - $(0, \varnothing)$
    - $(1, \varnothing)$
    - $(25, \varnothing)$
    - $(61, \varnothing)$
    - $(137, \varnothing)$
*   - \-
    - $(0, 1)$
    - $(1, 2)$
    - $(13, 2)$
    - $(61, 4)$
*   - \-
    - \-
    - $(0, 2)$
    - $(1, 3)$
    - $(13, 4)$
*   - \-
    - \-
    - \-
    - $(0, 3)$
    - $(1, 4)$
*   - \-
    - \-
    - \-
    - \-
    - $(0, 4)$
```

To choose 3 of the 5 lengths, read row 3 of the last column: the total length grows by 13, to $\sum_{i} N_i L_i + 13$.
The longest length is always chosen; the cell gives $ref = 4$, so length 4 is chosen next; row 2 of column 4 gives $ref = 2$, so length 2 is chosen.
The chosen lengths are $[2,4,5]$, that is $[3, 11, 15]$.

#### Maximum length of a piece

Each piece also has an upper bound on its length, $\overline{L}_i$ (see [Rounding](#rounding)).
Some solutions are now not possible; they get the value $\infty$, and the two formulas become:

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

```{prf:algorithm} Choosing the lengths of the foundation
:label: total-algorithm

**Inputs** The shortest-piece lengths of all the additional rebars of the foundation, and the number of length types $P$ (**Total**)

**Output** The $P$ chosen lengths, or the smallest feasible number of length types

1. Group the pieces by length: the lengths $L_1 < \ldots < L_n$, the number $N_i$ and the smallest upper bound $\overline{L}_i$ of the pieces of each length.
2. If 12 m is not among the lengths, add it with $N = 0$ and $\overline{L} = 12$ m, so the stock length is always a candidate.
3. Compute the table of $len$ and $ref$ with the formulas above.
4. If $len(P, n) = \infty$: stop with the error that $P$ is not feasible, and give the smallest $p$ with $len(p, n) < \infty$.
5. Follow $ref$ from row $P$ of the last column to get the chosen lengths.
```

The smallest feasible number is shown in the report and saved as `min_feasible_num`, see [Outputs](../reference/outputs.md).

#### Choosing the lengths of a stack

This subproblem is solved for each stack on its own: out of the $P$ lengths of the foundation, $PSUB$ (**Stack**) are chosen.
Let $L_p,\ p = 1, \ldots, P$ be the lengths of the foundation, in ascending order; let $R_q,\ q = 1, \ldots, Q$ be the lengths of the pieces of the stack, $\overline{R}_q$ their upper bounds and $N_q$ their numbers.

```{prf:algorithm} Choosing the lengths of a stack, one cell
:label: stack-algorithm

**Inputs** $i$, $j$: choosing $i$ lengths out of the $j$ shortest lengths

**Output** $len(i,j)$, $ref(i,j)$

1. $minIndex \leftarrow None$, $minSum \leftarrow \infty$
2. For each $k = i-1, \ldots, j-1$:
    1. If $i > 1$: $sum \leftarrow len(i-1, k)$, $\underline{L} \leftarrow L_k$
    2. Else: $sum \leftarrow 0$, $\underline{L} \leftarrow -\infty$
    3. For each $q = 1, \ldots, Q$ with $\underline{L} < R_q \leq L_j$:
        1. If $\overline{R}_q \geq L_j$: $sum \leftarrow sum + (L_j - R_q) N_q$
        2. Else: $sum \leftarrow \infty$
    4. If $sum < minSum$: $minSum \leftarrow sum$, $minIndex \leftarrow k$
3. $len(i,j) \leftarrow minSum$, $ref(i,j) \leftarrow minIndex$
```

As before, the table is computed row by row and from left to right, up to row $PSUB$.
In that row, every cell with $len(PSUB, j) < \infty$ and $R_Q \leq L_j$ is a feasible solution (every piece of the stack is assigned a chosen length); the one with the least $len$ is the best.

(stack-program)=
#### Integer program for the stacks

The algorithm above is implemented (`StackAlgorithm`), but the app uses an integer program instead (`StackAlgorithmExact`), solved with the HiGHS solver through Pyomo.
In it, a length type of a stack is a pair of a length and a number of pieces: a 4 m bar and a 16 m bar made of a 12 m piece and a 4 m piece count as different types.

With the pieces $i$ of the stack, their shortest-piece lengths $LS_i$ and numbers of pieces $m_i$, and the lengths of the foundation $LO_j$:

* $x_{ij} \in \{0,1\}$: piece $i$ gets length $LO_j$;
* $z_{mj} \in \{0,1\}$: some piece made of $m$ pieces gets length $LO_j$;

$$
  \begin{align*}
  \min \quad & \sum_{i,j} (LO_j - LS_i)\, x_{ij} \\
  \text{s.t.} \quad & \sum_j x_{ij} = 1 && \text{for every piece } i \\
  & x_{ij} = 0 && \text{if } LS_i > LO_j \\
  & z_{m_i j} \geq x_{ij} && \text{for every } i, j \\
  & \sum_{m,j} z_{mj} \leq PSUB
  \end{align*}
$$

The solver stops within 10% of the optimum.
If there is no solution with $PSUB$ types, $PSUB$ is increased by one until there is; the stacks that needed more types than allowed are listed in the report as a warning (`excess_stack`).

```{warning}
The integer program doesn't use the upper bounds $\overline{R}_q$ of the pieces, so a piece can get a length longer than its upper bound.
```

Setting the practical periods
-----------------------------

The rounded or reduced length tells how long a piece must be, but not where it starts and ends.
The pieces of each stack are placed from the longest to the shortest; each piece is placed against the piece below it, its **base piece**, so the ends of the stack line up where possible (`Mesh._set_piece_practical`).

```{prf:algorithm} Adjusting the length of a piece
:label: length-adjustment

**Inputs** A piece with its required period, its new length, and its base piece (optional)

**Output** The practical period of the piece, with its new length

1. Piece without bends:
    1. Shorter: take the same amount off both ends.
    2. Longer, with a base piece:
        1. If the base piece has no bends: if the piece reaches one end of the base piece, align it with that end; otherwise add the same amount to both ends.
        2. If the base piece is bent at one end: try to align the piece with the unbent end of the base piece. If it would pass the side of the strip, try to reach the bent side and bend the piece there. If neither is possible, give the piece the length of the base piece and bend it.
        3. If the base piece is bent at both ends: as without a base piece.
    3. Longer, without a base piece: if adding to one end reaches the side of the strip, stop at the side and add the rest to the other end; otherwise add the same amount to both ends.
2. Piece bent at one end:
    1. Shorter: take it off the unbent end.
    2. Longer: add it to the unbent end, up to the side of the strip and the end of the base piece. If the base piece is bent at that end and the piece reaches it, bend the piece there too.
3. Piece bent at both ends:
    1. Shorter: take it off the end side.
    2. Longer: leave it as it is; this should not happen.
```

```{warning}
In case 1.2.2, a piece is bent only to keep the number of length types down.
This is an exception and should be checked on the drawing.
In case 3.2, the original design asks for a warning, but the code keeps the length silently.
```
