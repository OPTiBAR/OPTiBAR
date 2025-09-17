from __future__ import annotations
from typing import Any, Dict

class Registry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._elements = {}
        return cls._instance

    def register(self, element: Any, name: str):
        if name in self._elements:
            raise ValueError(f"An element with the name '{name}' is already registered.")
        self._elements[name] = element

    def get(self, name: str) -> Any:
        if name not in self._elements:
            raise ValueError(f"No element registered with the name '{name}'.")
        return self._elements[name]

    def get_all_names(self):
        return list(self._elements.keys())

        