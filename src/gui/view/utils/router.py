from __future__ import annotations
from typing import List

class Router():
    def __init__(self, name:str) -> None:
        self.name = name
        self.children = dict()
    
    def add_child(self, child: Router):
        if child.name not in self.children:
            self.children[child.name] = child
        else:
            raise ValueError('there is another child with the same name.')
            
    def get_child(self, child_name: str) -> Router:
        if child_name in self.children:
            return self.children[child_name]
        else:
            raise ValueError('there is no child with this name')
    
    def get_children(self) -> List[str]:
        return self.children.keys()
        