from __future__ import annotations
import copy
from typing import Callable, Dict, List

from core.io.input import InputInterpreter
from core.io.output import Output
from core.components.foundation import Foundation
from core.components.config import Config


def run_calculation(parsed_data: Dict, config_data: Dict) -> Dict:
    """runs the engine once.

    Returns:
        Dict: the output with a "data" key on success (plus "warnings" if any),
            or an "errors" key when the configuration is infeasible.
    """
    foundation = Foundation(InputInterpreter(copy.deepcopy(parsed_data)))
    foundation.run(Config(config_data))
    return Output(foundation).get_output()


def run_analysis(parsed_data: Dict, config_data: Dict, progress: Callable[[int, int], None] = None) -> List[Dict]:
    """runs the engine for every (stack, total) pair in the configured ranges.

    config_data["type_number"] has "stack" and "total" as {"from": int, "to": int}.

    Returns:
        List[Dict]: the "data" part of each run's output, or {} for infeasible pairs.
    """
    type_number = config_data["type_number"]
    pairs = [
        (stack, total)
        for stack in range(type_number["stack"]["from"], type_number["stack"]["to"] + 1)
        for total in range(type_number["total"]["from"], type_number["total"]["to"] + 1)
    ]
    results = []
    for i, (stack, total) in enumerate(pairs):
        config = copy.deepcopy(config_data)
        config["type_number"] = {"stack": stack, "total": total, "shear": type_number["shear"]}
        output = run_calculation(parsed_data, config)
        results.append(output.get("data", {}))
        if progress is not None:
            progress(i + 1, len(pairs))
    return results
