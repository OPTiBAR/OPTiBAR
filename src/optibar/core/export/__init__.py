"""exports a result as tables, in several formats.

Two steps, so a new format is one new writer:

- tables.prepare() turns a saved result into format-neutral tables (tables.py)
- a writer lays them out as one file (writers.py)

    from optibar.core.export import export
    export(saved, "foundation.xlsx")   # the format follows the extension: .xlsx, .zip (CSV) or .json
"""
from __future__ import annotations
from pathlib import Path
from typing import Callable, Dict, NamedTuple, Union

from optibar.core.export.tables import Column, Table, Tables, prepare
from optibar.core.export.writers import write_csv_zip, write_json, write_xlsx


class Format(NamedTuple):
    name: str
    extension: str
    write: Callable[[Tables, Union[str, Path]], None]


# by extension, in the order to offer them
FORMATS: Dict[str, Format] = {
    '.xlsx': Format('Excel workbook', '.xlsx', write_xlsx),
    '.zip': Format('CSV files (zip)', '.zip', write_csv_zip),
    '.json': Format('JSON tables', '.json', write_json),
}


def export(saved: Dict, path: Union[str, Path]) -> Tables:
    """writes the tables of a saved result to a file, in the format of its extension; returns the tables"""
    path = Path(path)
    format = FORMATS.get(path.suffix.lower())
    if format is None:
        raise ValueError(f"unknown export format '{path.suffix}', use one of {', '.join(FORMATS)}")
    tables = prepare(saved)
    format.write(tables, path)
    return tables


__all__ = ['Column', 'Table', 'Tables', 'prepare', 'export', 'FORMATS', 'Format']
