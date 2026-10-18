import tkinter as tk

class CreateToolTip(object):
    """
    create a tooltip for a given widget
    """
    def __init__(self, widget, widget_key: str):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = tooltips_dict[widget_key]
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='right',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)
    
    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()

tooltips_dict = {
    'typical': "Typical rebar diameter",
    'additional': "Additional (reinforcing) rebar diameter",
    'thermal': "Thermal rebar diameter",
    'shear': "Shear rebar diameter",
    "elim-additional": "Rebars shorter than the selected length will be removed.\nThe theoretical length of rebars is based on meters.",
    'elim-shear': "If the length (in meters) of a section of the strip that requires shear rebars is less than this value, shear rebars for that section will be removed.",
    "interval": "Spacing between typical rebars in centimeters",
    "total": "Maximum variety of reinforcing rebar lengths in the entire foundation",
    "stack": "Maximum variety of reinforcing rebar lengths in a single batch",
    "type-shear": "Maximum variety of shear rebar arrangement (number of legs per section and longitudinal spacing of legs) in the foundation.",
    "computation": "Foundation drawing",
    "analysis": "Foundation analysis for different reinforcing rebar arrangement scenarios.\n The final result of using this option will be a chart showing the weight of reinforcing rebars based on length variety in a batch and in the entire foundation.",
    "side-cover": "Minimum distance of longitudinal rebars to the side surface of the foundation",
}