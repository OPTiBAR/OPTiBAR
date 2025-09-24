Allowable Length
===================================

Explain how the stacks are found using a figure and remove the code.
continue with the figure from theoretical length part.
a single stack and two joint stacks.


Explain how the additions are added using a figure and briefly explain the example how increasing the theoretical length could decrease the total added length.
simply compare with and without increasing the theoretical length.

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

## Example

$$
  \begin{align}
  \text{len}(1,1) &= \max\{L_d, L_1 + d\} = \max\{1.4, 1 + 0.3\} = 1.4 \\
  \text{len}(1,2) &= 2 \times \max\{L_d, L_2 + d\} = \max\{1.4, 1.5 + 0.3\} = 2 \times 1.8 \\
  \text{len}(1,3) &= 3 \times \max\{L_d, L_3 + d\} = \max\{1.4, 2 + 0.3\} = 3 \times 2.3 = 6.9 \\
  \text{len}(2,2) &= \text{len}(1,1) + \max\{L_1+L_d , L_2 + d\} \\
  &= 1.4 + \max\{1+1.4, 1.5+0.3\} = 1.4 + 2.4 \\
  \text{len}(2,3) &= \min\{\text{len}(1,1) + 2 \times \max\{L_1+L_d, L_3+d\} , \text{len}(1,2) + \max\{L_2+L_d, L_3+d\}\} \\
  &= \min\{1.4 + 2 \times \max\{1+1.4, 2+0.3\} ,2 \times 1.8 + \max\{1.5+1.4,2+0.3\}\} \\
  &= \min\left\{1.4 + 2 \times 2.4 ,2 \times 1.8 + 2.9\right\} = 6.2 \\
  \text{len}(3,3) &= \text{len}(2,2)+\max\{L_2+L_d,L_3+d\} \\
  &= 1.4 + 2.4 + \max\{1.5+1.4, 2+0.3\} = 1.4 + 2.4 + 2.9 = 6.7
  \end{align}
$$

```{list-table} Dynamic programming algorithm table

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
