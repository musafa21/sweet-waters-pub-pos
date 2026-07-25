import time
import os

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 300

BG = (0.07, 0.07, 0.14, 1)
CARD = (0.12, 0.12, 0.20, 1)
INPUT_BG = (0.16, 0.16, 0.26, 1)
ACCENT = (0.42, 0.28, 0.82, 1)
WHITE = (1, 1, 1, 1)
MUTED = (0.5, 0.5, 0.6, 1)
HINT = (0.4, 0.4, 0.5, 1)
ERR = (0.95, 0.3, 0.3, 1)
GOLD = (1.0, 0.78, 0.2, 1)
SUCCESS = (0.2, 0.78, 0.55, 1)
SURFACE = (0.14, 0.14, 0.24, 1)


def _hint_shown_file():
    from backend.database import DATA_DIR, init_data_dir
    if DATA_DIR is None:
        init_data_dir()
    from backend.database import DATA_DIR
    return os.path.join(DATA_DIR, ".hint_seen")


def _mark_hint_seen():
    try:
        with open(_hint_shown_file(), "w") as f:
            f.write("1")
    except Exception:
        pass


def _was_hint_seen():
    return os.path.exists(_hint_shown_file())


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self._attempts = 0
        self._locked_until = 0
        self._pin_mode = False
        self._lockout_timer = None

    def set_app(self, app):
        self.app = app

    def on_enter(self):
        if not self.ids:
            self.build_ui()
        self.username_input.text = ""
        self.password_input.text = ""
        self.error_label.text = ""
        self._set_pin_fields("")
        self._check_lockout()
        if _was_hint_seen():
            self.login_hint.opacity = 0
            self.login_hint.size_hint_y = None
            self.login_hint.height = 0

    def on_leave(self):
        if self._lockout_timer:
            self._lockout_timer.cancel()
            self._lockout_timer = None

    def build_ui(self):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical")

        with root.canvas.before:
            Color(*BG)
            self._bg_rect = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._update_bg, size=self._update_bg)

        root.add_widget(Widget(size_hint_y=0.15))

        brand = BoxLayout(orientation="vertical", size_hint_y=0.10, spacing=2)
        brand.add_widget(Label(
            text="SWEET WATERS",
            font_size="28sp", color=WHITE, bold=True, size_hint_y=0.6,
        ))
        sub = BoxLayout(size_hint_y=0.4, spacing=4)
        sub.add_widget(Label(text="", size_hint_x=0.2))
        sub.add_widget(Label(text="P U B", font_size="14sp", color=GOLD, size_hint_x=0.6))
        sub.add_widget(Label(text="", size_hint_x=0.2))
        brand.add_widget(sub)
        root.add_widget(brand)

        root.add_widget(Widget(size_hint_y=0.03))

        card_wrapper = BoxLayout(size_hint=(0.82, None), height=380, pos_hint={"center_x": 0.5})
        self._card = BoxLayout(orientation="vertical", padding=[28, 20, 28, 16], spacing=10)
        with self._card.canvas.before:
            Color(*CARD)
            self._card_rect = RoundedRectangle(pos=self._card.pos, size=self._card.size, radius=[16])
        self._card.bind(pos=self._update_card, size=self._update_card)

        self._mode_toggle = Button(
            text="Use PIN Login", font_size="11sp", size_hint_y=None, height=28,
            background_color=SURFACE, color=MUTED, background_normal="",
        )
        self._mode_toggle.bind(on_release=self._toggle_mode)
        self._card.add_widget(self._mode_toggle)

        self._pw_fields_box = BoxLayout(orientation="vertical", spacing=8)
        self.username_input = self._make_input("Username", False)
        self._pw_fields_box.add_widget(self.username_input)
        self.password_input = self._make_input("Password", True)
        self._pw_fields_box.add_widget(self.password_input)
        self._card.add_widget(self._pw_fields_box)

        self._pin_fields_box = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None, height=140)
        pin_label = Label(text="Enter 4-digit PIN", font_size="13sp", color=MUTED, size_hint_y=None, height=24)
        self._pin_fields_box.add_widget(pin_label)

        pin_row = BoxLayout(spacing=10, size_hint_y=None, height=56)
        self._pin_fields = []
        for i in range(4):
            inp = TextInput(
                hint_text=str(i + 1), password=True,
                size_hint_x=0.22, size_hint_y=None, height=56,
                multiline=False, font_size="24sp", halign="center",
                foreground_color=WHITE, cursor_color=ACCENT,
                background_color=INPUT_BG, background_normal="",
                hint_text_color=HINT, padding=[4, 8],
                input_filter="int", max_length=1,
            )
            inp._idx = i
            inp.bind(text=self._on_pin_digit)
            inp.bind(focus=lambda instance, f, idx=i: None)
            self._pin_fields.append(inp)
            pin_row.add_widget(inp)
        self._pin_fields_box.add_widget(pin_row)

        self._pin_error = Label(text="", font_size="11sp", color=ERR, size_hint_y=None, height=18)
        self._pin_fields_box.add_widget(self._pin_error)
        self._card.add_widget(self._pin_fields_box)

        self.error_label = Label(text="", color=ERR, font_size="12sp", size_hint_y=None, height=18)
        self._card.add_widget(self.error_label)

        self.login_btn = Button(
            text="SIGN IN", size_hint=(1, None), height=48,
            background_color=ACCENT, color=WHITE,
            font_size="15sp", bold=True, background_normal="",
        )
        self.login_btn.bind(on_release=self.do_login)
        self._card.add_widget(self.login_btn)

        self.login_hint = Label(
            text="Default: admin / changeme", font_size="10sp", color=MUTED,
            size_hint_y=None, height=18,
        )
        self._card.add_widget(self.login_hint)

        card_wrapper.add_widget(self._card)
        root.add_widget(card_wrapper)

        root.add_widget(Widget(size_hint_y=0.22))
        self.add_widget(root)

        self.password_input.bind(on_text_validate=lambda x: self.do_login())
        self._pin_fields_box.opacity = 0
        self._pin_fields_box.size_hint_y = 0
        self._pin_fields_box.height = 0

    def _make_input(self, hint, is_password):
        box = BoxLayout(orientation="vertical", size_hint_y=None, height=52, spacing=2)
        lbl = Label(
            text=hint.upper(), font_size="10sp", color=MUTED,
            size_hint_y=None, height=14, halign="left", padding=[4, 0],
        )
        lbl.bind(size=lbl.setter("text_size"))
        inp = TextInput(
            hint_text=f"Enter {hint.lower()}", password=is_password,
            size_hint_y=None, height=34, multiline=False, font_size="16sp",
            foreground_color=WHITE, cursor_color=ACCENT,
            background_color=INPUT_BG, background_normal="",
            hint_text_color=HINT, padding=[12, 8, 12, 8],
        )
        box.add_widget(lbl)
        box.add_widget(inp)
        if is_password:
            self.password_input = inp
        else:
            self.username_input = inp
        return box

    def _toggle_mode(self, *args):
        from backend.database import haptic_click
        haptic_click()
        self._pin_mode = not self._pin_mode
        if self._pin_mode:
            self._mode_toggle.text = "Use Password Login"
            self._pw_fields_box.opacity = 0
            self._pw_fields_box.size_hint_y = 0
            self._pw_fields_box.height = 0
            self._pin_fields_box.opacity = 1
            self._pin_fields_box.size_hint_y = None
            self._pin_fields_box.height = 140
            self.login_btn.text = "SIGN IN WITH PIN"
            self.error_label.text = ""
            if self._pin_fields:
                self._pin_fields[0].focus = True
        else:
            self._mode_toggle.text = "Use PIN Login"
            self._pw_fields_box.opacity = 1
            self._pw_fields_box.size_hint_y = None
            self._pw_fields_box.height = 120
            self._pin_fields_box.opacity = 0
            self._pin_fields_box.size_hint_y = 0
            self._pin_fields_box.height = 0
            self.login_btn.text = "SIGN IN"
            self._pin_error.text = ""
            self._set_pin_fields("")

    def _set_pin_fields(self, val):
        for f in self._pin_fields:
            f.text = val

    def _on_pin_digit(self, instance, value):
        idx = instance._idx
        if value:
            if idx < 3:
                self._pin_fields[idx + 1].focus = True
            pin = "".join(f.text for f in self._pin_fields)
            if len(pin) == 4 and pin == "".join(f.text for f in self._pin_fields):
                self.do_login()
        else:
            if idx > 0:
                Clock.schedule_once(lambda dt: self._pin_fields[idx - 1].focus.__setattr__('focus', True), 0.05)

    def _update_bg(self, *args):
        self._bg_rect.pos = self.children[0].pos
        self._bg_rect.size = self.children[0].size

    def _update_card(self, *args):
        self._card_rect.pos = self._card.pos
        self._card_rect.size = self._card.size

    def _check_lockout(self):
        now = time.time()
        if self._locked_until > now:
            remaining = int(self._locked_until - now)
            self.error_label.text = f"Locked out. Try again in {remaining}s"
            self.username_input.disabled = True
            self.password_input.disabled = True
            self.login_btn.disabled = True
            self._start_lockout_tick(remaining)
        else:
            self._locked_until = 0
            self.username_input.disabled = False
            self.password_input.disabled = False
            self.login_btn.disabled = False
            if self._lockout_timer:
                self._lockout_timer.cancel()
                self._lockout_timer = None

    def _start_lockout_tick(self, remaining):
        if self._lockout_timer:
            self._lockout_timer.cancel()
        self._lockout_remaining = remaining

        def _tick(dt):
            self._lockout_remaining -= 1
            if self._lockout_remaining <= 0:
                self._locked_until = 0
                self.error_label.text = ""
                self.username_input.disabled = False
                self.password_input.disabled = False
                self.login_btn.disabled = False
                if self._lockout_timer:
                    self._lockout_timer.cancel()
                    self._lockout_timer = None
                return
            self.error_label.text = f"Locked out. Try again in {self._lockout_remaining}s"

        self._lockout_timer = Clock.schedule_interval(_tick, 1)

    def do_login(self, *args):
        from backend.database import haptic_click
        haptic_click()
        self._check_lockout()
        if self._locked_until > time.time():
            return

        if self._pin_mode:
            pin = "".join(f.text for f in self._pin_fields)
            if len(pin) != 4:
                self._pin_error.text = "Enter 4 digits"
                return
            self._pin_error.text = ""
            from backend.database import load_json, decrypt_pin
            staff = load_json("staff", {"accounts": {}}).get("accounts", {})
            username = None
            for uname, acc in staff.items():
                stored_pin = acc.get("pin", "")
                if stored_pin and decrypt_pin(stored_pin) == pin:
                    username = uname
                    break
            if username is None:
                self._attempts += 1
                remaining = MAX_ATTEMPTS - self._attempts
                if self._attempts >= MAX_ATTEMPTS:
                    self._locked_until = time.time() + LOCKOUT_SECONDS
                    self._pin_error.text = "Too many attempts. Locked 5 min."
                    self.login_btn.disabled = True
                    self._start_lockout_tick(LOCKOUT_SECONDS)
                else:
                    self._pin_error.text = f"Wrong PIN ({remaining} left)"
                self._set_pin_fields("")
                return
            acc = staff[username]
            self._do_auth(username, acc)
        else:
            username = self.username_input.text.strip()
            password = self.password_input.text
            if not username or not password:
                self.error_label.text = "Enter username and password"
                return
            from backend.database import load_json
            staff = load_json("staff", {"accounts": {}}).get("accounts", {})
            acc = staff.get(username)
            if acc:
                from backend.database import verify_pw
                if verify_pw(password, acc.get("password_hash", "")):
                    from backend.database import migrate_pw
                    migrate_pw(password, acc.get("password_hash", ""), username)
                    self._do_auth(username, acc)
                    return
            self._attempts += 1
            remaining = MAX_ATTEMPTS - self._attempts
            if self._attempts >= MAX_ATTEMPTS:
                self._locked_until = time.time() + LOCKOUT_SECONDS
                self.error_label.text = "Too many attempts. Locked 5 min."
                self.username_input.disabled = True
                self.password_input.disabled = True
                self.login_btn.disabled = True
                self._start_lockout_tick(LOCKOUT_SECONDS)
            else:
                self.error_label.text = f"Wrong username or password ({remaining} left)"
            self.password_input.text = ""

    def _do_auth(self, username, acc):
        from backend.database import session
        self._attempts = 0
        session.set_user({
            "username": username,
            "role": acc.get("role", "cashier"),
            "display_name": acc.get("display_name", username),
        })
        self.app.current_user = session.get_user()
        self.error_label.text = ""
        _mark_hint_seen()
        self.manager.current = "pos"
