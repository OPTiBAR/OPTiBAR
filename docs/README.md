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

Images go in `docs/source/_static/images`, as SVG with a white background, except the screenshots of the app (PNG).
The renders of the DXF drawing and the analysis plot are made from the sample foundation by the scripts in
`docs/figures`; rerun them after a change to the drawing or the engine (they need the app and the Access ODBC driver):

```console
> uv run python docs/figures/render_dxf.py
> uv run python docs/figures/analysis_plot.py
```

The other diagrams are drawn by hand in SVG.

## Translations

The docs are written in English only. Every other language is a set of translated strings, kept in the repository and
built into its own site: English at the root, Persian at `fa/`, and so on. The language menu under the search box (a
dropdown, with room for any number of languages) links to the same page in every language. Untranslated or outdated strings show in English, so a translation can be partial.

The algorithms, the diagrams and the math are never translated: `update` leaves them out of the catalogs (algorithm
blocks, Mermaid diagrams, display math and math environments, and strings that are only a formula, a code name or a
number), and on right-to-left pages they stay left to right. A sentence with a formula in it is translated, and
`check` makes sure the formula comes through unchanged.

Every page of a translation starts with a banner, in that language, saying that the translation is AI generated and
that only the English version is checked (`TRANSLATION_NOTICES` in `docs/source/conf.py`). A translated language
without a notice fails the build.

Each language has, in `docs/source/locale/<language>/`:

- `LC_MESSAGES/*.po`: the translated strings, one catalog per folder of the docs.
- `glossary.yml`: the equivalents to use for the terms of OPTiBAR (for example, *required length*), with hints for the
  translator, and the names that stay as they are (OPTiBAR, SAFE, DXF, ...). Every translation follows it.

`docs/i18n.py` keeps the translations in sync with the English text. From the repository root:

```console
> uv run --group docs python docs/i18n.py update               # after the English text changed
> uv run --group docs python docs/i18n.py pending fa --out fa.json   # the strings to translate, with the glossary
> uv run --group docs python docs/i18n.py apply fa fa.json     # write the translated strings back
> uv run --group docs python docs/i18n.py check fa             # what is left, the glossary, kept names and markup
```

After the English text changes, `update` adds the new strings empty and marks the changed ones as changed (their old
translation is kept as a starting point). `pending` lists them, with the glossary, in a JSON file to translate; `apply`
writes the translations back. `check` reports what is left to translate and every translation that doesn't use the
glossary's term, drops a kept name, or changes the markup (links, inline code, math). Broken markup breaks the build,
so `check` exits with an error for it.

To build a translation locally, for example Persian:

```console
> uv run --only-group docs sphinx-build -b html -D language=fa docs/source docs/build/html/fa
```

To add a language, add it to `LANGUAGES` in `docs/source/conf.py` (and to `RTL_LANGUAGES` if it is written right to
left), add its notice to `TRANSLATION_NOTICES`, create `docs/source/locale/<language>/LC_MESSAGES/` and a `glossary.yml`, and run `update`. The docs workflow
builds every language in `docs/source/locale`, and the menu lists only those, so a language in `LANGUAGES` without
catalogs never gets a broken link.

Right-to-left languages get `rtl.js` and `rtl.css` (Furo has no right-to-left support): the page is laid out right to
left, with a Persian font, while code and formulas stay left to right.
