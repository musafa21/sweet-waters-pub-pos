import os
import sys

__version__ = "1.0.0"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from kivy.utils import platform

from screens.login import LoginScreen
from screens.pos import POSScreen
from screens.report import ReportScreen
from screens.debts import DebtScreen
from screens.admin import AdminScreen

Window.size = (400, 700)


class SweetWatersPubApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_user = None
        self.title = "Sweet Waters Pub POS"
        self.sm = None

    def build(self):
        self.sm = ScreenManager()

        screens = [
            ("login", LoginScreen),
            ("pos", POSScreen),
            ("report", ReportScreen),
            ("debts", DebtScreen),
            ("admin", AdminScreen),
        ]
        for name, cls in screens:
            scr = cls(name=name)
            scr.set_app(self)
            self.sm.add_widget(scr)

        self.sm.current = "login"
        return self.sm

    def get_screen(self, name):
        return self.sm.get_screen(name)


if __name__ == "__main__":
    SweetWatersPubApp().run()
