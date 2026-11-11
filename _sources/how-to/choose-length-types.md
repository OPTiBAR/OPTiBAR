Choose the number of length types
=================================

The **Number of Types** settings, **Total** and **Stack**, set how many different lengths of additional rebars the drawing may use.
Fewer lengths make the foundation easier to build but use more steel; see [Why the number of length types matters](../explanation/intro.md#length-types).

## Start from typical values

Good starting values are 2 to 4 for **Stack** and 10 to 30 for **Total**.
Use smaller numbers for small foundations and for sites that need a simple drawing, larger ones for large foundations.

## Compare the options with an analysis

An analysis runs the detailing for every combination in a range of **Total** and **Stack**, and compares the rebar mass.

1. Open the foundation with **Open…**.
2. In the settings on the left, set **Type of Request** to **Analysis**.
3. Under **Number of Types**, set the range of **Total**, for example 10 to 20, and of **Stack**, for example 2 to 4.
   A range can span at most 10 for Total and 2 for Stack.
4. Set the other settings as for the final computation, and press **Calculate**.
   The status line shows the progress; an analysis takes longer than a single computation.
5. Above the report, press **Diagram**, and choose **Total** to plot the mass of all the rebars, or **Additional** for the additional rebars only.

![Mass of the additional rebars of a foundation, for stack 3 and 4 and total 6 to 29](../_static/images/analysis_plot.png)

The plot has one curve per Stack number.
Look for the point where the curve gets steep: below it, every length type you remove costs a lot of steel.

6. Set **Type of Request** back to **Computation**, enter the chosen numbers, and press **Calculate**.

## If the numbers are not feasible

When **Total** is too small for the foundation, the calculation stops and the report gives the smallest number that works.
When **Stack** is too small for some stacks, OPTiBAR uses more types there and lists those strips as a warning.
