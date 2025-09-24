Theoretical Length
===================================
To obtain the theoretical lengths of components, it is necessary to first determine the cross-sectional steel area required along the length of the strip. Then, by reducing step by step, the required amount of steel, the length, and the location of the components are obtained.

Note that this algorithm is only applicable when all the components obtained in one stage of the algorithm have the same diameter.

According to the clause (this part should be completed) of the Iranian code and the clause (this part should be completed) of the American code, in regions where a concrete column is present, it is sufficient to satisfy the maximum required steel on each of the two faces of the column. Also, for steel columns, the mid-height is considered next to the base plate and on the column.

(Note: The placeholders (this part should be completed) indicate that specific information or details need to be filled in based on the actual content of the codes or regulations being referred to.)

There are three methods for placing general reinforcements, which are as follows:

- **Minimum (minRatio):** In this method, the minimum allowable reinforcement according to the code is placed in each strip.
  (:math:`area = minRatio * width * depth`)
- **Count (count):** If the reinforcement meets the minimum requirement, the desired number of reinforcements is placed. If the minimum reinforcement is not met, the minimum amount of reinforcement is placed.
- **Smart (smart):** The minimum reinforcement is placed. If the distance from the first station with zero steel demand to any of the edges is more than the pile depth, or if the distance between two consecutive zero-demand intermediate stations is more than twice the pile depth, the reinforcement placement is completed. Otherwise, another reinforcement is placed.


Remove all the follwowing algorithms.

decrease column sides
additional rebars
