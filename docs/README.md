## Documentation

The documentation is built with Sphinx and published on [Read the Docs](https://optibar.readthedocs.io/).
A GitHub workflow also builds it and deploys it to the `gh-pages` branch on every push to `main`.

To build it locally, from the repository root:

```console
> uv run --no-project --with-requirements docs/requirements.txt sphinx-build -b html docs/source docs/build/html
```

or with a virtual environment:

```console
> pip install -r docs/requirements.txt
> docs\make html
```

The pages are in `docs/source`, organized by [Diátaxis](https://diataxis.fr/):

- `tutorials`: lessons for new users, step by step.
- `how-to`: steps for specific tasks.
- `reference`: settings, SAFE input, outputs and detailing rules, to look up.
- `explanation`: how and why the rebar lengths are calculated.

Images go in `docs/source/_static/images`.
