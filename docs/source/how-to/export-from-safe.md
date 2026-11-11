Export a model from SAFE
========================

OPTiBAR reads the Microsoft Access database (`.accdb` or `.mdb`) that SAFE exports.
This guide shows how to export it so that OPTiBAR finds everything it needs.

1. In SAFE, give every column load a **Load Size**. OPTiBAR finds the columns from the load sizes of the point loads; without them it doesn't know where the columns are.
2. Run the analysis and the design (**Run Analysis** and **Start Design**).
3. Choose **File > Export > Access .mdb/.accdb File**.
4. Select the table groups **Model Definition** and **Design Results**.
   To export less, select only the tables listed in [SAFE input](../reference/safe-input.md).
5. Press **OK** and choose a name and a folder for the file.

The units of the export don't matter; OPTiBAR converts them.

To check the file, load it in OPTiBAR: in **1. Input File**, press **Browse**, choose the file and press **Load**.
If a table is missing, the **Report** box names it; export again with that table selected.
The report also warns when the model uses more than one concrete or steel material.

```{note}
OPTiBAR is tested with files from SAFE 2016 (v16).
SAFE v20 and later export different tables, see [SAFE input](../reference/safe-input.md#safe-versions).
```
