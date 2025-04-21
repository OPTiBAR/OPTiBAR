from packaging import version
import tkinter as tk
from tkinter import ttk
from pathlib import Path

from PIL import Image, ImageTk
import webbrowser
from src.view.utils.common import Popup
from src.setting import VERSION, CONTACTS

class HelpMenu(tk.Menu):
    def __init__(self, parent, root):
        super().__init__(parent)
        self.add_command(label='Documentation', command=lambda: root.event_generate("<<open-doc>>"))
        self.add_command(label='Check for updates', command=lambda: root.event_generate("<<menu-check-update>>"))
        self.add_command(label='Contacts', command=lambda: root.event_generate("<<contacts>>"))
        self.add_command(label='About', command=lambda: root.event_generate("<<about>>"))

class About(Popup):
    def __init__(self, root) -> None:
        Popup.__init__(self, title='About', root=root)
        main = self.main
        # self._window.minsize(200,200)
        # self._window.maxsize(200,200)

        # widgets
        optibar_img = Image.open((Path(__file__).parent.parent.parent.parent).joinpath('data', 'images', 'optibar.png').absolute()).convert("RGBA").resize((120,100))
        # optibar_img = Image.open("./data/images/optibar.png").convert("RGBA").resize((120,100))
        main.optibar_image = ImageTk.PhotoImage(optibar_img)
        logo_label = ttk.Label(main, image=main.optibar_image)
        version_label = ttk.Label(main, text='Software Version: ' + str(version.parse(VERSION)))
        text_label = ttk.Label(main, text='', wraplength=280)
        ok_button = ttk.Button(main, text='OK', command=self.close)
        
        # geometry
        logo_label.grid(row=0,column=0, sticky='n', padx=40, pady=15)
        version_label.grid(row=1,column=0, sticky='w', padx=15, pady=15)
        # text_label.grid(row=2,column=0, sticky='ns')
        ok_button.grid(row=3, column=0, sticky='s', padx=15, pady=15)
        
        
        for i in range(4):
            main.rowconfigure(i, weight=1)
        main.columnconfigure(0, weight=1)

        # for child in main.winfo_children(): 
        #     child.grid_configure(padx=15, pady=15)


class Contacts(Popup):
    def __init__(self, root) -> None:
        Popup.__init__(self, title='Contacts', root=root)
        # window = popup.window
        # window.minsize(300,300)
        # window.maxsize(300,300)
        main = self.main
        # window.rowconfigure(0, weight=1)
        
        # widgets
            # telegram
        telegram_img = Image.open((Path(__file__).parent.parent.parent.parent).joinpath('data', 'images', 'contacts', 'telegram.png').absolute()).convert("RGBA").resize((50,50))
        # telegram_img = Image.open("./data/images/contacts/telegram.png").convert("RGBA").resize((50,50))
        main.telegram_image = ImageTk.PhotoImage(telegram_img)
        telegram_logo = ttk.Label(main, image=main.telegram_image)
        telegram_link = ttk.Label(main, text=CONTACTS['telegram'], cursor="hand1")
        telegram_link['style'] = 'link.TLabel'
        telegram_link.bind('<Button-1>', lambda e:webbrowser.open(CONTACTS['telegram']))
            # whatsapp
        whatsapp_img = Image.open((Path(__file__).parent.parent.parent.parent).joinpath('data', 'images', 'contacts', 'whatsapp.png').absolute()).convert("RGBA").resize((50,50))
        # whatsapp_img = Image.open("./data/images/contacts/whatsapp.png").convert("RGBA").resize((50,50))
        main.whatsapp_image = ImageTk.PhotoImage(whatsapp_img)
        whatsapp_logo = ttk.Label(main, image=main.whatsapp_image)
        whatsapp_link = ttk.Label(main, text=CONTACTS['whatsapp'], cursor="hand1")
        whatsapp_link['style'] = 'link.TLabel'
        whatsapp_link.bind('<Button-1>', lambda e:webbrowser.open(CONTACTS['whatsapp']))
            # linkedin 
        linkedin_img = Image.open((Path(__file__).parent.parent.parent.parent).joinpath('data', 'images', 'contacts', 'linkedin.png').absolute()).convert("RGBA").resize((50,50))
        # linkedin_img = Image.open("./data/images/contacts/linkedin.png").convert("RGBA").resize((50,50))
        main.linkedin_image = ImageTk.PhotoImage(linkedin_img)
        linkedin_logo = ttk.Label(main, image=main.linkedin_image)
        linkedin_link = ttk.Label(main, text=CONTACTS['linkedin'], cursor="hand1")
        linkedin_link['style'] = 'link.TLabel'
        linkedin_link.bind('<Button-1>', lambda e:webbrowser.open(CONTACTS['linkedin']))
            # instagram 
        instagram_img = Image.open((Path(__file__).parent.parent.parent.parent).joinpath('data', 'images', 'contacts', 'instagram.png').absolute()).convert("RGBA").resize((50,50))
        # instagram_img = Image.open("./data/images/contacts/instagram.png").convert("RGBA").resize((50,50))
        main.instagram_image = ImageTk.PhotoImage(instagram_img)
        instagram_logo = ttk.Label(main, image=main.instagram_image)
        instagram_link = ttk.Label(main, text=CONTACTS['instagram'], cursor="hand1")
        instagram_link['style'] = 'link.TLabel'
        instagram_link.bind('<Button-1>', lambda e:webbrowser.open(CONTACTS['instagram']))
            # email
        # email_img = Image.open("./src/view/images/contacts/email.png").convert("RGBA").resize((50,50))
        # window.email_image = ImageTk.PhotoImage(email_img)
        # email_logo = ttk.Label(main, image=window.email_image)
        # email_link = ttk.Label(main, text=CONTACTS['email'])
        # email_link.bind('<Button-1>',  lambda e:webbrowser.open(CONTACTS['email']))
            # telephone
        # telephone_img = Image.open("./src/view/images/contacts/telephone.png").convert("RGBA").resize((50,50))
        # window.telephone_image = ImageTk.PhotoImage(telephone_img)
        # telephone_logo = ttk.Label(main, image=window.telephone_image)
        # telephone_link = ttk.Label(main, text=CONTACTS['telephone'])
        # telephone_link.bind('<Button-1>', lambda e:webbrowser.open(CONTACTS['telephone']))
        
        # geometry
        telegram_logo.grid(row=0,column=0, sticky='w')
        telegram_link.grid(row=0,column=1, sticky='w')
        whatsapp_logo.grid(row=1,column=0, sticky='w')
        whatsapp_link.grid(row=1,column=1, sticky='w')
        linkedin_logo.grid(row=2,column=0, sticky='w')
        linkedin_link.grid(row=2,column=1, sticky='w')
        instagram_logo.grid(row=3,column=0, sticky='w')
        instagram_link.grid(row=3,column=1, sticky='w')
        # email_logo.grid(row=4,column=0, sticky='w')
        # email_link.grid(row=4,column=1, sticky='w')
        # telephone_logo.grid(row=5,column=0, sticky='w')
        # telephone_link.grid(row=5,column=1, sticky='w')
        
        for i in range(4):
            main.rowconfigure(i, weight=1)

        for child in main.winfo_children(): 
            child.grid_configure(padx=15, pady=15)