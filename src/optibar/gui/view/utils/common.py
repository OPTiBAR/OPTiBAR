import re
import tkinter as tk
import webbrowser
from tkinter import font, ttk
from typing import List, Sequence, Tuple
from optibar.gui.view.utils.styles import palette, report_font

INDENT = 4
# the report's tables come as lines of cells padded with spaces, at least this many between two cells
CELL_GAP = re.compile(r' {3,}')
NUMBER = re.compile(r'^[-+]?[\d.,]+%?$')
DASHES = ('-', '–')
TABLE_LINES = ('RULE', 'ROW', 'ROW_ALT', 'TOTAL')
COLUMN_SPACE = 36 # px between the columns of a table
TABLE_MARGIN = 6 # px before the first column, also the padding of the striped rows


class LogWindow(ttk.Frame):
    """the report: messages, section headings, and tables laid out with tab stops, so they read
    like tables in a proportional font, not like columns of a terminal"""
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)

        body = report_font()
        self._fonts = {
            'body': body,
            'bold': font.Font(family=body.cget('family') + ' Semibold', size=body.cget('size')),
            'heading': font.Font(family='Segoe UI Semibold', size=body.cget('size') + 3),
            'mono': font.Font(family='Consolas', size=body.cget('size')),
        }
        self._tables = 0
        text = tk.Text(self, wrap= "none", width=40, relief='flat', borderwidth=0, highlightthickness=0,
            padx=4, pady=4, font=body, state='disabled', spacing1=1, spacing3=1)
        self.text = text
        yscroll = ttk.Scrollbar(self, orient = 'vertical', command = text.yview)
        xscroll = ttk.Scrollbar(self, orient = 'horizontal', command = text.xview)
        text['yscrollcommand'] = yscroll.set
        text['xscrollcommand'] = xscroll.set
        text.grid(column = 0, row = 0, sticky = 'nwes')
        xscroll.grid(column = 0, row = 1, sticky = 'we', pady=(4, 0))
        # only shown when needed
        self._autohide(xscroll, 'x')
        self._autohide(yscroll, 'y')
        yscroll.grid(column = 1, row = 0, sticky = 'ns', padx=(4, 0))
        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(1, weight = 0)
        self.grid_rowconfigure(1, weight = 0)

        # LINK lines open their text, a url, in the browser
        text.tag_bind('LINK', '<Button-1>', self._open_link)
        text.tag_bind('LINK', '<Enter>', lambda e: text.configure(cursor='hand2'))
        text.tag_bind('LINK', '<Leave>', lambda e: text.configure(cursor=''))

        self._apply_colors()
        self.bind('<<ThemeChanged>>', self._apply_colors)

    def _autohide(self, scrollbar: ttk.Scrollbar, axis: str) -> None:
        def set(first, last):
            if float(first) <= 0 and float(last) >= 1:
                scrollbar.grid_remove()
            else:
                scrollbar.grid()
            scrollbar.set(first, last)
        self.text[axis + 'scrollcommand'] = set

    def _open_link(self, event) -> None:
        start, end = self.text.tag_prevrange('LINK', f'@{event.x},{event.y} + 1c')
        webbrowser.open(self.text.get(start, end).strip())

    def _apply_colors(self, *args) -> None:
        colors = palette()
        self.text.configure(background=colors['text_bg'], foreground=colors['text_fg'], insertbackground=colors['text_fg'],
            selectbackground=colors['link'])
        self.text.tag_configure('ERROR', foreground=colors['error'])
        self.text.tag_configure('WARNING', foreground=colors['warning'])
        self.text.tag_configure('SUCCESS', foreground=colors['success'])
        self.text.tag_configure('INFO', foreground=colors['text_fg'])
        # report sections and tables, see gui/control/body/report.py
        self.text.tag_configure('HEADING', foreground=colors['text_fg'], font=self._fonts['heading'], spacing1=10)
        self.text.tag_configure('WARNING_HEADING', foreground=colors['warning'], font=self._fonts['heading'], spacing1=10)
        self.text.tag_configure('TABLE_HEAD', foreground=colors['muted'], font=self._fonts['bold'], spacing3=6)
        self.text.tag_configure('RULE', foreground=colors['border'], font=self._fonts['mono'])
        self.text.tag_configure('ROW', foreground=colors['text_fg'], spacing1=4, spacing3=4)
        self.text.tag_configure('ROW_ALT', foreground=colors['text_fg'], background=colors['stripe'], spacing1=4, spacing3=4)
        self.text.tag_configure('TOTAL', foreground=colors['text_fg'], font=self._fonts['bold'], spacing1=8)
        # a table that couldn't be split into cells keeps its padded columns
        self.text.tag_configure('MONO', font=self._fonts['mono'])
        self.text.tag_configure('MUTED', foreground=colors['muted'])
        self.text.tag_configure('LINK', foreground=colors['link'], underline=True)
    
    def clear(self) -> None:
        self.text['state'] = 'normal'
        self.text.delete('1.0', 'end')
        self.text['state'] = 'disabled'
    
    def write_success(self, data_str: str, indent:int=0) -> None:
        self._write(data_str, 'SUCCESS', indent)

    def write_info(self, data_str: str, indent: int = 0) -> None:
        self._write(data_str, 'INFO', indent)

    def write_error(self, data_str: str, indent:int = 0) -> None:
        self._write(data_str, 'ERROR', indent)

    def write_warning(self, data_str: str, indent:int = 0) -> None:
        self._write(data_str, 'WARNING', indent)

    def write_lines(self, lines: List) -> None:
        """writes (tag, text) pairs, tag being one of SUCCESS, INFO, WARNING, ERROR, or one of the
        lines of a table: TABLE_HEAD, then RULE, ROW, ROW_ALT and TOTAL lines"""
        i = 0
        while i < len(lines):
            if lines[i][0] == 'TABLE_HEAD':
                end = i + 1
                while end < len(lines) and lines[end][0] in TABLE_LINES:
                    end += 1
                self._write_table(lines[i:end])
                i = end
            else:
                self._write(lines[i][1], lines[i][0], 0)
                i += 1

    def _write_table(self, lines: Sequence[Tuple[str, str]]) -> None:
        """a table of the report, its cells at tab stops: numbers right-aligned, text left-aligned"""
        rows = [(tag, CELL_GAP.split(text.strip())) for tag, text in lines if tag != 'RULE']
        columns = len(rows[0][1])
        if any(len(cells) != columns for _, cells in rows):
            for tag, text in lines:
                self._write(text, (tag, 'MONO'), 0)
            return
        body = [cells for tag, cells in rows[1:]]
        numeric = [
            all(NUMBER.match(cells[i]) or cells[i] in DASHES for cells in body)
            and any(NUMBER.match(cells[i]) for cells in body)
            for i in range(columns)
        ]
        fonts = {'TABLE_HEAD': self._fonts['bold'], 'TOTAL': self._fonts['bold']}
        widths = [max(fonts.get(tag, self._fonts['body']).measure(cells[i]) for tag, cells in rows) for i in range(columns)]
        tabs, x = [], TABLE_MARGIN
        for i in range(columns):
            tabs += [x + widths[i], 'right'] if numeric[i] else [x, 'left']
            x += widths[i] + COLUMN_SPACE
        # a last stop, so every striped row is as wide as the table
        tabs += [x - COLUMN_SPACE + TABLE_MARGIN, 'left']
        self._tables += 1
        table_tag = f'TABLE_{self._tables}'
        self.text.tag_configure(table_tag, tabs=tabs)
        for tag, cells in rows:
            self._write('\t' + '\t'.join(cells) + '\t', (tag, table_tag), 0)

    def _write(self, data_str: str, tag, indent: int):
        self.text['state'] = 'normal'
        info_str = indent * INDENT * ' ' + data_str
        # the newline stays untagged, so a striped row is shaded as wide as its table, not the whole box
        self.text.insert('end', info_str, tag, '\n', ())
        self.text['state'] = 'disabled'


class Popup():
    def __init__(self,root,title) -> None:
        # it needs that root should be registered
        window = tk.Toplevel(root)
        window.title(title)
        self._window = window
        main = ttk.Frame(self._window)
        main.grid(sticky='nsew')
        self.main = main
        window.grid_columnconfigure(0, weight=1)
        window.grid_rowconfigure(0, weight=1)


        # the position of top left corner of the popup relative to the root window
        x = root.winfo_x()
        width = root.winfo_width()
        y = root.winfo_y()
        height = root.winfo_height()
        window.geometry("+%d+%d" % (x + width * .4, y + height * .2))

        window.protocol("WM_DELETE_WINDOW", self.close) # intercept close button
        window.transient(root) # dialog window is related to main
        window.wait_visibility() # can't grab until window appears, so we wait
        window.grab_set() # ensure all input goes to our window
        # window.wait_window()

    def close(self):
        self._window.grab_release()
        self._window.destroy()

    def is_live(self):
        try:
            self._window.winfo_name()
            return True
        except:
            return False

    def bind(self, event, fun):
        self._window.bind(event, fun)

class IntCombo(ttk.Combobox):
    def __init__(self, parent, values):
        super().__init__(parent, width=10)
        self.int_var = tk.IntVar()
        self['textvariable'] = self.int_var
        self.state(["readonly"])
        self.set_values(values)

    def set_values(self, values: List[int]) -> None:
        self['values'] = list(values)

    def get_value(self) -> int:
        return self.int_var.get()
    
    def set_value(self, value: int) -> None:
        return self.int_var.set(value)

class IntEntry(ttk.Entry):
    def __init__(self, parent, upper_bound:float = float('inf')):
        super().__init__(parent, width=10,  validate="focusout", validatecommand=self.validate_entry)
        self.upper_bound = upper_bound
        self.str_var = tk.StringVar()
        self['textvariable'] = self.str_var
        self.last_valid = ''
    
    def set_value(self, value: str) -> None:
        self.str_var.set(value)
        self.last_valid = value
    
    def get_value(self) -> int:
        return int(self.str_var.get())
    
    def set_state(self, state: str) -> None:
        if state == 'disabled':
            pass
        elif state == '!disabled':
            pass
        else:
            raise ValueError('state value is not valid')
    
    def _valid(self, value: str) -> bool:
        try:
            int_value = int(value)
            if 0 < int_value < self.upper_bound:
                return True
            else:
                return False
        except:
            return False
    
    def validate_entry(self):
        value = self.str_var.get()
        if self._valid(value):
            self.set_value(str(int(value)))
            return True
        else:
            self.set_value(self.last_valid)
            return False
            

        
