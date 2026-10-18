"""the app theme: sv-ttk (Windows 11 style) plus colors for the widgets it doesn't style."""
import sys
import tkinter as tk
from tkinter import font, ttk
from typing import Dict

import sv_ttk

PALETTES = {
    'light': {
        'text_bg': '#ffffff', 'text_fg': '#1c1c1c', 'muted': '#6b6b6b', 'border': '#d0d0d0',
        'success': '#0f7b0f', 'warning': '#9d5d00', 'error': '#c42b1c', 'link': '#005fb8',
        'stripe': '#f3f3f3', 'tooltip_bg': '#f9f9f9',
    },
    'dark': {
        'text_bg': '#1c1c1c', 'text_fg': '#e4e4e4', 'muted': '#9d9d9d', 'border': '#3f3f3f',
        'success': '#6ccb5f', 'warning': '#fce100', 'error': '#ff99a4', 'link': '#60cdff',
        'stripe': '#262626', 'tooltip_bg': '#2b2b2b',
    },
}


def enable_dpi_awareness() -> None:
    """lets Windows render the app at the display's real resolution instead of stretching it,
    which blurs text and misplaces widgets on scaled displays. Must run before the first Tk()."""
    if sys.platform != 'win32':
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1) # system aware
    except (AttributeError, OSError):
        pass


def palette() -> Dict[str, str]:
    return PALETTES['dark' if sv_ttk.get_theme() == 'dark' else 'light']


def set_theme(root: tk.Misc, mode: str) -> None:
    """applies 'light' or 'dark'; widgets with their own colors refresh on <<ThemeChanged>>"""
    sv_ttk.set_theme(mode, root)
    _scale_fonts(root)
    colors = palette()
    style = ttk.Style(root)
    style.configure('Link.TLabel', foreground=colors['link'])
    style.configure('Muted.TLabel', foreground=colors['muted'])
    style.configure('Info.TLabel', foreground=colors['muted'])
    # sv-ttk fixes the row height in pixels; follow the font instead so rows don't overlap on scaled displays
    tree_font = str(style.lookup('Treeview', 'font') or 'TkDefaultFont') # lookup returns a Tcl object
    linespace = font.nametofont(tree_font, root).metrics('linespace')
    style.configure('Treeview', rowheight=max(26, int(linespace * 1.5)))


def _scale_fonts(root: tk.Misc) -> None:
    """sv-ttk sizes its fonts in pixels, which don't grow with the display scaling;
    points do, so convert them (96 dpi: 1 px = 0.75 pt). Only negative sizes are pixels."""
    for name in root.tk.splitlist(root.tk.call('font', 'names')):
        if name.startswith('SunValley'):
            named = font.nametofont(name, root)
            size = named.cget('size')
            if size < 0:
                named.configure(size=max(1, round(-size * 0.75)))


def report_font() -> font.Font:
    return font.Font(family='Consolas', size=10)
