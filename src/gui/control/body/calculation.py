from typing import Dict
from tkinter.messagebox import showinfo, showerror
from gui.view.body.calculation.notebook import CalcNote
from gui.control.utils.job import EngineJob
from .special_lengths import Rebar

class Calc():
    def __init__(self, calc_note: CalcNote, project_data: Dict, result_data: Dict) -> None:
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
            showinfo('Calculation', 'Calculated successfully. Go to the 3. Results tab to observe the results.')
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
