from typing import final

@final
class NotEnoughTypes(Exception):
    def __init__(self, message:str, min_feasible_type_num:int):
        self.min_feasible_type_num = min_feasible_type_num
        super().__init__(message)
