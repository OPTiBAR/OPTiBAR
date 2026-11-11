"""the Report box of the results pane, shared by the input file and the results"""
from typing import List, Tuple
from optibar.gui.view.utils.common import LogWindow

Lines = List[Tuple[str, str]]


class ReportLog():
    """the report has two sections: the input file at the top, the results below it.
    Each section is replaced on its own, so the messages about the input file stay visible
    while results come and go."""
    def __init__(self, log: LogWindow) -> None:
        self.log = log
        self.input: Lines = []
        self.results: Lines = []
        self.render()

    def set_input(self, lines: Lines) -> None:
        self.input = list(lines)
        self.render()

    def set_results(self, lines: Lines) -> None:
        self.results = list(lines)
        self.render()

    def show_input(self) -> None:
        self.log.text.see('1.0')

    def render(self) -> None:
        log = self.log
        log.clear()
        if self.input:
            log.write_lines([('HEADING', 'Input File'), ('INFO', '')] + self.input + [('INFO', '')])
        if self.results:
            log.write_lines(self.results)
        elif not self.input:
            log.write_lines([
                ('MUTED', 'To start, open the Access file exported from SAFE:'),
                ('MUTED', 'File > Open, or the Open… button above.'),
            ])
        log.text.yview_moveto(0)
