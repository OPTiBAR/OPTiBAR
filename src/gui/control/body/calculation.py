import tkinter as tk
from typing import Dict
import requests
from src.control.utils.urls import connection_error, get_header, get_url
from src.view.utils.router import Router
from src.control.utils.threading import tr_request, Monitor
from tkinter.messagebox import showinfo, showerror
from .special_lengths import Rebar

class Calc():
    def __init__(self, root: Router, token_var: tk.StringVar, project_data: Dict, result_data: Dict) -> None:
        self.root = root
        calc_note = root.get_child('notebook').get_child('calc')
        self.calc_type = calc_note.get_child('type')
        self.setting = calc_note.get_child('setting')
        self.request_frame = calc_note.get_child('request')
        self.special_lengths = self.setting.get_child('advanced').get_child('special-lengths')


        # bind to events
        self.request_frame.bind('<<calc-pressed>>', self.calc_pressed)
        self.calc_type.bind('<<calc-type-changed>>', self.calc_type_changed)
        self.special_lengths.bind('<<check-changed>>', self.check_changed)
        self.special_lengths.bind('<<reset-pressed>>', self.reset_pressed)

        # variables
        self.result_data = result_data
        self.token_var = token_var
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
        calc_widget = self.root.get_child('notebook').get_child('calc')
        calc_type_value = calc_widget.get_child('type').get_value()
        if calc_type_value == 'analysis':
            calc_widget.get_child('setting').get_child('basic').set_analysis_layout()
        elif calc_type_value == 'calculation':
            calc_widget.get_child('setting').get_child('basic').set_calc_layout()

    def _stop_monitor(self):
        if hasattr(self, 'monitor'):
            self.monitor.stop()
        self.monitor = Monitor(self.root)
        if hasattr(self, 'stop_flag'):
            self.stop_flag.set(True)
        self.stop_flag = tk.BooleanVar()
        self.stop_flag.set(False)


    def calc_pressed(self, *args):
        calc_type = self.calc_type.get_value() 
        stop_flag = self.stop_flag # a local copy of
        iter_counter = 0 

        def create_order_request():
            setting_values = {'config_data': self.setting.get_values()}
            calc_type = self.calc_type.get_value()
            if calc_type == 'calculation':
                url = get_url('calculation_orders', project_id = self.project_data['data']['project_id'])
            elif calc_type == 'analysis':
                url = get_url('analysis_orders', project_id = self.project_data['data']['project_id'])
            else:
                raise ValueError('calc type is not valid')
            
            thread = tr_request(method='post', url=url, json=setting_values, headers=get_header(self.token_var))
            self.monitor.run(thread, handle_create_order)
        
        def handle_create_order(response: requests.Response):
            if response is not None:
                if  response.status_code in (200,201):
                    self.order_id = response.json()['id']
                    self.request_frame.set_status('Waiting in the queue')
                    get_order()
                else:
                    stop_calc()
                    if response.status_code == 403:
                        showerror('Service Level', response.json()['detail'])
                    elif response.status_code == 404:
                        pass
                    else:
                        raise ValueError(f'unhandled status code {response.status_code}')
            elif not stop_flag.get():
                connection_error()
                        

            
        def retrieve_order():
            print('retrieve called')
            if calc_type == 'calculation':
                url = get_url('calculation_orders_id', project_id = self.project_data['data']['project_id'], order_id=self.order_id)
            elif calc_type == 'analysis':
                url = get_url('analysis_orders_id', project_id = self.project_data['data']['project_id'], order_id=self.order_id)
            else:
                raise ValueError('calc type is not valid')
            thread = tr_request(method='get', url=url, headers=get_header(self.token_var))
            self.monitor.run(thread, handle_retrieve_order)
        
        def handle_retrieve_order(response: requests.Response):
            if response is not None:
                if  response.status_code == 200:
                    if response.json()['status'] == 'WA':
                        self.request_frame.set_status('Waiting in the queue')
                    elif response.json()['status'] == 'ST':
                        if calc_type == 'analysis':
                            self.request_frame.set_status(f'Started, Progress: {response.json()["progress"]}')
                        else:
                            self.request_frame.set_status('Started')
                    elif response.json()['status'] == 'FN':
                        self.result_data['data'] = {
                            'order_id' : self.order_id,
                            'calc_type': calc_type,
                            'result_data' : response.json()['result_data'],
                        }
                        self.request_frame.set_status('Finished')
                        stop_calc()
                        showinfo('Calculation', 'Calculated successfuly. go to the 3. Results tab to observe the results.')
                        # comes last to show mass limit info after the successful calculation message.
                        self.result_data['is_available'].set(True)
                    else:
                        raise ValueError(f'unhandled status value {response.json()["status"]}')
                else:
                    raise ValueError(f'unhandled status code {response.status_code}')
            elif not stop_flag.get():
                self.request_frame.set_status('Connection Problem ...')

            
        
        def get_order():
            if not stop_flag.get():
                nonlocal iter_counter
                print(iter_counter)
                retrieve_order()
                if iter_counter < 5:
                    interval = 5000
                elif iter_counter < 10:
                    interval = 10000
                else:
                    interval = 20000
                self.root.after(interval, get_order)
                iter_counter += 1


        def delete_order():
            print('delete order called')
            if calc_type == 'calculation':
                url = get_url('calculation_orders_id', project_id = self.project_data['data']['project_id'], order_id=self.order_id)
            elif calc_type == 'analysis':
                url = get_url('analysis_orders_id', project_id = self.project_data['data']['project_id'], order_id=self.order_id)
            else:
                raise ValueError('calc type is not valid')
            thread = tr_request(method='delete', url=url, headers=get_header(self.token_var))
            self.monitor.run(thread, handle_delete_order)
        
        def handle_delete_order(response: requests.Response):
            print('handle delete order called')
            if response is not None:
                if  response.status_code == 204:
                    print('order deleted successfuly')    
                else:
                    raise ValueError(f'unhandled status code {response.status_code}')

        def stop_calc():
            self._stop_monitor()
            self.request_frame.set_button_label('Calculate')

        if self.request_frame.get_button_label() == 'Calculate':
            self.order_id = None
            self.result_data['is_available'].set(False)
            self.result_data['data'] = None

            self.request_frame.set_button_label('Stop')
            create_order_request()
        else:
            self.request_frame.set_status("Ready")
            stop_calc()
            if self.order_id is not None:
                delete_order()






