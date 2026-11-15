"""Render the DXF figures of the docs as SVG, from the sample foundation.

Runs the calculation of the tutorial on tonf_m.accdb, writes the DXF, and renders parts of it
on a white background into docs/source/_static/images:

- dxf_plan.svg: the sheet of the top additional rebars of the X direction
- dxf_sections.svg: the sections of the shear types
- dxf_tables.svg: the tables
- dxf_cutting.svg: the first cutting plan sheet of the 25 mm bars

Everything is black, which reads better on white and is what a monochrome plot style prints, except the
colors the docs explain: the blue and magenta additional rebars of the plan.

From the repository root (needs the Access ODBC driver, like the app):

    uv run python docs/figures/render_dxf.py
"""
import tempfile
from pathlib import Path
from typing import Sequence

import ezdxf
from ezdxf import bbox
from ezdxf.addons.drawing import Frontend, RenderContext, layout, svg
from ezdxf.addons.drawing.config import BackgroundPolicy, ColorPolicy, Configuration
from ezdxf.math import BoundingBox2d

from optibar.core.parser.parse import V16Parser
from optibar.core.run import run_calculation
from optibar.core.sketch.dxf import TOP_ADDITIONAL_X, DxfDrawing, Layout

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "src/optibar/core/tests/parser/data_files/tonf_m.accdb"
IMAGES = ROOT / "docs/source/_static/images"

CONFIG = {
    "diameter": {"typical": 18, "additional": 25, "thermal": 12, "shear": 14},
    "typical_arrangement": {"method": "INTERVAL", "value": 0.2},
    "side_cover": 0.05,
    "elimination": {"additional": 0.2, "shear": 2.0},
    "type_number": {"total": 20, "stack": 2, "shear": 4},
}

# the layers whose colors the docs explain: blue bars are separate stacks, magenta ones are spliced
REBAR_LAYERS = ("Additional Rebar Top", "Additional Rebar Bottom", "continuous Rebar")

# width of the SVGs in px; the height follows the region
PAGE_WIDTH = 900


def render(doc, box: BoundingBox2d, name: str, width: float = PAGE_WIDTH, colored: Sequence[str] = ()) -> None:
    """render the entities inside a box of model space to an SVG, black on white except the layers in colored,
    which keep their colors (every entity takes its color from its layer)"""
    msp = doc.modelspace()
    colors = {layer.dxf.name: layer.dxf.color for layer in doc.layers}
    for layer in doc.layers:
        if layer.dxf.name not in colored:
            layer.dxf.color = 7 # black on a white background
    cache = bbox.Cache()
    inside = set()
    for entity in msp:
        extents = bbox.extents([entity], cache=cache)
        if extents.has_data and box.has_intersection(BoundingBox2d([extents.extmin, extents.extmax])):
            inside.add(entity.dxf.handle)
    # draw_layout, not draw_entities: only draw_layout applies the background policy
    config = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.COLOR)
    backend = svg.SVGBackend()
    frontend = Frontend(RenderContext(doc), backend, config=config, bbox_cache=cache)
    frontend.draw_layout(msp, filter_func=lambda entity: entity.dxf.handle in inside)
    for layer in doc.layers:
        layer.dxf.color = colors[layer.dxf.name]
    size = box.size
    page = layout.Page(width, width * size.y / size.x, layout.Units.px)
    settings = layout.Settings(fit_page=True, min_stroke_width=0.05, max_stroke_width=0.002)
    text = backend.get_string(page, settings=settings, render_box=box, xml_declaration=False)
    (IMAGES / name).write_text(text, encoding="utf-8")
    print("wrote", IMAGES / name)


def region(doc, x0: float, y0: float, x1: float, y1: float, margin: float) -> BoundingBox2d:
    """extents of the entities inside a rough box, with a margin"""
    rough = BoundingBox2d([(x0, y0), (x1, y1)])
    found = BoundingBox2d()
    for entity in doc.modelspace():
        extents = bbox.extents([entity])
        if not extents.has_data:
            continue
        box = BoundingBox2d([extents.extmin, extents.extmax])
        if rough.inside(box.extmin) and rough.inside(box.extmax):
            found.extend([box.extmin, box.extmax])
    return BoundingBox2d([found.extmin - (margin, margin), found.extmax + (margin, margin)])


def main() -> None:
    parser = V16Parser(str(SAMPLE))
    foundation = parser.get_foundation()
    parser.close()
    output = run_calculation(foundation, CONFIG)
    data = output["data"]

    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "sample.dxf"
        DxfDrawing(data).save(path)
        doc = ezdxf.readfile(path)

    L = Layout(data["areas"])
    W, H = L.WIDTH, L.HEIGHT

    # a plan sheet, inside its border
    inset = H / 21 * 0.8
    x0 = TOP_ADDITIONAL_X * W
    render(doc, region(doc, x0 + inset, inset, x0 + W - inset, H - inset, 0.03 * H), "dxf_plan.svg", 800, colored=REBAR_LAYERS)

    # the shear sections, right of the last plan sheet, and the tables, up to the strip names of the moment diagrams
    lx, _ = L.list_base()
    mx, _ = L.moment_base()
    render(doc, region(doc, 9 * W + 0.01, -H, lx - 5, 2 * H, 0.03 * H), "dxf_sections.svg", 700)
    render(doc, region(doc, lx - 5, -H, mx - 10, 2 * H, 0.5), "dxf_tables.svg", 1400)

    # the cutting plans are portrait sheets in a row below the plans; take the first of the 25 mm bars
    sheet = 0
    for plan in data["cut"]:
        if plan["diameter"] == 25:
            break
        sheet += max(1, -(-len(plan["patterns"]) // 15))
    w = W / 2
    left, top = 1.5 * sheet * w, -H / 2
    render(doc, BoundingBox2d([(left - 0.02 * H, top - H - 0.02 * H), (left + w + 0.02 * H, top + 0.08 * H)]), "dxf_cutting.svg", 700)


if __name__ == "__main__":
    main()
