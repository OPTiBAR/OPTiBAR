SAFE input
==========

OPTiBAR reads the Microsoft Access database (`.accdb` or `.mdb`) exported by CSI SAFE, through the Microsoft Access ODBC driver.
The units of the file are converted when it is read.

## Tables

| Table | What OPTiBAR reads |
| --- | --- |
| Program Control | The units of the file. |
| Grid Lines | The grid lines, for the drawing. |
| Concrete Slab Design 01 - Flexural And Shear Data | The required top and bottom steel, the shear steel, the factored moments and the width at every station of every strip. |
| Object Geometry - Design Strips | The geometry and widths of the strips. |
| Material Properties 03 - Concrete | $f'_c$ of the concrete. |
| Material Properties 04 - Rebar | $f_y$ of the rebars. |
| Slab Design Overwrites 01 - Strip Based | The rebar material and cover overwrites of the strips. |
| Design Preferences 02 - Rebar Cover - Slabs | The top and bottom covers, where a strip doesn't overwrite them. |
| Slab Properties 02 - Solid Slabs | The thickness and material of the slabs. |
| Slab Property Assignments | Which slab property each area has. |
| Object Geometry - Point Coordinates | The coordinates of the points. |
| Load Assignments - Point Loads | The columns: point loads with a load size larger than 5 cm in both directions. |
| Object Geometry - Areas 01 - General | The outline and openings of the foundation; wall areas are skipped. |

When the export doesn't contain a table, loading the file fails and the report names what is missing.
When the model uses more than one concrete or steel material, the report warns about it.

(safe-versions)=
## SAFE versions

OPTiBAR is tested with files exported by **SAFE 2016** (v16.0.2); the parser is `V16Parser`.

SAFE v20 and later (v20, v21, v22, v23) are built on a new platform, and the exported tables have different names: for example, the strip design results are in "Concrete Slab Design Summary - Flexure and Shear Data".
These files are not supported yet.
