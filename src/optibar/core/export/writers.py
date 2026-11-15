"""writers of prepared tables: each takes the tables and a path and writes one file.

They only lay the tables out for their format; what the tables hold is decided in tables.py.
"""
from __future__ import annotations
import csv
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any, Union

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from optibar.core.export.tables import Table, Tables, columns

ABOUT = 'About'


def slug(name: str) -> str:
    """a file name from a table name: 'Mass Summary' -> 'mass_summary'"""
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')


def about_table(tables: Tables) -> Table:
    """the meta data as a table of its own, for the formats that only hold tables"""
    return Table(ABOUT, columns('Item', 'Value'), [[key, value] for key, value in tables.meta.items()])


# --- JSON -------------------------------------------------------------------------------------

def write_json(tables: Tables, path: Union[str, Path]) -> None:
    """{"meta": {...}, "tables": {name: {"columns": [{"name", "unit"}], "rows": [{column: value}]}}}"""
    content = {
        'meta': tables.meta,
        'tables': {
            table.name: {
                'columns': [{'name': c.name, 'unit': c.unit} for c in table.columns],
                'rows': table.records(),
            }
            for table in tables.tables
        },
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(content, f, indent=2, ensure_ascii=False)


# --- CSV in a zip -----------------------------------------------------------------------------

def _csv_text(table: Table) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator='\n')
    writer.writerow([c.label for c in table.columns])
    writer.writerows([['' if v is None else v for v in row] for row in table.rows])
    # with a byte order mark, Excel reads the file as UTF-8 (Ø, ³, °)
    return '﻿' + buffer.getvalue()


def write_csv_zip(tables: Tables, path: Union[str, Path]) -> None:
    """a zip of one CSV file per table, numbered in the order of the tables, about.csv first"""
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('00_about.csv', _csv_text(about_table(tables)))
        for i, table in enumerate(tables.tables, start=1):
            archive.writestr(f'{i:02d}_{slug(table.name)}.csv', _csv_text(table))


# --- Excel ------------------------------------------------------------------------------------

def _width(value: Any) -> int:
    return len(str(value)) if value is not None else 0


def _sheet(workbook: Workbook, table: Table) -> None:
    sheet = workbook.create_sheet(table.name[:31]) # Excel limits sheet names to 31 characters
    sheet.append([c.label for c in table.columns])
    for row in table.rows:
        sheet.append(row)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    sheet.freeze_panes = 'A2'
    if table.rows:
        sheet.auto_filter.ref = sheet.dimensions
    for i, column in enumerate(table.columns, start=1):
        width = max([_width(column.label)] + [_width(row[i - 1]) for row in table.rows])
        sheet.column_dimensions[get_column_letter(i)].width = min(width + 3, 80)


def write_xlsx(tables: Tables, path: Union[str, Path]) -> None:
    """an Excel workbook with a sheet per table, the About sheet first"""
    workbook = Workbook()
    workbook.remove(workbook.active)
    _sheet(workbook, about_table(tables))
    for table in tables.tables:
        _sheet(workbook, table)
    workbook.save(path)
