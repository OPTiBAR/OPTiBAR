"""Plot the analysis diagram of the docs as SVG, from the sample foundation.

Runs an analysis of tonf_m.accdb with the settings of the tutorial, for stack 3 and 4 and total 3 to 25,
and plots the mass of the additional rebars as the app's Diagram window does, on a white background,
into docs/source/_static/images/analysis_plot.svg. Takes about a minute.

From the repository root (needs the Access ODBC driver, like the app):

    uv run python docs/figures/analysis_plot.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from optibar.core.parser.parse import V16Parser
from optibar.core.run import run_analysis
from optibar.gui.control.body.report import diagram_data

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "src/optibar/core/tests/parser/data_files/tonf_m.accdb"
OUTPUT = ROOT / "docs/source/_static/images/analysis_plot.svg"

CONFIG = {
    "diameter": {"typical": 18, "additional": 25, "thermal": 12, "shear": 14},
    "typical_arrangement": {"method": "INTERVAL", "value": 0.2},
    "side_cover": 0.05,
    "elimination": {"additional": 0.2, "shear": 2.0},
    "type_number": {"total": {"from": 3, "to": 25}, "stack": {"from": 3, "to": 4}, "shear": 4},
}


def main() -> None:
    parser = V16Parser(str(SAMPLE))
    foundation = parser.get_foundation()
    parser.close()
    data = diagram_data(run_analysis(foundation, CONFIG))

    plt.rcParams["svg.hashsalt"] = "optibar" # stable ids, so a rerun gives the same file
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    fig.set_facecolor("white")
    for stack in sorted(data):
        totals = sorted(data[stack])
        ax.plot(totals, [data[stack][t]["additional"] for t in totals], label=f"{stack} piece stack", marker="o", markersize=4)
    ax.set_title("Additional Rebar Mass")
    ax.set_xlabel("Number of Length Types")
    ax.set_ylabel("mass(ton)")
    ax.grid(True, color="#d0d0d0", linewidth=0.6)
    ax.legend(loc="upper left", frameon=True)
    ax.invert_xaxis()
    fig.tight_layout()
    fig.savefig(OUTPUT, format="svg", metadata={"Date": None})
    print("wrote", OUTPUT)


if __name__ == "__main__":
    main()
