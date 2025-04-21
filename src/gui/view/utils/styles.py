from tkinter import ttk

class Styler():
    def __init__(self) -> None:
        s = ttk.Style()
        s.configure('header.TFrame', background='#37483e')
        s.configure('link.TLabel', foreground='blue')
        s.configure('error.TLabel', foreground='red')