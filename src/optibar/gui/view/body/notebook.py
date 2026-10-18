import tkinter as tk
from tkinter import ttk
from .upload import UploadNote
from .calculation.notebook import CalcNote
from .results import ResultNote

class NoteBook(ttk.Notebook):
    def __init__(self, parent):
        ttk.Notebook.__init__(self, parent)

        # widgets
        self.upload = UploadNote(self)
        self.calc = CalcNote(self)
        self.results = ResultNote(self)

                
        # geometry
        self.upload.grid(sticky='ewns')
        self.calc.grid(sticky='ewsn')
        self.results.grid(sticky='ewns')
        
        self.add(self.upload, text='1. Input File')
        self.add(self.calc, text='2. Calculation')
        self.add(self.results, text='3. Results')