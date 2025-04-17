class NotEnoughTypes(Exception):
    def __init__(self, message, min_feasible_type_num):
        self.min_feasible_type_num = min_feasible_type_num
        super().__init__(message)

class MyWarning(Warning):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)