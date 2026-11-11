Basic Concepts
===================================

In this chapter, the problem is defined, and its inputs and outputs are specified. Then, the main algorithm for solving it is presented, and its constituent parts are generally described.

The input to this problem is the required cross-sectional steel area in stations along a design strip.
These values are provided for all design strips and upper and lower meshs.
This input can be extracted from the output of analytical software such as *CSI SAFE*.
In addition to this, the required cross-sectional area of shear reinforcement in these sections is also observable in the output of some design software.
The input values are more precisely described in the following list:

* Material types for rebar and concrete
* Design strips

  * Depth
  * Coordinates of stations
  * Coordinates of columns
  * Shear punch for each column (!)
  * Cross-sectional steel area in the upper network
  * Cross-sectional steel area in the lower network
  * Shear steel cross-sectional area (!)

Items marked with (!) may not be available in the output of some *CSI SAFE* software versions.

By using the steel quantity at each station, the length of each rebar can be calculated. These lengths are referred to as the **theoretical** lengths of the components.

Bars that only cover the required steel of the input are too short: according to ACI 318, they must be extended to satisfy the code requirements.
The extended lengths are the **required** lengths of the rebars, see [Detailing Rules](../reference/detailing-rules.md#additional-rebars).
A map drawn based on required lengths is hard to build for three reasons:

* The non-roundness of the lengths makes it difficult for workers to cut and locate, and for supervisors to check, for example, a rebar with a length of 3.77 m. The designer may prefer a length of 3.80 m or 4.00 m.
* There may be too many different lengths used throughout the foundation. This complicates the maps and the rebar cutting process.
* The abundance of lengths used side by side in a section of the strip. This complicates map reading and execution for the contractor and makes it difficult for the supervisor to check.

To solve this problem, it is possible to reduce the number of lengths by increasing the length of a set of components.
The lengths obtained after this stage are called **practical** lengths.

In the following chapters, each of these stages will be examined.

```{mermaid}
    ---
    title: Main stages of the algorithm
    ---
    flowchart LR
        id1(Parse the Analysis software output) --> id2(Theoretical Length) --> id3(Required Length) --> id4(Calculate <br>Practical Length)
```

(length-types)=
Why the number of length types matters
--------------------------------------

SAFE gives the required steel area as a continuous diagram along each strip.
Covering it with bars, layer by layer, gives a bar of a different length for every layer:

![The required steel area along a strip (blue) and the bars that cover it](../_static/images/steel_area_diagram.png)

Done for every strip, this gives tens or hundreds of different lengths in one foundation.
A drawing like the one below is correct, but it is impractical to cut, place and check:

![Additional rebars of a strip without unified lengths: every bar has its own length](../_static/images/lengths_not_unified.png)

OPTiBAR takes two limits from the user:

* **Stack**: the maximum number of different lengths in one stack of bars.
* **Total**: the maximum number of different lengths of additional rebars in the whole foundation.

Within these limits, it chooses the lengths that add the least steel. The same strip, with at most 4 lengths in a stack:

![The same strip with at most 4 lengths per stack](../_static/images/lengths_stack_4.png)

Larger limits save steel but make the foundation harder to build; [an analysis](../how-to/choose-length-types.md) shows the trade-off for a project.

Trying every choice is not possible.
To keep 25 lengths out of 50, there are $\binom{50}{25} \approx 1.3 \times 10^{14}$ choices; at one second each, checking them all would take about 4 million years.
OPTiBAR uses dynamic programming instead, see [Required Length](required.md) and [Practical Length](practical.md).

Notations
-----------

* $L_d$: Development length of the bar.
* $d$: Effective depth of the foundation.
* $b$: Width of the foundation.
* $As$: Area of steel in the section.
* $\epsilon_t$: Total strain.
* $\epsilon_{ty}$: Yield strain.
