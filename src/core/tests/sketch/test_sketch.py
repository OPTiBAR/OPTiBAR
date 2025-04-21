from optibar.src.sketch.sketch import Sketch
import pathlib

class TestSketch():
    def test_draw(self, output):
        Sketch(pathlib.Path(__file__).parent.joinpath('plot'), output.get_output())