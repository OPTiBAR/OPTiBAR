import tkinter as tk
from tkinter import ttk
from .upload import UploadNote
from .calculation.notebook import CalcNote
from .results import ResultNote
from src.view.utils.router import Router

class NoteBook(ttk.Notebook, Router):
    def __init__(self, parent):
        ttk.Notebook.__init__(self, parent)
        Router.__init__(self, 'notebook')    

        # widgets
        upload_note = UploadNote(self)
        calc_note = CalcNote(self)
        result_note = ResultNote(self)

        self.add_child(upload_note)
        self.add_child(calc_note)
        self.add_child(result_note)

                
        # geometry
        upload_note.grid(sticky='ewns')
        calc_note.grid(sticky='ewsn')
        result_note.grid(sticky='ewns')
        
        self.add(upload_note, text='1. File Upload')
        self.add(calc_note, text='2. Calculation')
        self.add(result_note, text='3. Results')