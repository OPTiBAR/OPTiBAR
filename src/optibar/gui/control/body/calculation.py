from typing import Dict
from tkinter.messagebox import showerror
from optibar.gui.view.body.calculation.notebook import SettingsPane
from optibar.gui.control.utils.job import EngineJob
from .special_lengths import Rebar

STALE_CHECK_INTERVAL = 600 # ms


class Calc():
    def __init__(self, calc_note: SettingsPane, project_data: Dict, result_data: Dict) -> None:
        self.calc_type = calc_note.calc_type
        self.setting = calc_note.setting
        self.request_frame = calc_note.request
        self.special_lengths = calc_note.setting.advanced.special_length
        self.job = None

        # bind to events
        self.request_frame.bind('<<calc-pressed>>', self.calc_pressed)
        self.calc_type.bind('<<calc-type-changed>>', self.calc_type_changed)
        self.special_lengths.bind('<<check-changed>>', self.check_changed)
        self.special_lengths.bind('<<reset-pressed>>', self.reset_pressed)

        # variables
        self.result_data = result_data
        self.project_data = project_data
        project_data['is_available'].trace_add('write', self.project_data_changed)

        # initialize
        self.request_frame.set_status("Waiting for input file ...")
        project_data['is_available'].set(False)
        self._stale_after = None
        self.request_frame.bind('<Destroy>', self._cancel_stale_check, add='+')
        self._check_stale()

    def _cancel_stale_check(self, event=None):
        if self._stale_after is not None:
            self.request_frame.after_cancel(self._stale_after)
            self._stale_after = None

    def _current_request(self):
        """the calc type and settings as they are now, or None while an entry is being edited"""
        try:
            return (self.calc_type.get_value(), self.setting.get_values())
        except Exception:
            return None

    def _check_stale(self):
        """marks the results out of date when the settings changed after the calculation"""
        data = self.result_data['data']
        if self.result_data['is_available'].get() and data is not None:
            current = self._current_request()
            if current is not None:
                stale = current != (data['calc_type'], data['config'])
                if self.result_data['stale'].get() != stale:
                    self.result_data['stale'].set(stale)
        self._stale_after = self.request_frame.after(STALE_CHECK_INTERVAL, self._check_stale)

    def check_changed(self, *args):
        if self.special_lengths.get_checked():
            self.special_lengths.set_columns_state('disabled')
            if self.project_data['is_available'].get():
                values = Rebar.calc_automatic(self.special_lengths.get_values()['ld']['bottom'])
                self.special_lengths.set_values(values)
        else:
            self.special_lengths.set_columns_state('!disabled')

    def reset_pressed(self, *args):
        if self.project_data['is_available'].get():
            materials = self.project_data['data']['materials']
            self.special_lengths.set_material(fc=materials['fc'], fy=materials['fy'])
            values = Rebar.get_values(fc=materials['fc'], fy=materials['fy'])
            self.special_lengths.set_values(values)

    def project_data_changed(self,*args):
        self._stop_job()

        # refesh results
        self.result_data['is_available'].set(False)
        self.result_data['data'] = None

        # adopt calc note
        self.request_frame.set_button_label('Calculate')
        if self.project_data['is_available'].get() == False:
            self.request_frame.set_status("Waiting for input file ...")
            self.request_frame.set_button_state('disabled')
            self.setting.advanced.typical.set_strip_names([])
        else:
            self.request_frame.set_status("Ready")
            self.request_frame.set_button_state('!disabled')
            self.setting.advanced.typical.set_strip_names(self.project_data['data']['strip_names'])
            self.reset_pressed()

    def calc_type_changed(self, *args):
        calc_type_value = self.calc_type.get_value()
        if calc_type_value == 'analysis':
            self.setting.basic.set_analysis_layout()
        elif calc_type_value == 'calculation':
            self.setting.basic.set_calc_layout()

    def _stop_job(self):
        if self.job is not None:
            self.job.stop()
            self.job = None
        self.request_frame.stop_progress()

    def calc_pressed(self, *args):
        if self.job is not None:
            self._stop_job()
            self.request_frame.set_status("Stopped")
            self.request_frame.set_button_label('Calculate')
            return

        calc_type = self.calc_type.get_value()
        config = self.setting.get_values()
        self.result_data['is_available'].set(False)
        self.result_data['data'] = None

        def on_progress(done: int, total: int):
            self.request_frame.set_progress(done, total)
            self.request_frame.set_status(f'Running, {done} of {total} combinations done')

        def on_done(result):
            self.job = None
            self.request_frame.stop_progress()
            self.request_frame.set_button_label('Calculate')
            self.request_frame.set_status('Finished')
            self.result_data['data'] = {
                'calc_type': calc_type,
                'config': config,
                'input_file': self.project_data['data']['file_path'],
                'result_data': result,
            }
            self.result_data['stale'].set(False)
            self.result_data['is_available'].set(True)

        def on_error(message: str):
            self.job = None
            self.request_frame.stop_progress()
            self.request_frame.set_button_label('Calculate')
            self.request_frame.set_status('Failed')
            showerror('Calculation Error', 'The calculation failed.\n\n' + message.strip().splitlines()[-1])
            print(message)

        self.request_frame.set_button_label('Stop')
        self.request_frame.set_status('Running')
        self.request_frame.start_progress()
        self.job = EngineJob(
            self.request_frame,
            calc_type,
            self.project_data['data']['input_data'],
            config,
            on_progress=on_progress,
            on_done=on_done,
            on_error=on_error,
        )
