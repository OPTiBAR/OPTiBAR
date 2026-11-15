"""Where the parser gets SAFE's tables from.

A table source returns the rows of a SAFE database table by name, so the
parser doesn't depend on how the tables were exported: an Access file read
through ODBC, or tables already in memory (read from another export, or
from SAFE's API).
"""
from __future__ import annotations
import os
from typing import Any, Dict, List, Mapping, Optional, Protocol, Sequence
import pyodbc
from .errors import TableMissingError, DriverMissingError

ACCESS_DRIVER = 'Microsoft Access Driver (*.mdb, *.accdb)'

Row = Dict[str, Any]


def has_access_driver() -> bool:
    """whether the ODBC driver needed to read SAFE access files is installed"""
    return ACCESS_DRIVER in pyodbc.drivers()


class TableSource(Protocol):
    def read(self, table: str, columns: Optional[Sequence[str]] = None) -> List[Row]:
        """rows of a table, each a dict of column name to value, in the order of the table.

        Args:
            table: the table name as SAFE writes it, e.g. 'Grid Lines'.
            columns: the columns to return; all of them, in the table's order, when None.

        Raises:
            TableMissingError: the table, or one of the columns, is not available.
        """
        ...

    def close(self) -> None:
        ...


class AccessSource():
    """tables of an Access file (.accdb / .mdb) exported by SAFE, read through the ODBC driver"""

    def __init__(self, file_path: str) -> None:
        if not has_access_driver():
            raise DriverMissingError()
        if not os.path.isfile(file_path):
            raise IOError("database file is not available")
        # the access driver rejects relative paths
        file_path = os.path.abspath(file_path)
        self.conn = pyodbc.connect('Driver={' + ACCESS_DRIVER + '};DBQ=' + file_path + ';')
        self.cursor = self.conn.cursor()

    def read(self, table: str, columns: Optional[Sequence[str]] = None) -> List[Row]:
        selected = '*' if columns is None else ','.join(f'[{column}]' for column in columns)
        try:
            self.cursor.execute(f'select {selected} from [{table}]')
        except pyodbc.Error:
            raise TableMissingError(table)
        names = [description[0] for description in self.cursor.description]
        return [dict(zip(names, row)) for row in self.cursor.fetchall()]

    def close(self) -> None:
        # safe to call twice, and after __init__ failed before connecting
        if getattr(self, 'cursor', None) is not None:
            self.cursor.close()
            self.cursor = None
        if getattr(self, 'conn', None) is not None:
            self.conn.close()
            self.conn = None

    def __del__(self):
        self.close()


class MemorySource():
    """tables already in memory: table name to a list of rows, each a dict of column name to value"""

    def __init__(self, tables: Mapping[str, Sequence[Mapping[str, Any]]]) -> None:
        self.tables = tables

    def read(self, table: str, columns: Optional[Sequence[str]] = None) -> List[Row]:
        if table not in self.tables:
            raise TableMissingError(table)
        rows = self.tables[table]
        if columns is None:
            return [dict(row) for row in rows]
        try:
            return [{column: row[column] for column in columns} for row in rows]
        except KeyError:
            raise TableMissingError(table)

    def close(self) -> None:
        pass
