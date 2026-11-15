"""exports the PNG logos of the app from the SVG logos of this folder.

The app can't show SVG (Tk and Pillow don't read it), so it has PNG copies, made by this script:

    uv run --with pymupdf python assets/export_png.py

- src/optibar/gui/data/images/logo.png: the window icon, the bars of logo-mark.svg, 256 x 256
- src/optibar/gui/data/images/optibar.png: the About dialog, logo.svg on a 615 x 511 canvas

Run it after changing logo-mark.svg or logo.svg, and commit the PNGs with the SVGs.
"""
import io
from pathlib import Path

import pymupdf
from PIL import Image

ASSETS = Path(__file__).resolve().parent
IMAGES = ASSETS.parent / 'src' / 'optibar' / 'gui' / 'data' / 'images'


def render(svg: Path, width: int) -> Image.Image:
    """the SVG drawn at the given width, with a transparent background"""
    page = pymupdf.open(svg)[0]
    zoom = width / page.rect.width
    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=True)
    return Image.open(io.BytesIO(pixmap.tobytes('png'))).convert('RGBA')


def on_canvas(image: Image.Image, size: tuple[int, int], fill: float) -> Image.Image:
    """the image centered on a transparent canvas, taking the given share of its width or height"""
    scale = min(size[0] * fill / image.width, size[1] * fill / image.height)
    image = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    canvas = Image.new('RGBA', size, (0, 0, 0, 0))
    canvas.alpha_composite(image, ((size[0] - image.width) // 2, (size[1] - image.height) // 2))
    return canvas


def main() -> None:
    # drawn larger than needed, then scaled down: smoother edges
    on_canvas(render(ASSETS / 'logo-mark.svg', 1024), (256, 256), 0.96).save(IMAGES / 'logo.png', optimize=True)
    on_canvas(render(ASSETS / 'logo.svg', 1600), (615, 511), 0.65).save(IMAGES / 'optibar.png', optimize=True)
    for name in ('logo.png', 'optibar.png'):
        print(f'written {IMAGES / name}')


if __name__ == '__main__':
    main()
