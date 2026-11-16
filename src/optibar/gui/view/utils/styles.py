"""the app theme: sv-ttk (Windows 11 style), plus the app's own styles and colors for the widgets it doesn't style.

The layout follows Windows 11 apps: the panes are white cards on a light gray window, groups of settings are
titled sections without borders, and the main numbers of a result are shown large.
"""
import sys
import tkinter as tk
from tkinter import font, ttk
from typing import Dict

import sv_ttk

PALETTES = {
    'light': {
        'text_bg': '#ffffff', 'text_fg': '#1c1c1c', 'muted': '#6b6b6b', 'border': '#d0d0d0',
        'success': '#0f7b0f', 'warning': '#9d5d00', 'error': '#c42b1c', 'link': '#005fb8',
        'stripe': '#f5f5f5', 'tooltip_bg': '#f9f9f9', 'card_bg': '#ffffff', 'subtle_bg': '#f5f5f5', 'window_bg': '#f0f0f0',
    },
    'dark': {
        'text_bg': '#272727', 'text_fg': '#e4e4e4', 'muted': '#9d9d9d', 'border': '#3f3f3f',
        'success': '#6ccb5f', 'warning': '#fce100', 'error': '#ff99a4', 'link': '#60cdff',
        'stripe': '#262626', 'tooltip_bg': '#2b2b2b', 'card_bg': '#272727', 'subtle_bg': '#303030', 'window_bg': '#1c1c1c',
    },
}


# the space inside the cards of the panes, px
CARD_PADDING = (20, 16, 20, 16)


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


def system_theme() -> str:
    """'dark' when Windows uses the dark mode for apps, otherwise 'light'"""
    if sys.platform != 'win32':
        return 'light'
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize')
        with key:
            return 'light' if winreg.QueryValueEx(key, 'AppsUseLightTheme')[0] else 'dark'
    except OSError:
        return 'light'


def set_title_bar(window: tk.Misc, mode: str) -> None:
    """the title bar of Windows 10 and 11 follows the theme; it stays light without this"""
    if sys.platform != 'win32':
        return
    try:
        import ctypes
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        value = ctypes.c_int(1 if mode == 'dark' else 0)
        # DWMWA_USE_IMMERSIVE_DARK_MODE: 20 on current Windows, 19 on early Windows 10 builds
        for attribute in (20, 19):
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)) == 0:
                break
    except (AttributeError, OSError):
        pass


def palette() -> Dict[str, str]:
    return PALETTES['dark' if sv_ttk.get_theme() == 'dark' else 'light']


def set_theme(root: tk.Misc, mode: str) -> None:
    """applies 'light' or 'dark'; widgets with their own colors refresh on <<ThemeChanged>>"""
    sv_ttk.set_theme(mode, root)
    _scale_fonts(root)
    set_title_bar(root, mode)
    colors = palette()
    style = ttk.Style(root)
    style.configure('Link.TLabel', foreground=colors['link'])
    style.configure('Muted.TLabel', foreground=colors['muted'])
    style.configure('Info.TLabel', foreground=colors['muted'])
    # the status badge of the file bar
    style.configure('Success.TLabel', foreground=colors['success'])
    style.configure('Warning.TLabel', foreground=colors['warning'])
    style.configure('Error.TLabel', foreground=colors['error'])
    # the widgets sit on white cards, only the gaps between the cards show the gray of the window
    style.configure('.', background=colors['card_bg'])
    style.configure('App.TFrame', background=colors['window_bg'])
    style.configure('TPanedwindow', background=colors['window_bg'])
    root.configure(background=colors['window_bg'])
    # titled sections instead of boxed groups: the label frames lose their border
    style.layout('TLabelframe', [('Labelframe.padding', {'sticky': 'nswe', 'expand': 1})])
    style.configure('TLabelframe', padding=(0, 2, 0, 0))
    style.configure('TLabelframe.Label', font='SunValleyBodyStrongFont')
    style.configure('Section.TLabel', font='SunValleySubtitleFont')
    style.configure('Unit.TLabel', foreground=colors['muted'])
    style.configure('Status.TLabel', foreground=colors['muted'])
    # the header: the app name and the input file
    style.configure('Brand.TLabel', font='SunValleySubtitleFont')
    style.configure('FileName.TLabel', font='SunValleyBodyStrongFont')
    # the cards of the result summary: a caption, a large number and its unit
    subtle = colors['subtle_bg']
    style.configure('Stat.TFrame', background=subtle)
    style.configure('StatCaption.TLabel', background=subtle, foreground=colors['muted'], font='SunValleyCaptionFont')
    style.configure('StatValue.TLabel', background=subtle, font='SunValleyTitleFont')
    style.configure('StatUnit.TLabel', background=subtle, foreground=colors['muted'])
    style.configure('StatNote.TLabel', background=subtle, foreground=colors['muted'], font='SunValleyCaptionFont')
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
    """the text of the report; its tables are laid out with tab stops, so it needn't be monospaced"""
    return font.Font(family='Segoe UI', size=10)
