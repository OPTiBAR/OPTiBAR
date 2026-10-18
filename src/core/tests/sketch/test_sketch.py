import pytest
# the sketch (PDF drawing) module has not been brought over from the OPTiBAR/core repo yet
Sketch = pytest.importorskip("core.sketch.sketch").Sketch
import pathlib

class TestSketch():
    def test_draw(self, output):
        Sketch(pathlib.Path(__file__).parent.joinpath('plot'), output.get_output())