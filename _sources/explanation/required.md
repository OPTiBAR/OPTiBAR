Required Length
===================================

% TODO: Explain how the stacks are found using a figure.
% continue with the figure from theoretical length part.
% a single stack and two joint stacks.
% TODO: Explain how the additions are added using a figure and briefly explain the example how increasing the theoretical length could decrease the total added length.
% simply compare with and without increasing the theoretical length.

To turn the theoretical lengths of the pieces into lengths accepted by the code, they must be extended.
The rules are given below; then an optimization problem is defined that satisfies them while adding the least length to the theoretical lengths (`optimization/required.py`).

Stacks
------

A **stack** is a set of additional rebars placed on top of each other: from top to bottom, every piece lies within the next one, so the pieces go from short to long.
The station of the largest required steel within the top piece is the **base** of the stack.

Stacks are found from the rows of {prf:ref}`theoretical-piece` with the following algorithm (`PieceContainer.get_stacks`).
A piece can join more than one stack, so two stacks can share their lower pieces.

```{prf:algorithm} Finding the stacks of rebars
:label: stackify

**Inputs** $pieceContainer$: the rows of pieces, from top to bottom (short to long)

**Output** $stackList$: the stacks; each stack is a list of pieces from top to bottom (short to long)

1. $stackList \leftarrow []$
2. For each $pieceList \in pieceContainer$:
    1. For each $piece \in pieceList$:
        1. $added \leftarrow False$
        2. For each $stack \in stackList$:
            1. $child \leftarrow stack[-1]$
            2. If $child \subseteq piece$: $stack.append(piece)$, $added \leftarrow True$
        3. If $added = False$: $stackList.append([piece])$
```

Problem definition
------------------

On one side of the base of a stack (start or end), let $L_1, \ldots, L_n$ be the distances from the base to the theoretical ends of the pieces, from top to bottom, so $L_1 < \ldots < L_n$.
Each piece is extended according to two rules:

1. The bar runs past its theoretical end by at least the effective depth $d$.
2. The required end of every bar is at least $L_d$ past the theoretical end of the next shorter bar; for the shortest bar, at least $L_d$ past the base.

The rule that gives the longer bar **governs** the end of the bar; OPTiBAR records which one it is ($d$ or $L_d$), as it decides how a bar is treated at the side of the foundation, see [Bars at the sides of the strip](#bars-at-the-sides).

```{warning}
The code clauses for these rules are not documented yet.
For the first rule, see the warning in [Detailing Rules](../reference/detailing-rules.md#additional-rebars).
```

The second rule is based on the theoretical end of the shorter bar.
Suppose a stack has three bars of different lengths: bar 3 is extended from the end of bar 2, and bar 2 from the end of bar 1.
If bar 2 is given the length of bar 3, then both bars 2 and 3 are extended from the end of bar 1.
So giving some bars of a stack the same length can make the total length of the stack shorter.

Dynamic programming algorithm
-----------------------------

We choose the best subset of the lengths $1, \ldots, q$: every length that is not chosen is increased to the smallest chosen length above it, and the total length after applying the two rules is the least possible.
The best way to choose $p$ lengths out of $1, \ldots, q$ is built from the best ways to choose $p-1$ lengths out of $1, \ldots, q-1$, $1, \ldots, q-2$, …, $1, \ldots, p-1$.

$len(p,q)$ is the least total length of the bars $1, \ldots, q$ when $p$ lengths are chosen from them:

$$
  \text{len}(p,q) = \left\{
  \begin{array}{lr}
  \min_{i=p-1,\ldots,q-1}\left\{ \text{len}(p-1,i) + (q-i) \max\{L_i + L_d,\ L_q + d\}\right\}, & p>1 \\
  q \max\{L_d,\ L_q+d\}, & p=1
  \end{array}
  \right.
$$

If the minimum is reached at $\hat{i}$, the best way to choose $p$ lengths out of $1, \ldots, q$ is to choose $q$, and $p-1$ lengths out of $1, \ldots, \hat{i}$; the lengths $\hat{i}+1, \ldots, q-1$ are increased to $L_q$.
$ref(p,q)$ returns $\hat{i}$:

$$
  \text{ref}(p,q) = \left\{
  \begin{array}{lr}
  \text{arg}\,\min_{i=p-1,\ldots,q-1}\left\{ \text{len}(p-1,i) + (q-i) \max\{L_i + L_d,\ L_q + d\}\right\}, & p>1 \\
  \varnothing, & p=1
  \end{array}
  \right.
$$

A recursive function would compute the same values many times.
Instead, the values are computed in a table, row by row from the top, and in every row from left to right: $len(1,1), len(1,2), \ldots, len(1,n)$, then $len(2,2), \ldots, len(2,n)$, and so on.
The least value in the last column is the best solution; following $ref$ from there gives the chosen lengths.

```{list-table} Dynamic programming algorithm table

*   - $len(1,1)$
    - $len(1,2)$
    - $len(1,3)$
    - $\ldots$
    - $len(1,n-1)$
    - $len(1,n)$
*   - \-
    - $len(2,2)$
    - $len(2,3)$
    - $\ldots$
    - $len(2,n-1)$
    - $len(2,n)$
*   - \-
    - \-
    - $len(3,3)$
    - $\ldots$
    - $len(3,n-1)$
    - $len(3,n)$
*   - $\ldots$
    - $\ldots$
    - $\ldots$
    - $\ldots$
    - $\ldots$
    - $\ldots$
*   - \-
    - \-
    - \-
    - \-
    - $len(n-1,n-1)$
    - $len(n-1,n)$
*   - \-
    - \-
    - \-
    - \-
    - \-
    - $len(n,n)$
```

Example
-------

Let $L = [1, 1.5, 2]$, $d = 0.3$ and $L_d = 1.4$. Each cell of the table below holds the value of $len$ and the value of $ref$.

$$
  \begin{align}
  \text{len}(1,1) &= \max\{L_d, L_1 + d\} = \max\{1.4, 1 + 0.3\} = 1.4 \\
  \text{len}(1,2) &= 2 \times \max\{L_d, L_2 + d\} = 2 \times \max\{1.4, 1.5 + 0.3\} = 2 \times 1.8 = 3.6 \\
  \text{len}(1,3) &= 3 \times \max\{L_d, L_3 + d\} = 3 \times \max\{1.4, 2 + 0.3\} = 3 \times 2.3 = 6.9 \\
  \text{len}(2,2) &= \text{len}(1,1) + \max\{L_1+L_d , L_2 + d\} \\
  &= 1.4 + \max\{1+1.4, 1.5+0.3\} = 1.4 + 2.4 = 3.8 \\
  \text{len}(2,3) &= \min\{\text{len}(1,1) + 2 \times \max\{L_1+L_d, L_3+d\} , \text{len}(1,2) + \max\{L_2+L_d, L_3+d\}\} \\
  &= \min\{1.4 + 2 \times \max\{1+1.4, 2+0.3\} ,2 \times 1.8 + \max\{1.5+1.4,2+0.3\}\} \\
  &= \min\left\{1.4 + 2 \times 2.4 ,2 \times 1.8 + 2.9\right\} = 6.2 \\
  \text{len}(3,3) &= \text{len}(2,2)+\max\{L_2+L_d,L_3+d\} \\
  &= 1.4 + 2.4 + \max\{1.5+1.4, 2+0.3\} = 1.4 + 2.4 + 2.9 = 6.7
  \end{align}
$$

```{list-table} The table of the example

*   - $(1.4, \varnothing)$
    - $(3.6, \varnothing)$
    - $(6.9, \varnothing)$
*   - \-
    - $(3.8, 1)$
    - $(6.2, 1)$
*   - \-
    - \-
    - $(6.7, 2) $
```

The least value in the last column is $len(2,3) = 6.2$, with $ref(2,3) = 1$: bar 1 keeps its theoretical length, and bar 2 gets the theoretical length of bar 3.
Applying the two rules to these lengths gives a total length of 6.2, less than the 6.7 of extending every bar on its own, $len(3,3)$.

The extensions are found for the start and the end side of each stack separately.
A piece that belongs to two stacks gets the longer of the two required ends.

(bars-at-the-sides)=
Bars at the sides of the strip
------------------------------

The bars must stay within the strip, less the side cover on both ends.
Bars that pass the side are bent or cut (`Mesh._bend_stack_base`), with a bend of the length given in [Special Lengths](../reference/detailing-rules.md#special-lengths):

```{prf:algorithm} Bending the bars at the sides of the strip
:label: bend-pieces

**Inputs** The stacks of the strip, each from top to bottom, with their theoretical and required periods and the governing rule of each end

**Output** The bends and the corrected periods of the pieces

1. For each $stack$, and each $piece$ of it, from top to bottom, and each $side \in \{start, end\}$:
    1. If the theoretical $side$ of the piece passes the side of the strip: bend it; the theoretical and required $side$ are at the side of the strip plus the bend.
    2. Else, if the required $side$ passes the side of the strip:
        1. If $L_d$ governs that end, or the piece above it in the stack is bent on that side: bend it, and its required $side$ is at the side of the strip plus the bend.
        2. Else ($d$ governs): cut it at the side of the strip.
```

Merging bars of a row
---------------------

The required lengths of two neighbouring bars of a row can overlap.
Then one bar from the start of the first to the end of the second may be shorter than the two bars together, as an overlap is only needed every 12 m.
The bars of a row are merged where this lowers the total length, with the following algorithm (`Mesh._unify`).
The **net length** of a bar of length $L$ is $L$ itself up to 12 m, and $L$ plus its overlaps above, see [Practical Length](practical.md#bars-longer-than-12-m).

```{prf:algorithm} Merging bars that meet
:label: merge-pieces

**Inputs** The pieces $p_1, \ldots, p_n$ of a row, sorted by their start (and end)

**Output** The pieces of the row, merged with the least total net length

1. $subset \leftarrow []$
2. For each $i \in 1, \ldots, n$:
    1. $subset.append(p_i)$
    2. If $i = n$ or $p_i.end < p_{i+1}.start$ (the next piece doesn't meet $p_i$):
        1. $minPartitionValue \leftarrow \infty$, $minPartition \leftarrow None$
        2. For each partition $part$ of $subset$ into groups of consecutive pieces:
            1. $partSum \leftarrow$ the sum of the net lengths of the merged pieces of the groups of $part$
            2. If $partSum < minPartitionValue$: $minPartitionValue \leftarrow partSum$, $minPartition \leftarrow part$
        3. Replace the pieces of $subset$ by one merged piece for each group of $minPartition$
        4. $subset \leftarrow []$
```

When two pieces are not merged, the stacks they belong to are kept apart in the rows above too.
After merging, the required lengths are found again, and this repeats until no bars are merged.
