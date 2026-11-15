# Assets

The logo of OPTiBAR, in one place. Everything else uses these files: the README, the docs (through
`html_static_path` in `docs/source/conf.py`) and, as PNG copies, the app.

| File | Content |
| --- | --- |
| `logo.svg` | The logo: the bars and the name. |
| `logo-dark.svg` | The logo for dark backgrounds: light gray bars and name, the same orange. |
| `logo-mark.svg` | The bars only, for the app icon. |

The SVGs are the master copies: change the logo in them. They were made from the original Photoshop
file (not in the repository): the bars traced from its layers, with cylinder tops, and the name drawn
with the outlines of [Josefin Sans](https://fonts.google.com/specimen/Josefin+Sans) Bold, under the
SIL Open Font License.

The app can't show SVG, so it has PNG copies in `src/optibar/gui/data/images/` (`logo.png`, the window
icon, and `optibar.png`, the About dialog). After changing an SVG, export them again:

```console
> uv run --with pymupdf python assets/export_png.py
```
