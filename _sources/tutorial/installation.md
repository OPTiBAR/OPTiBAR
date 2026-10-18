Installation
============

## Requirements

- **Windows**. OPTiBAR reads the Access database exported by SAFE through a Windows ODBC driver.
- **Python 3.13** or higher, or [uv](https://docs.astral.sh/uv/), which installs the right Python for you.
- The **Microsoft Access ODBC driver**, from the
  [Microsoft Access Database Engine 2016 Redistributable](https://www.microsoft.com/en-us/download/details.aspx?id=54920).
  Its bitness must match Python's: install the 64-bit version for 64-bit Python.
  OPTiBAR checks for the driver at startup and shows the download link when it is missing.

AutoCAD is not needed: OPTiBAR writes the drawing as a DXF file, which AutoCAD, AutoCAD LT, BricsCAD and free viewers can open.

## With uv

Clone the repository and run the app. uv creates the environment and installs the dependencies on the first run.

```bash
git clone https://github.com/OPTiBAR/OPTiBAR.git
cd OPTiBAR
uv run main.py
```

## With pip

```bash
pip install git+https://github.com/OPTiBAR/OPTiBAR
```

This installs the `optibar` command, which starts the app:

```bash
optibar
```

## Check the installation

The OPTiBAR window opens with three tabs: **1. Input File**, **2. Calculation** and **3. Results**.
If the **Report** box of the first tab says the Access ODBC driver is not installed, install it and restart OPTiBAR.
