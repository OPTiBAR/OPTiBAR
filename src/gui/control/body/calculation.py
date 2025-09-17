import tkinter as tk
from typing import Dict
from src.control.utils.urls import connection_error, get_header, get_url
from src.view.utils.registry import Registry
from tkinter.messagebox import showinfo, showerror
from .special_lengths import Rebar

class Calc():
    def __init__(self, registry: Registry, project_data: Dict, result_data: Dict) -> None:
        self.registry = registry
        calc_note = registry.get('calc')
        self.calc_type = registry.get('type')
        self.setting = registry.get('setting')
        self.request_frame = registry.get('request')
        # self.special_lengths = self.setting.get_child('advanced').get_child('special-lengths')
        self.special_lengths = registry.get('special-lengths')


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
        self._stop_monitor()
        self.order_id = None
        self.request_frame.set_status("Waiting for input file ...")

        # initialize
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
            self.special_lengths.set_material(fc=self.project_data['data']['materials']['fc'], fy=self.project_data['data']['materials']['fy'])
            values = Rebar.get_values(fc=self.project_data['data']['materials']['fc'], fy=self.project_data['data']['materials']['fy'])
            self.special_lengths.set_values(values)
    
    def project_data_changed(self,*args):
        self._stop_monitor()
        
        # refesh results
        self.result_data['is_available'].set(False)
        self.result_data['data'] = None

        # adopt calc note
        self.request_frame.set_button_label('Calculate')
        if self.project_data['is_available'].get() == False:
            self.request_frame.set_button_state('disabled')
            self.setting.get_child('advanced').get_child('typical').set_strip_names([])
        else:
            self.request_frame.set_status("Ready")
            self.request_frame.set_button_state('!disabled')
            self.setting.get_child('advanced').get_child('typical').set_strip_names(self.project_data['data']['strip_names'])
            self.reset_pressed()
    
    def calc_type_changed(self, *args):
        # calc_widget = self.root.get_child('notebook').get_child('calc')
        # calc_type_value = calc_widget.get_child('type').get_value()
        calc_widget = self.registry.get('calc')
        calc_type_value = self.registry.get('type').get_value()
        if calc_type_value == 'analysis':
            calc_widget.get_child('setting').get_child('basic').set_analysis_layout()
        elif calc_type_value == 'calculation':
            calc_widget.get_child('setting').get_child('basic').set_calc_layout()


    def calc_pressed(self, *args):
        calc_type = self.calc_type.get_value() 
        stop_flag = self.stop_flag # a local copy of
        iter_counter = 0





