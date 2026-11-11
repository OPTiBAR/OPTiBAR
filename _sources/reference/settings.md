Settings
========

The settings on the left of the window, in the **Basic**, **Special Lengths** and **Strips** pages.
Hover the ⓘ next to a setting in the app for a short description.
**View > Dark Theme** switches the app to a dark theme.

## Type of Request

| Value | Meaning |
| --- | --- |
| Computation | Details the foundation once, with the settings below. |
| Analysis | Repeats the detailing for a range of Total and Stack, and compares the rebar mass of each combination. |

## Basic

| Setting | Meaning | Unit | Default | Values |
| --- | --- | --- | --- | --- |
| Diameter, Typical | Diameter of the typical rebars. | mm | 18 | 8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 32 |
| Diameter, Additional | Diameter of the additional rebars. | mm | 25 | as above |
| Diameter, Thermal | Diameter of the thermal rebars. | mm | 12 | as above |
| Diameter, Shear | Diameter of the shear rebars. | mm | 14 | as above |
| Typical Arrangement, Interval | Spacing of the typical rebars; a strip gets its width divided by the interval, rounded up. | cm | 20 | up to 100 |
| Cover, Side Cover | Distance from the side of the foundation to the ends of the longitudinal rebars. | cm | 5 | up to 20 |
| Elimination, Additional | Additional rebars with a theoretical length shorter than this are left out. | m | 0.2 | 0 to 2, in steps of 0.1 |
| Elimination, Shear | Parts of a strip that need shear rebars and are shorter than this get none. | m | 2 | 0 to 5, in steps of 0.5 |
| Number of Types, Total | Maximum number of different lengths of additional rebars in the whole foundation. | | 20 | 10 to 40 |
| Number of Types, Stack | Maximum number of different lengths of additional rebars in one stack. | | 2 | 1 to 5 |
| Number of Types, Shear | Maximum number of different shear rebar arrangements in the foundation. | | 4 | 1 to 5 |

For an **Analysis**, Total and Stack are ranges, **From** and **To**: Total from 10 to 20 by default, spanning at most 10; Stack from 2 to 4, spanning at most 2.

The covers of the top and bottom faces are read from the SAFE model.

## Special Lengths and Strips

| Setting | Meaning |
| --- | --- |
| Special Lengths | The development length (Ld, top and bottom), overlap length (top and bottom) and bend lengths (90° and 135°) of each bar diameter, in cm. Calculated from the materials of the SAFE model when the file is loaded, see [Special lengths](detailing-rules.md#special-lengths). |
| Special Lengths, Automatic | When checked, the top Ld and the overlaps follow from the bottom Ld. |
| Special Lengths, Reset | Restores the calculated values. |
| Strips | The number and diameter of the typical rebars of single strips and levels, instead of the interval. **Set** applies them, **Erase** removes them. |
