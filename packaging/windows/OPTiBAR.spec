# PyInstaller spec of the Windows build of OPTiBAR: a one-folder build of the desktop app, in dist/OPTiBAR.
# Build it with build.ps1 of this folder, which then makes the installer from it.
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

ROOT = Path(SPECPATH).parents[1]


def not_a_test(name: str) -> bool:
    return '.tests' not in name and not name.endswith('.tests')


# Pyomo registers its solvers (appsi_highs among them) by importing plugin modules at run time,
# which PyInstaller can't see; its tests are left out
hidden_imports = collect_submodules('pyomo', filter=not_a_test)
hidden_imports += collect_submodules('highspy')

datas = [
    # the JSON schemas and the GUI images, but not the test data
    *collect_data_files('optibar', excludes=['**/tests/**', '**/__pycache__/**']),
    *collect_data_files('sv_ttk'),
]
binaries = collect_dynamic_libs('highspy')

a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT / 'src')],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    excludes=['pytest', 'IPython', 'jupyter', 'notebook', 'sphinx', 'PyQt5', 'PyQt6', 'PySide6'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OPTiBAR',
    icon=str(ROOT / 'assets' / 'optibar.ico'),
    console=False,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name='OPTiBAR', upx=False)
