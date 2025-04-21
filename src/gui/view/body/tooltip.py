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
    'typical': "قطر میلگرد عمومی",
    'additional': "قطر میلگرد تقویتی",
    'thermal': "قطر میلگرد حرارتی",
    'shear': "قطر میلگرد برشی",
    'elim-additional': "میلگردهای تقویت کوتاه‌تر از میزان انتخاب شده حذف می‌شود\n مبنا طول تئوریک میلگردها بر اساس متر است",
    'elim-shear': "چنانچه طول(به متر) قسمتی از نوار که نیاز به میلگرد برشی دارد کمتر از این عدد باشد، این قسمت از میلگردهای برشی حذف می‌شوند",
    'interval': "فاصله بین میلگردهای عمومی بر حسب سانتی‌متر",
    'total': "حداکثر تنوع طول میلگردهای تقویت در کل فونداسیون",
    'stack': "حداکثر تنوع طول میلگرد تقویت در یک دسته",
    'type-shear': "حداکثر تنوع چنیش میلگرد برشی (تعداد ساق‌ها در هر مقطع و فاصله طولی ساق‌ها) در فونداسیون",
    'computation': "ترسیم فونداسیون",
    'analysis': 'آنالیز فونداسیون برای سناریوهای مختلف چینش میلگرد تقویت\n نتیجه نهایی استفاده از این گزینه نموداری خواهد بود که وزن میلگردهای تقویت را بر اساس تنوع طول در دسته و کل فونداسیون نشان می‌دهد',
    'side-cover': 'حداقل فاصله میلگردهای طولی تا سطح جانبی فونداسیون',
}