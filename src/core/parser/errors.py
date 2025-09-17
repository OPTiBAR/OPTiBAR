TABLE_GROUPS = {
    'model': [
        '[Program Control]',
        '[Grid Lines]',
        '[Object Geometry - Design Strips]',
        '[Material Properties 03 - Concrete]',
        '[Material Properties 04 - Rebar]',
        '[Slab Design Overwrites 01 - Strip Based]',
        '[Design Preferences 02 - Rebar Cover - Slabs]',
        '[Slab Properties 02 - Solid Slabs]',
        '[Slab Property Assignments]',
        '[Object Geometry - Point Coordinates]',
        '[Load Assignments - Point Loads]',
        '[Object Geometry - Areas 01 - General]',
    ],
    'design': [
        '[Concrete Slab Design 01 - Flexural And Shear Data]',
    ]
}

ERROR_MESSAGES = {
    'model': 'Please select "MODEL DEFINITION" tables when exporting access file from CSI SAFE.',
    'design': 'Please select "DESIGN RESULTS" tables when exporting access file from CSI SAFE.',    
}


class TableMissingError(Exception):
    """Exception raised when a table is missing.

    Attributes:
        table_name -- input salary which caused the error
        message -- explanation of the error
    """

    def __init__(self, table_name, message=""):
        self.table_name = table_name
        if table_name in TABLE_GROUPS['model']:
            message = ERROR_MESSAGES['model']
        elif table_name in TABLE_GROUPS['design']:
            message = ERROR_MESSAGES['design']
        else:
            message = ''
        self.message = message
        super().__init__(self.message)

class MultipleMaterialError(Exception):
    """Exception raised when using two different material

    Args:
        material_name -- name of the material
        message -- explanation of the error
    """
    def __init__(self, material_name):
        self.material_name = material_name
        self.message = f"You have used more than one {material_name} material. Please Just use one type."
        super().__init__(self.message)