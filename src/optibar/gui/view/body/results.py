import tkinter as tk
from tkinter import ttk
from typing import Dict, List, NamedTuple, Tuple
from optibar.gui.view.utils.common import LogWindow
from optibar.gui.view.utils.styles import CARD_PADDING, palette

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class FileFrame(ttk.Frame):
    """the actions on a result, right of the title of the results card"""
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)

        # widgets
        self.save_button = ttk.Button(self, text='Save', command=lambda: self.event_generate("<<save-button-pressed>>"))
        self.export_button = ttk.Button(self, text='Export tables…', command=lambda: self.event_generate("<<export-button-pressed>>"))
        self.pdf_button = ttk.Button(self, text='PDF drawing', command=lambda: self.event_generate("<<pdf-button-pressed>>"))
        self.dxf_button = ttk.Button(self, text='DXF drawing', command=lambda: self.event_generate("<<dxf-button-pressed>>"))
        self.diagram_button = ttk.Button(self, text='Mass diagram', command=lambda: self.event_generate("<<diagram-button-pressed>>"))
        separator = ttk.Separator(self, orient=tk.VERTICAL)

        # geometry: the files of the result, then the drawings, then the diagram of an analysis
        for i, widget in enumerate((self.save_button, self.export_button, separator, self.pdf_button, self.dxf_button, self.diagram_button)):
            widget.grid(row=0, column=i, padx=(0 if i == 0 else 8, 0), sticky='ns')

    def set_button_state(self, name: str, state: str):
        """toggles the state of a button

        Args:
            name (str): should be save, export, pdf, dxf or diagram
            state (str): should be disabled or !disabled

        Raises:
            ValueError: raises if the input value is not appropriate.
        """
        if name not in ('save', 'export', 'pdf', 'dxf', 'diagram'):
            raise ValueError("button name should be save, export, pdf, dxf or diagram")
        if state not in ('disabled', '!disabled'):
            raise ValueError("state value should be disabled or !disabled")
        getattr(self, name + '_button').state([state])


class Stat(NamedTuple):
    """one card of the summary: a caption, a large value with its unit, and a note under it"""
    caption: str
    value: str
    unit: str = ''
    note: str = ''


class SummaryCards(ttk.Frame):
    """the main numbers of a result, in a row of cards above the report"""
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.cards: List[ttk.Frame] = []

    def show(self, stats: List[Stat]) -> None:
        self.clear()
        for i, stat in enumerate(stats):
            card = ttk.Frame(self, style='Stat.TFrame', padding=(14, 10, 14, 10))
            ttk.Label(card, text=stat.caption, style='StatCaption.TLabel').grid(row=0, column=0, sticky='w')
            # the unit follows the number, on its baseline
            value = ttk.Frame(card, style='Stat.TFrame')
            ttk.Label(value, text=stat.value, style='StatValue.TLabel').grid(row=0, column=0, sticky='sw')
            ttk.Label(value, text=stat.unit, style='StatUnit.TLabel').grid(row=0, column=1, sticky='sw', padx=(4, 0), pady=(0, 7))
            value.grid(row=1, column=0, sticky='w')
            note = ttk.Label(card, text=stat.note, style='StatNote.TLabel')
            note.grid(row=2, column=0, sticky='w')
            # narrow cards wrap their note instead of cutting it
            card.bind('<Configure>', lambda e, note=note: note.configure(wraplength=max(60, e.width - 28)))
            card.grid(row=0, column=i, sticky='nswe', padx=(0 if i == 0 else 10, 0))
            self.columnconfigure(i, weight=1, uniform='stat')
            self.cards.append(card)

    def clear(self) -> None:
        for card in self.cards:
            card.destroy()
        for i in range(len(self.cards)):
            self.columnconfigure(i, weight=0, uniform='')
        self.cards = []


class Diagram():
    """the mass of the analysis runs over the number of length types, a line per stack number.

    Args:
        series: by name, the title and the masses to plot: {stack: {'total_num': [...], 'mass': [...]}}
    """
    def __init__(self, root, series: Dict[str, Tuple[str, Dict[int, Dict[str, List]]]]) -> None:
        self.series = series
        window = tk.Toplevel(root)
        window.title('Mass Diagram')
        window.configure(background=palette()['card_bg'])
        main = ttk.Frame(window, padding=(16, 12))
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # which mass to plot
        self.kind_var = tk.StringVar(window, next(iter(series)))
        switch = ttk.Frame(main)
        for i, name in enumerate(series):
            ttk.Radiobutton(switch, text=name, value=name, variable=self.kind_var,
                command=self._plot).grid(row=0, column=i, padx=(0, 20))
        switch.pack(side=tk.TOP, anchor='w', pady=(0, 6))

        fig = Figure(figsize=(7, 4.4), dpi=100, layout='constrained')
        self.font = {'family': ['Segoe UI', 'DejaVu Sans']}
        self.sub = fig.add_subplot(1,1,1)
        # match the app theme
        colors = palette()
        fig.set_facecolor(colors['card_bg'])
        self.sub.set_facecolor(colors['card_bg'])
        self.sub.tick_params(colors=colors['muted'], length=0)
        for item in (self.sub.xaxis.label, self.sub.yaxis.label, self.sub.title):
            item.set_color(colors['text_fg'])
        for side, spine in self.sub.spines.items():
            spine.set_visible(side == 'bottom')
            spine.set_color(colors['border'])
        self.sub.grid(True, axis='y', color=colors['border'], linewidth=0.6)
        self.sub.set_axisbelow(True)
        self.colors = colors

        canvas = FigureCanvasTkAgg(fig, master=main)
        canvas.get_tk_widget().configure(highlightthickness=0, borderwidth=0)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.canvas = canvas
        self._plot()

    def _plot(self) -> None:
        title, mass_dict = self.series[self.kind_var.get()]
        sub = self.sub
        sub.clear()
        sub.grid(True, axis='y', color=self.colors['border'], linewidth=0.6)
        for stack_num in mass_dict:
            sub.plot(mass_dict[stack_num]['total_num'], mass_dict[stack_num]['mass'], label=f'{stack_num} piece stack',
                marker='o', markersize=4, linewidth=2)
        sub.set_title(title, loc='left', color=self.colors['text_fg'], fontsize=12, fontweight='bold', fontdict=self.font, pad=28)
        sub.set_xlabel('Number of length types', color=self.colors['muted'], fontdict=self.font)
        sub.set_ylabel('Mass (t)', color=self.colors['muted'], fontdict=self.font)
        # above the plot, so it never covers a line
        legend = sub.legend(loc='lower left', bbox_to_anchor=(0, 1.0), ncols=len(mass_dict), frameon=False,
            borderaxespad=0.2, prop=self.font)
        for text in legend.get_texts():
            text.set_color(self.colors['text_fg'])
        sub.invert_xaxis()
        self.canvas.draw()


class ResultsPane(ttk.Frame):
    """the right pane, a card: the actions on the result, its main numbers, and the report of the input file and the results"""
    def __init__(self, parent):
        # the gray margin to the settings card; the card is inside it
        ttk.Frame.__init__(self, parent, style='App.TFrame', padding=(6, 0, 0, 0))
        card = ttk.Frame(self, style='Card.TFrame', padding=CARD_PADDING)

        title = ttk.Label(card, text='Results', style='Section.TLabel')
        self.files = FileFrame(card)
        # shown when the settings changed after the calculation
        self.stale_label = ttk.Label(card, style='Warning.TLabel', justify='left',
            text='⚠ The settings changed after this calculation. Press Calculate to update the results.')
        card.bind('<Configure>', lambda e: self.stale_label.configure(wraplength=max(200, e.width - 40)))
        self.summary = SummaryCards(card)
        self.log = LogWindow(card)

        # geometry
        card.grid(row=0, column=0, sticky='news')
        title.grid(row=0, column=0, sticky='w', pady=(0, 10))
        self.files.grid(row=0, column=1, sticky='e', pady=(0, 10))
        self.stale_label.grid(row=1, column=0, columnspan=2, sticky='w', pady=(0, 10))
        self.stale_label.grid_remove()
        self.summary.grid(row=2, column=0, columnspan=2, sticky='we', pady=(0, 12))
        self.log.grid(row=3, column=0, columnspan=2, sticky='news')
        card.columnconfigure(1, weight=1)
        card.rowconfigure(3, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def set_stale(self, stale: bool) -> None:
        if stale:
            self.stale_label.grid()
        else:
            self.stale_label.grid_remove()
