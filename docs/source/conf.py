# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import gettext
from pathlib import Path

from sphinx import locale as sphinx_locale

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
html_static_path = ['_static', '../../assets/logo.svg', '../../assets/logo-dark.svg'] # the logos: one copy, in assets/
html_css_files = ['custom.css']
html_theme_options = {
    # the logos of assets/ (see assets/README.md), the dark one for dark mode
    "light_logo": "logo.svg",
    "dark_logo": "logo-dark.svg",
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
html_sidebars = {
    "**": [
        "sidebar/brand.html",
        "sidebar/search.html",
        "sidebar/languages.html", # the language menu, see below
        "sidebar/scroll-start.html",
        "sidebar/navigation.html",
        "sidebar/ethical-ads.html",
        "sidebar/scroll-end.html",
        "sidebar/variant-selector.html",
    ]
}


# -- Translations ------------------------------------------------------------
# The docs are written in English. The translations are gettext catalogs in locale/<language>/,
# kept up to date with docs/i18n.py (see docs/README.md); untranslated text stays English. Every
# language is built as its own site: English at the root, the others in a folder named after them.

locale_dirs = ['locale/']
LANGUAGES = [('en', 'English'), ('fa', 'فارسی')] # (code, name in that language), English first
RTL_LANGUAGES = {'fa', 'ar', 'he', 'ur'}
ENGLISH_DOCS = 'https://optibar.github.io/OPTiBAR/'

# the banner at the top of every page of a translation, in its language: every translated language needs one
TRANSLATION_NOTICES = {
    'fa': 'این ترجمه با هوش مصنوعی تهیه شده و بازبینی نشده است. تنها '
          f'<a href="{ENGLISH_DOCS}">نسخهٔ انگلیسی</a> بررسی شده است و در صورت تفاوت، آن نسخه معتبر است.',
}


def _link_prefix(target: str, current: str) -> str:
    """the path from the root of the current language's site to the root of the target's"""
    up = '' if current == 'en' else '../'
    return up + ('' if target == 'en' else target + '/')


def setup(app):
    # the language is known only after the command line overrides (-D language=fa) are applied
    def configure_language(app):
        current = app.config.language or 'en'
        # only the languages that are built: English, and those with catalogs in locale/
        locale = Path(app.confdir) / 'locale'
        built = [(code, name) for code, name in LANGUAGES if code == 'en' or (locale / code / 'LC_MESSAGES').is_dir()]
        app.config.html_context['languages'] = [
            {'code': code, 'name': name, 'prefix': _link_prefix(code, current), 'current': code == current}
            for code, name in built
        ]
        if current != 'en':
            # the algorithms stay English (docs/i18n.py leaves them out of the catalogs): so do their
            # labels, which sphinx-proof would translate with its own catalog ("Algorithm 7")
            sphinx_locale.translators[('general', 'proof')] = gettext.NullTranslations()
            if current not in TRANSLATION_NOTICES:
                raise ValueError(f'add a notice for the {current!r} translation to TRANSLATION_NOTICES in conf.py')
            app.config.html_theme_options['announcement'] = TRANSLATION_NOTICES[current]
        if current in RTL_LANGUAGES:
            app.add_js_file('rtl.js')
            app.add_css_file('rtl.css')
    app.connect('builder-inited', configure_language)
