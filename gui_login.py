#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Draw the log window, create epic list, Disclaimer
"""

import wx
import wx.lib.agw.hyperlink as hl

import personal
# Variables global
import globalvar


class LogWindow(wx.Frame):
    """Class for the window "login"
    """

    def __init__(self, parent, title):
        """Init Window """
        super(LogWindow, self).__init__(parent, title=title, size=(450, 520))
        self.init_ui()
        self.Centre()
        self.Show()

    def init_ui(self):
        """Init Window Graphical Interface"""

        # Load Combobox with Epic dictionnary
        # Tri AlphB de la list des keys
        self.epic_choices = sorted(globalvar.epic_dict.keys())

        # Create default value in "personal.py"
        self.create_default_values()

        # Create panel & sizer
        panel = wx.Panel(self)
        sizer = wx.GridBagSizer(5, 5)

        # ######################################################################
        # Icone de la fenêtre
        self.icon = wx.Icon('l3.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)

        # Logo L3 Scalping (coin haut droit)
        logo = wx.StaticBitmap(panel, bitmap=wx.Bitmap('L3.png'))
        sizer.Add(logo, pos=(0, 3), flag=wx.TOP | wx.RIGHT | wx.ALIGN_RIGHT,
                  border=5)

        # Ligne de séparation
        line = wx.StaticLine(panel)
        sizer.Add(line, pos=(1, 0), span=(1, 5), flag=wx.EXPAND | wx.BOTTOM,
                  border=10)
        # ######################################################################

        # Label username
        text_username = wx.StaticText(panel, label="Username")
        sizer.Add(text_username, pos=(2, 0), flag=wx.LEFT, border=5)
        # Textcontrol username
        self.tc_username = wx.TextCtrl(panel, -1, personal.username)
        sizer.Add(self.tc_username, pos=(2, 1), span=(1, 2),
                  flag=wx.TOP | wx.EXPAND)

        # Label Password
        text_passwd = wx.StaticText(panel, label="Password")
        sizer.Add(text_passwd, pos=(3, 0),
                  flag=wx.LEFT | wx.TOP, border=5)
        # Textcontrol Password
        self.tc_passwd = wx.TextCtrl(panel, -1,
                                    personal.password.decode('base64'),
                                    style=wx.TE_PASSWORD)
        sizer.Add(self.tc_passwd, pos=(3, 1), span=(1, 2),
                  flag=wx.TOP | wx.EXPAND, border=5)

        # Label API
        text_api = wx.StaticText(panel, label="API")
        sizer.Add(text_api, pos=(4, 0), flag=wx.LEFT | wx.TOP, border=5)
        # Textcontrol API
        self.tc_api = wx.TextCtrl(panel, -1, personal.api_key)
        sizer.Add(self.tc_api, pos=(4, 1), span=(1, 3),
                  flag=wx.TOP | wx.EXPAND, border=5)

        # CheckBox Demo
        self.chk_demo = wx.CheckBox(panel, -1, 'Demo')
        self.chk_demo.SetValue(personal.is_demo)
        sizer.Add(self.chk_demo, pos=(5, 1), flag=wx.TOP | wx.LEFT, border=5)

        # Label Accounts
        text_nb_account = wx.StaticText(panel, label="Account [0,1,2]")
        sizer.Add(text_nb_account, pos=(6, 0), flag=wx.LEFT | wx.TOP, border=5)
        # Textcontrol Accounts
        self.tc_nb_account = wx.TextCtrl(panel, -1, personal.account_nb)
        sizer.Add(self.tc_nb_account, pos=(6, 1), span=(1, 1),
                  flag=wx.TOP | wx.EXPAND, border=5)

        # Label Proxy
        text_proxies = wx.StaticText(panel, label="Proxy (Optional)")
        sizer.Add(text_proxies, pos=(7, 0), flag=wx.LEFT | wx.TOP, border=5)
        # textcontrol Proxy
        self.tc_proxy = wx.TextCtrl(panel, -1, personal.proxies.get('https'))
        sizer.Add(self.tc_proxy, pos=(7, 1), span=(1, 3),
                  flag=wx.TOP | wx.EXPAND, border=5)

        # Ligne de séparation
        line2 = wx.StaticLine(panel)
        sizer.Add(line2, pos=(8, 0), span=(1, 5),
                  flag=wx.EXPAND | wx.TOP, border=10)
        # ######################################################################

        # Label Epic
        text_epic = wx.StaticText(panel, label="Epic")
        sizer.Add(text_epic, pos=(9, 0), flag=wx.TOP | wx.LEFT, border=10)

        # Combo Epic
        self.combo = wx.ComboBox(panel, -1, choices=self.epic_choices)
        sizer.Add(self.combo, pos=(9, 1), span=(1, 3),
                  flag=wx.TOP | wx.BOTTOM | wx.EXPAND, border=10)

        # Selection automatique de L'epic dans la liste
        # si il existe dans personnal.py
        # sinon on definit le Dax par défaut
        if personal.epic != '':
            index_epic = globalvar.epic_dict.values().index(personal.epic)
            my_epic = globalvar.epic_dict.keys()[index_epic]
        else:
            my_epic = 'IX.D.DAX.IMF.IP'

        self.combo.SetStringSelection(my_epic)

        # Ligne de séparation
        line3 = wx.StaticLine(panel)
        sizer.Add(line3, pos=(10, 0), span=(1, 5),
                  flag=wx.EXPAND | wx.BOTTOM, border=5)
        # ######################################################################

        # Disclaimer Panel
        box_disclaimer = wx.StaticBox(panel, label="DISCLAIMER")
        box_disclaimer.SetForegroundColour((255, 0, 0))
        boxsizer = wx.StaticBoxSizer(box_disclaimer, wx.VERTICAL)

        # Disclaimer Checkbox
        disclaimer =  u'Je certifie avoir lu, compris et accepté, ' \
                      u'les conditions générales\n d\'utilisation ' \
                      u'du logiciel \"L3 Scalping\"'
        self.chk_cgu = wx.CheckBox(panel, label=disclaimer)
        self.chk_cgu.SetForegroundColour((255, 0, 0))
        self.chk_cgu.SetValue(False)

        # Add checkbox CGU to Disclaimer Panel
        boxsizer.Add(self.chk_cgu, flag=wx.LEFT | wx.TOP, border=5)

        # Web links to L3 CGU on ANDLIL Website
        cgu_url = "http://www.andlil.com/forum/" \
                  "scalping-l3-installation-mise-a-jour-explications-t8887.html"
        hyper1 = hl.HyperLinkCtrl(panel, -1,
                                  "Lire les C.G.U du logiciel L3 Scalping",
                                  URL=cgu_url)

        # Add weblink to Disclaimer Panel
        boxsizer.Add(hyper1, flag=wx.LEFT, border=25)

        # Bind to checkCGU function
        self.Bind(wx.EVT_CHECKBOX, self.check_cgu, self.chk_cgu)

        # Add Panel Disclaimer to Sizer
        sizer.Add(boxsizer, pos=(11, 0), span=(1, 5),
                  flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT | wx.BOTTOM,
                  border=10)
        # ######################################################################

        # Boutton Exit, Bind on Self.close
        btn_exit = wx.Button(panel, label="Exit")
        btn_exit.Bind(wx.EVT_BUTTON, lambda _: self.Close())
        sizer.Add(btn_exit, pos=(12, 2))

        # Button Connect
        self.btn_conn = wx.Button(panel, label="Connect")
        # Set enable False by default
        self.btn_conn.Enable(False)
        sizer.Add(self.btn_conn, pos=(12, 3))


        sizer.AddGrowableCol(2)
        panel.SetSizer(sizer)

        # ######################################################################

    def on_close(self):
        """On window Close, Create a file "personnal.py" with configuration var
        """
        epic_key_selection = self.epic_choices[self.combo.GetCurrentSelection()]
        epic_value_selection = globalvar.epic_dict[epic_key_selection]

        config_vars = {"username": self.tc_username.GetValue(),
                       "password": self.tc_passwd.GetValue(),
                       "is_demo": self.chk_demo.GetValue(),
                       "epic": epic_value_selection,
                       "api_key": self.tc_api.GetValue(),
                       "proxies": {"https": self.tc_proxy.GetValue()},
                       "account_nb": self.tc_nb_account.GetValue()
                       }

        with open('personal.py', 'w') as config_file:
            for key, val in config_vars.iteritems():
                if key == 'password':
                    val = val.encode('base64')
                config_file.write("%s = %s\n" %(key, repr(val)))
                personal.__dict__[key] = val
        self.Close()

    def create_default_values (self):
        """ Create default values in "Personal.py" if this file is empty """

        self.default_values = {"username": '',
                               "password": '',
                               "is_demo": True,
                               "epic": 'IX.D.DAX.IMF.IP',
                               "api_key": '',
                               "proxies": {"https": ''},
                               "account_nb": '0'
                               }
        for key in self.default_values:
            if key not in personal.__dict__:
                personal.__dict__[key] = self.default_values[key]

    def check_cgu(self, evt):
        """Function to check / Uncheck the CGU Checkbox and
        Enable/Disable the connect button

        :param evt:
        :return:
        """

        self.btn_conn.Enable(evt.IsChecked())

if __name__ == '__main__':
    app = wx.App()
    LogWindow(None, title="L3 Scalping GUI_LOGIN ONLY")
    app.MainLoop()
