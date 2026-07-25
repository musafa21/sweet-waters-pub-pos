import os
import sys
import traceback

__version__ = "3.1.0"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _write_crash_log(exc):
    try:
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash.log")
        with open(log_path, "a") as f:
            f.write(f"\n{'='*60}\n")
            import datetime
            f.write(f"CRASH: {datetime.datetime.now()}\n")
            f.write(f"Version: {__version__}\n")
            traceback.print_exc(file=f)
        print(f"[CRASH] {exc} — see crash.log")
    except Exception:
        pass


try:
    from kivy.app import App
    from kivy.uix.screenmanager import ScreenManager
    from kivy.core.window import Window
    from kivy.utils import platform
    from kivy.clock import Clock
    from kivy.core.window import Window as _Win
except Exception as e:
    _write_crash_log(e)
    raise


class SweetWatersPubApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_user = None
        self.title = "Sweet Waters Pub POS"
        self.sm = None
        self._session_check = None

    def build(self):
        from backend.database import init_data_dir, seed_default_staff
        init_data_dir()
        seed_default_staff()

        if platform != "android":
            Window.size = (400, 700)

        from screens.login import LoginScreen
        from screens.pos import POSScreen
        from screens.report import ReportScreen
        from screens.debts import DebtScreen
        from screens.admin import AdminScreen

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

        self._session_check = Clock.schedule_interval(self._check_session, 30)

        return self.sm

    def _check_session(self, dt):
        from backend.database import session
        if self.sm.current == "login":
            return
        if not session.is_logged_in():
            session.clear_user()
            self.current_user = None
            self.sm.current = "login"

    def get_screen(self, name):
        return self.sm.get_screen(name)


if __name__ == "__main__":
    try:
        SweetWatersPubApp().run()
    except Exception as e:
        _write_crash_log(e)
        raise
