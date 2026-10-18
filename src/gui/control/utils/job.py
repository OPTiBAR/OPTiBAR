"""runs the engine in a separate process so the window stays responsive and the run can be stopped."""
import multiprocessing
import queue
import traceback
import tkinter as tk
from typing import Callable, Dict

from core.run import run_calculation, run_analysis

POLL_INTERVAL = 200 # ms


def _work(messages: multiprocessing.Queue, calc_type: str, parsed_data: Dict, config_data: Dict) -> None:
    """process entry point, it must be a module level function to be picklable."""
    try:
        if calc_type == 'calculation':
            result = run_calculation(parsed_data, config_data)
        elif calc_type == 'analysis':
            result = run_analysis(parsed_data, config_data, progress=lambda i, n: messages.put(('progress', (i, n))))
        else:
            raise ValueError(f'calc type is not valid: {calc_type}')
        messages.put(('done', result))
    except Exception:
        messages.put(('error', traceback.format_exc()))


class EngineJob():
    """one engine run, reported back on the tk event loop.

    Args:
        widget: any widget, used to schedule polling with after()
        on_progress(done, total): called during analysis runs
        on_done(result): called with the engine output
        on_error(message): called with the traceback if the engine raises
    """
    def __init__(self, widget: tk.Misc, calc_type: str, parsed_data: Dict, config_data: Dict,
            on_progress: Callable[[int, int], None], on_done: Callable[[object], None], on_error: Callable[[str], None]) -> None:
        self.widget = widget
        self.on_progress = on_progress
        self.on_done = on_done
        self.on_error = on_error
        self._messages = multiprocessing.Queue()
        self._process = multiprocessing.Process(target=_work, args=(self._messages, calc_type, parsed_data, config_data), daemon=True)
        self._process.start()
        self._after_id = widget.after(POLL_INTERVAL, self._poll)

    def stop(self) -> None:
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
        if self._process.is_alive():
            self._process.terminate()

    def _poll(self) -> None:
        self._after_id = None
        while True:
            try:
                message = self._messages.get_nowait()
            except queue.Empty:
                break
            if self._handle(*message):
                return
        if self._process.is_alive():
            self._after_id = self.widget.after(POLL_INTERVAL, self._poll)
            return
        # the last message can still be in transit after the process exits
        try:
            while not self._handle(*self._messages.get(timeout=1)):
                pass
        except queue.Empty:
            # the process died without reporting (e.g. killed or crashed in native code)
            self.on_error(f'The calculation process exited unexpectedly (exit code {self._process.exitcode}).')

    def _handle(self, kind: str, payload) -> bool:
        """returns True when the job is finished"""
        if kind == 'progress':
            self.on_progress(*payload)
            return False
        if kind == 'done':
            self.on_done(payload)
        else:
            self.on_error(payload)
        return True
