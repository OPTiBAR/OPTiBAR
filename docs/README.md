## Documentation

The documentation is built with Sphinx and published on GitHub Pages at <https://optibar.github.io/OPTiBAR/>.
The GitHub workflow `.github/workflows/docs.yml` builds it and deploys it to the `gh-pages` branch on every push to `main`.

The docs dependencies are the `docs` group in `pyproject.toml`, locked in `uv.lock` with the rest of the project.
To build the docs locally, from the repository root:

```console
> uv run --only-group docs sphinx-build -b html docs/source docs/build/html
```

`--only-group docs` installs Sphinx and its extensions without the app and its dependencies, which the docs don't need.
Open `docs/build/html/index.html` to read the result.

To add a Sphinx extension, add it to the group with `uv add --group docs <package>`, and to `extensions` in `docs/source/conf.py`.

The pages are in `docs/source`, organized by [Diátaxis](https://diataxis.fr/):

- `tutorials`: lessons for new users, step by step.
- `how-to`: steps for specific tasks.
- `reference`: settings, SAFE input, outputs and detailing rules, to look up.
- `explanation`: how and why the rebar lengths are calculated.

Images go in `docs/source/_static/images`.
