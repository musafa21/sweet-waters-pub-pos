import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window

from screens.login import LoginScreen
from screens.pos import POSScreen
from screens.report import ReportScreen
from screens.debts import DebtScreen
from screens.admin import AdminScreen


class SweetWatersPubApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_user = None
        self.title = "Sweet Waters Pub POS"

    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.theme_style = "Light"

        sm = ScreenManager()

        login = LoginScreen(name="login")
        login.set_app(self)
        sm.add_widget(login)

        pos = POSScreen(name="pos")
        pos.set_app(self)
        sm.add_widget(pos)

        report = ReportScreen(name="report")
        report.set_app(self)
        sm.add_widget(report)

        debts = DebtScreen(name="debts")
        debts.set_app(self)
        sm.add_widget(debts)

        admin = AdminScreen(name="admin")
        admin.set_app(self)
        sm.add_widget(admin)

        sm.current = "login"
        return sm


if __name__ == "__main__":
    SweetWatersPubApp().run()
