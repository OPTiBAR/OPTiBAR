"""keeps the translations of the docs in sync with the English text.

The docs are written in English. Every other language has gettext catalogs in
docs/source/locale/<language>/LC_MESSAGES/ (one .po file per folder of the docs) and a glossary,
docs/source/locale/<language>/glossary.yml, with the equivalents to use for the terms of OPTiBAR.

    uv run --group docs python docs/i18n.py update            # after the English text changed
    uv run --group docs python docs/i18n.py pending fa        # the strings to translate, as JSON
    uv run --group docs python docs/i18n.py apply fa FILE     # write translated strings back
    uv run --group docs python docs/i18n.py check fa          # glossary, kept words and markup

update extracts the English text and merges it into every catalog: a new string is added empty, a
changed one is marked fuzzy with its old translation kept as a starting point, and a removed one is
dropped. Sphinx shows untranslated and fuzzy strings in English, so a language never shows a stale
translation.

Some text always stays English, so update leaves it out of the catalogs: the algorithm blocks, the
diagrams and the math (display math, math environments, and strings that are only a formula). A
sentence with a formula in it is translated, with the formula unchanged.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml
from babel.messages.catalog import Catalog
from babel.messages.pofile import read_po, write_po

DOCS = Path(__file__).resolve().parent
SOURCE = DOCS / 'source'
LOCALE = SOURCE / 'locale'
TEMPLATES = DOCS / 'build' / 'gettext'

# markup that must come through a translation unchanged: roles and links, inline code, math, bold
MARKUP = [
    re.compile(r':[a-z]+(?::[a-z]+)?:`[^`]+`'), # :doc:`...`, :prf:ref:`...`
    re.compile(r'(?<![:`])`[^`]+`(?!`)'),       # `inline code` (not the target of a role)
    re.compile(r'\$[^$]+\$'),                   # $math$
    re.compile(r'\]\([^)]+\)'),                 # the target of a [link](target)
]

# blocks that stay English: algorithms, diagrams and math, as fenced directives of the Markdown pages
ENGLISH_FENCE = re.compile(r'^\s*(`{3,}|~{3,})\{(prf:algorithm|mermaid|math)\}')
DISPLAY_MATH = re.compile(r'\$\$.*?\$\$', re.DOTALL)
ENVIRONMENT = re.compile(r'^\s*\\begin\{([a-z*]+)\}')


def english_lines() -> set[tuple[str, int]]:
    """the (page, line) of every line of the Markdown pages inside a block that stays English"""
    found = set()
    for page in SOURCE.rglob('*.md'):
        name = page.relative_to(SOURCE).as_posix()
        lines = page.read_text(encoding='utf-8').splitlines()
        end = None # what closes the current block
        start = 0
        for number, line in enumerate(lines, start=1):
            text = line.strip()
            if end is None:
                if m := ENGLISH_FENCE.match(line):
                    end = re.compile(rf'{re.escape(m.group(1)[0])}{{{len(m.group(1))},}}')
                elif text == '$$' or (text.startswith('$$') and not (len(text) > 2 and text.endswith('$$'))):
                    end = re.compile(r'.*\$\$')
                elif text.startswith('$$'): # $$ ... $$ on one line
                    found.add((name, number))
                    continue
                elif m := ENVIRONMENT.match(line):
                    end = re.compile(rf'.*\\end\{{{re.escape(m.group(1))}\}}')
                if end is not None:
                    start = number
            elif end.fullmatch(text) or (end.pattern.startswith('.*') and end.match(text)):
                found.update((name, k) for k in range(start, number + 1))
                end = None
    return found


def prose(text: str) -> str:
    """the text without its formulas, code and link targets, which are not translated"""
    text = DISPLAY_MATH.sub('', text)
    for pattern in MARKUP:
        text = pattern.sub('', text)
    return text


def nothing_to_translate(text: str) -> bool:
    """whether a string has no words once its formulas, code and link targets are taken out"""
    return not re.search(r'[^\W\d_]', prose(text)) # no letter left


def stays_english(message, english: set[tuple[str, int]]) -> bool:
    if nothing_to_translate(message.id):
        return True
    places = [(path.split('source/', 1)[-1], line) for path, line in message.locations]
    return bool(places) and all(place in english for place in places)


def languages() -> list[str]:
    return sorted(p.name for p in LOCALE.iterdir() if (p / 'LC_MESSAGES').is_dir())


def load(path: Path) -> Catalog:
    with path.open('rb') as f:
        return read_po(f)


def save(catalog: Catalog, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('wb') as f:
        write_po(f, catalog, width=0, omit_header=False, ignore_obsolete=True)


def catalogs(language: str) -> dict[str, tuple[Path, Catalog]]:
    folder = LOCALE / language / 'LC_MESSAGES'
    return {p.stem: (p, load(p)) for p in sorted(folder.glob('*.po'))}


def messages(catalog: Catalog):
    return (m for m in catalog if m.id)


def status(catalog: Catalog) -> tuple[int, int, int]:
    """(translated, fuzzy, untranslated)"""
    translated = fuzzy = untranslated = 0
    for m in messages(catalog):
        if not m.string:
            untranslated += 1
        elif m.fuzzy:
            fuzzy += 1
        else:
            translated += 1
    return translated, fuzzy, untranslated


def glossary(language: str) -> dict:
    path = LOCALE / language / 'glossary.yml'
    if not path.exists():
        return {'terms': {}, 'keep': []}
    data = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    terms = {}
    for term, value in (data.get('terms') or {}).items():
        if isinstance(value, dict):
            forms = value.get('use')
            note = value.get('note')
        else:
            forms, note = value, None
        forms = [forms] if isinstance(forms, str) else list(forms)
        terms[term] = {'use': forms, 'note': note}
    return {'terms': terms, 'keep': list(data.get('keep') or [])}


def update(_args) -> None:
    subprocess.run(
        [sys.executable, '-m', 'sphinx', '-q', '-b', 'gettext', str(SOURCE), str(TEMPLATES)],
        check=True)
    english = english_lines()
    templates = {}
    for pot in sorted(TEMPLATES.glob('*.pot')):
        template = load(pot)
        kept_english = [m.id for m in messages(template) if stays_english(m, english)]
        for msgid in kept_english:
            del template[msgid]
        templates[pot.stem] = template
        print(f'{pot.stem:14s} {len(kept_english):4d} strings stay English (algorithms, diagrams, math)')
    for language in languages():
        print(f'== {language}')
        for name, template in templates.items():
            path = LOCALE / language / 'LC_MESSAGES' / f'{name}.po'
            if path.exists():
                catalog = load(path)
                catalog.update(template) # new: empty; changed: fuzzy, with the old translation
            else:
                catalog = Catalog(locale=language)
                catalog.update(template, no_fuzzy_matching=True)
            save(catalog, path)
            translated, fuzzy, untranslated = status(catalog)
            print(f'   {name:14s} {translated:4d} translated  {fuzzy:4d} changed  {untranslated:4d} new')


def pending(args) -> None:
    """the untranslated and changed strings of a language, with its glossary, as JSON"""
    items = []
    for name, (_, catalog) in catalogs(args.language).items():
        for m in messages(catalog):
            if not m.string or m.fuzzy:
                item = {'catalog': name, 'source': m.id, 'translation': ''}
                if m.fuzzy:
                    item['previous_translation'] = m.string # of the old English text
                items.append(item)
    data = {'language': args.language, 'glossary': glossary(args.language), 'strings': items}
    text = json.dumps(data, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
        print(f'{len(items)} strings to translate, written to {args.out}')
    else:
        print(text)


def apply(args) -> None:
    """writes the translations of a pending file back; empty translations are skipped"""
    data = json.loads(Path(args.file).read_text(encoding='utf-8'))
    found = catalogs(args.language)
    written = 0
    touched = set()
    for item in data['strings']:
        if not item.get('translation'):
            continue
        path, catalog = found[item['catalog']]
        message = catalog.get(item['source'])
        if message is None:
            print(f"not in the catalog any more, skipped: {item['source'][:60]!r}")
            continue
        message.string = item['translation']
        message.flags.discard('fuzzy')
        touched.add(item['catalog'])
        written += 1
    for name in touched:
        save(found[name][1], found[name][0])
    print(f'{written} translations written')


def check(args) -> None:
    """reports what is left to translate, and every translation that breaks the glossary, drops a
    kept word or changes the markup; exits with an error for broken markup, which breaks the build"""
    rules = glossary(args.language)
    totals = [0, 0, 0]
    term_problems, markup_problems = [], []
    for name, (_, catalog) in catalogs(args.language).items():
        totals = [t + s for t, s in zip(totals, status(catalog))]
        for m in messages(catalog):
            if not m.string or m.fuzzy:
                continue
            where = f'{name}: {m.id[:70]!r}'
            for pattern in MARKUP:
                if sorted(pattern.findall(m.id)) != sorted(pattern.findall(m.string)):
                    markup_problems.append(f'{where}\n      markup {pattern.pattern} differs')
            for word in rules['keep']:
                whole = re.compile(rf'(?<!\w){re.escape(word)}(?!\w)') # 'uv', not the uv of 'curve'
                if whole.search(m.id) and not whole.search(m.string):
                    term_problems.append(f'{where}\n      keep {word!r} as it is')
            for term, rule in rules['terms'].items():
                # in the prose only: a term in code or a formula stays as it is
                if re.search(rf'\b{re.escape(term)}(?:e?s)?\b', prose(m.id), re.IGNORECASE) and \
                        not any(form in m.string for form in rule['use']):
                    term_problems.append(f"{where}\n      {term!r} should be {' / '.join(rule['use'])}")
    translated, fuzzy, untranslated = totals
    print(f'{args.language}: {translated} translated, {fuzzy} changed, {untranslated} new')
    for title, problems in (('glossary and kept words', term_problems), ('markup', markup_problems)):
        print(f'{len(problems)} {title} problems')
        for problem in problems:
            print('   ' + problem)
    if markup_problems:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('update', help='extract the English text and update every catalog').set_defaults(run=update)
    p = commands.add_parser('pending', help='the strings to translate, as JSON')
    p.add_argument('language')
    p.add_argument('--out', help='write to this file instead of printing')
    p.set_defaults(run=pending)
    p = commands.add_parser('apply', help='write the translations of a pending file back')
    p.add_argument('language')
    p.add_argument('file')
    p.set_defaults(run=apply)
    p = commands.add_parser('check', help='glossary, kept words and markup of the translations')
    p.add_argument('language')
    p.set_defaults(run=check)
    args = parser.parse_args()
    args.run(args)


if __name__ == '__main__':
    main()
