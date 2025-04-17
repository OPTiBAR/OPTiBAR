# configuration for each run of the algorithm
from .rebar import RebarType
class Config():
    """[summary]
    """
    def __init__(self, data_dict):
        # diameter
        self.typical_rebar_type = RebarType(data_dict["diameter"]["typical"])
        self.additional_rebar_type = RebarType(data_dict["diameter"]["additional"])
        self.shear_rebar_type = RebarType(data_dict["diameter"]["shear"])
        self.thermal_rebar_type = RebarType(data_dict["diameter"]["thermal"])
        # type number
        self.total_type_number = data_dict["type_number"]["total"]
        self.stack_type_number = data_dict["type_number"]["stack"]
        self.shear_type_number = data_dict["type_number"]["shear"]
        # elimination
        self.reinfordement_elimination = data_dict["elimination"]["additional"]
        self.shear_elimination = data_dict["elimination"]["shear"]
        # typical arrangement
        exceptions = {}
        if "exceptions" in data_dict["typical_arrangement"]:
            for data in data_dict["typical_arrangement"]["exceptions"]:
                if data['strip_name'] not in exceptions:
                    exceptions[data['strip_name']] = {}
                exceptions[data['strip_name']][data['level']] = {
                    "method": data["method"],
                    "value": data["value"],
                    "diameter": RebarType(data["diameter"]),
                }
        self.typical_arrangement = {
            "method": data_dict["typical_arrangement"]["method"],
            "value": data_dict["typical_arrangement"]["value"],
            "exceptions": exceptions
        }
        self.side_cover = data_dict["side_cover"]
        if 'special_lengths' in data_dict:
            self.special_lengths = data_dict['special_lengths']
        else:
            self.special_lengths = None

        