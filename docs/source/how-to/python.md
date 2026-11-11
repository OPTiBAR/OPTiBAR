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

## Run an analysis

Give `type_number["total"]` and `type_number["stack"]` as ranges, for example `{"from": 10, "to": 20}`, and call `optibar.core.run.run_analysis` with the same arguments.
It returns one result per combination, or `{}` where a combination isn't feasible.

There is no command line interface yet.
