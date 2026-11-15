# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'OPTiBAR'
copyright = '2023, Sina Hajikazemi, Amir Salar'
author = 'Sina Hajikazemi, Amir Salar'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinxcontrib.mermaid",
    "sphinx_proof",
]

myst_enable_extensions = [
    "amsmath",
    "dollarmath",
]

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_title = 'OPTiBAR'
html_static_path = ['_static']
html_css_files = ['custom.css']
html_logo = "_static/logo.png"
html_theme_options = {
    "sidebar_hide_name": True, # the logo has the name
    # the orange of the logo, darkened in light mode so links keep a 4.5:1 contrast with the page
    "light_css_variables": {
        "color-brand-primary": "#b5480d",
        "color-brand-content": "#b5480d",
    },
    "dark_css_variables": {
        "color-brand-primary": "#f07a3a",
        "color-brand-content": "#f07a3a",
    },
}
