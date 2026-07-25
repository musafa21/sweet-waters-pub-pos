import os
import sys
import time
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
        self._warned_timeout = False

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
            self._warned_timeout = False
            return
        if not session.is_logged_in():
            session.clear_user()
            self.current_user = None
            self._warned_timeout = False
            self.sm.current = "login"
            return
        remaining = session.TIMEOUT_SECONDS - (time.time() - session._last_activity)
        if 0 < remaining <= 60 and not self._warned_timeout:
            self._warned_timeout = True
            self._show_timeout_warning(int(remaining))
        elif remaining > 60:
            self._warned_timeout = False

    def _show_timeout_warning(self, remaining):
        from kivy.uix.popup import Popup
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        from backend.database import session
        content = BoxLayout(orientation="vertical", spacing=12, padding=20)
        content.add_widget(Label(
            text=f"Session expires in {remaining}s.\nTap OK to stay logged in.",
            font_size="14sp", halign="center", color=(1, 1, 1, 1),
        ))
        popup = Popup(
            title="Session Timeout", content=content,
            size_hint=(0.8, 0.35), auto_dismiss=True,
            background_color=(0.12, 0.12, 0.20, 1),
            title_color=(1, 1, 1, 1),
            separator_color=(0.2, 0.2, 0.3, 1),
        )
        popup.bind(on_dismiss=lambda x: session.touch())
        popup.open()

    def get_screen(self, name):
        return self.sm.get_screen(name)


if __name__ == "__main__":
    try:
        SweetWatersPubApp().run()
    except Exception as e:
        _write_crash_log(e)
        raise
