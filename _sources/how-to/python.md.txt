Use OPTiBAR from Python
=======================

The engine can be used without the app, for example to detail many foundations in a script.

## Run a computation

Parse the SAFE file, run the calculation, and write the drawings:

```python
from optibar.core.parser.parse import V16Parser
from optibar.core.run import run_calculation
from optibar.core.sketch.dxf import DxfDrawing
from optibar.core.sketch.sketch import Sketch

parser = V16Parser("foundation.accdb")
foundation = parser.get_foundation()
parser.close()

config = {
    "diameter": {"typical": 18, "additional": 25, "thermal": 12, "shear": 14},  # mm
    "typical_arrangement": {"method": "INTERVAL", "value": 0.2},               # m
    "side_cover": 0.05,                                                          # m
    "elimination": {"additional": 0.2, "shear": 2.0},                           # m
    "type_number": {"total": 20, "stack": 2, "shear": 4},
}
output = run_calculation(foundation, config)

if "errors" in output:
    print("not feasible:", output["errors"])
else:
    DxfDrawing(output["data"]).save("foundation.dxf")
    Sketch(output["data"]).save("foundation.pdf")
```

The settings are those of the app, in meters; see [Settings](../reference/settings.md).
The output has the structure of the `result` key of the results file, see [Outputs](../reference/outputs.md#results-file).

## Read the tables from somewhere else

`V16Parser` takes the path of an Access file, or a table source that returns SAFE's tables.
`MemorySource` holds tables already in memory, for example tables read from another export: a dict from the table name, as SAFE writes it, to a list of rows, each a dict from the column name to the value.
The tables and columns are those of [SAFE input](../reference/safe-input.md), with values in the units of `Program Control`:

```python
from optibar.core.parser.parse import V16Parser, MemorySource

tables = {
    "Program Control": [{"CurrUnits": "Tonf, m, C"}],
    "Grid Lines": [{"AxisDir": "X", "GridID": "A", "Ordinate": 0.0}, ...],
    ...
}
foundation = V16Parser(MemorySource(tables)).get_foundation()
```

A missing table or column raises `TableMissingError`, as it does for an Access file.

## Export the results as tables

`optibar.core.export.export` writes the tables of [Exported tables](../reference/outputs.md#exported-tables) in the format of the file extension: `.xlsx`, `.zip` (CSV files) or `.json`.
It takes the result as the results file holds it:

```python
from optibar.core.export import export

saved = {"calc_type": "calculation", "config": config, "result": output, "input_file": "foundation.accdb"}
export(saved, "foundation.xlsx")
```

`optibar.core.export.prepare` returns the tables themselves, to use them in Python. A results file saved by the app can be exported the same way, after reading it with `json.load`.

## Run an analysis

Give `type_number["total"]` and `type_number["stack"]` as ranges, for example `{"from": 10, "to": 20}`, and call `optibar.core.run.run_analysis` with the same arguments.
It returns one result per combination, or `{}` where a combination isn't feasible.

There is no command line interface yet.
