import time

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.clock import Clock

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 300

BG_DARK = (0.06, 0.06, 0.12, 1)
BG_CARD = (0.10, 0.10, 0.18, 1)
BG_INPUT = (0.14, 0.14, 0.24, 1)
ACCENT = (0.36, 0.24, 0.73, 1)
ACCENT_BRIGHT = (0.48, 0.32, 0.92, 1)
TEXT_PRIMARY = (1, 1, 1, 1)
TEXT_SECONDARY = (0.65, 0.65, 0.75, 1)
TEXT_MUTED = (0.45, 0.45, 0.55, 1)
ERR_COLOR = (0.91, 0.27, 0.27, 1)
SUCCESS_COLOR = (0.2, 0.78, 0.55, 1)


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self._attempts = 0
        self._locked_until = 0

    def set_app(self, app):
        self.app = app

    def on_enter(self):
        if not self.ids:
            self.build_ui()
        self.username_field.text = ""
        self.password_field.text = ""
        self.error_label.text = ""
        self._check_lockout()

    def build_ui(self):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", size_hint=(1, 1))

        with root.canvas.before:
            Color(*BG_DARK)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._update_bg, size=self._update_bg)

        root.add_widget(Widget(size_hint_y=0.15))

        header_box = BoxLayout(orientation="vertical", size_hint_y=0.12, spacing=4)
        header_box.add_widget(Label(
            text="SWEET WATERS",
            font_size="32sp",
            color=TEXT_PRIMARY,
            bold=True,
        ))
        header_box.add_widget(Label(
            text="P U B",
            font_size="16sp",
            color=ACCENT_BRIGHT,
            letterSpacing=0.3,
        ))
        root.add_widget(header_box)

        root.add_widget(Widget(size_hint_y=0.06))

        card = BoxLayout(
            orientation="vertical",
            padding=[32, 24, 32, 24],
            spacing=16,
            size_hint=(0.85, None), height=280,
            pos_hint={"center_x": 0.5},
        )
        with card.canvas.before:
            Color(*BG_CARD)
            self._card_bg = Rectangle(pos=card.pos, size=card.size)
            Color(0.36, 0.24, 0.73, 0.3)
            self._card_border = Line(
                rounded_rectangle=(card.x, card.y, card.width, card.height, 12),
                width=1,
            )
        card.bind(pos=self._update_card, size=self._update_card)

        card.add_widget(Label(
            text="Staff Login",
            font_size="18sp",
            color=TEXT_SECONDARY,
            size_hint_y=None, height=28,
        ))

        self.username_field = self._make_input("Username", False)
        card.add_widget(self.username_field)

        self.password_field = self._make_input("Password", True)
        card.add_widget(self.password_field)

        self.error_label = Label(
            text="",
            color=ERR_COLOR,
            size_hint_y=None, height=22,
            font_size="12sp",
        )
        card.add_widget(self.error_label)

        login_btn = Button(
            text="S I G N   I N",
            size_hint=(0.85, None), height=48,
            pos_hint={"center_x": 0.5},
            background_color=ACCENT,
            color=TEXT_PRIMARY,
            font_size="14sp",
            bold=True,
        )
        with login_btn.canvas.before:
            Color(*ACCENT)
            self._btn_bg = Rectangle(pos=login_btn.pos, size=login_btn.size)
        login_btn.bind(pos=self._update_btn_bg, size=self._update_btn_bg)
        login_btn.bind(on_release=self.do_login)
        card.add_widget(login_btn)

        root.add_widget(card)
        root.add_widget(Widget(size_hint_y=0.2))
        self.add_widget(root)

        self.password_field.bind(on_text_validate=lambda x: self.do_login())

    def _make_input(self, hint, is_password):
        box = BoxLayout(orientation="vertical", size_hint_y=None, height=52, spacing=2)
        lbl = Label(
            text=hint,
            font_size="11sp",
            color=TEXT_MUTED,
            size_hint_y=None, height=16,
            halign="left",
            padding=[4, 0],
        )
        lbl.bind(size=lbl.setter("text_size"))
        inp = TextInput(
            hint_text=hint,
            password=is_password,
            size_hint_y=None, height=34,
            multiline=False,
            font_size="15sp",
            foreground_color=TEXT_PRIMARY,
            cursor_color=ACCENT_BRIGHT,
            background_color=BG_INPUT,
            background_normal="",
            hint_text_color=TEXT_MUTED,
            padding=[12, 8, 12, 8],
        )
        box.add_widget(lbl)
        box.add_widget(inp)
        if is_password:
            self.password_field = inp
        else:
            self.username_field = inp
        return box

    def _update_bg(self, *args):
        self._bg.pos = self.children[0].pos
        self._bg.size = self.children[0].size

    def _update_card(self, *args):
        card = self.children[0].children[1]
        self._card_bg.pos = card.pos
        self._card_bg.size = card.size
        self._card_border.rounded_rectangle = (
            card.x, card.y, card.width, card.height, 12
        )

    def _update_btn_bg(self, *args):
        btn = self.children[0].children[1].children[-1]
        self._btn_bg.pos = btn.pos
        self._btn_bg.size = btn.size

    def _check_lockout(self):
        now = time.time()
        if self._locked_until > now:
            remaining = int(self._locked_until - now)
            self.error_label.text = f"Locked out — try again in {remaining}s"
            self.username_field.children[0].disabled = True
            self.password_field.children[0].disabled = True
        else:
            self._locked_until = 0
            self.username_field.children[0].disabled = False
            self.password_field.children[0].disabled = False

    def do_login(self, *args):
        self._check_lockout()
        if self._locked_until > time.time():
            return

        username = self.username_field.children[0].text.strip()
        password = self.password_field.children[0].text
        if not username or not password:
            self.error_label.text = "Enter username and password"
            return

        from backend.database import load_json, verify_pw, migrate_pw, session
        staff = load_json("staff", {"accounts": {}}).get("accounts", {})
        acc = staff.get(username)
        if acc and verify_pw(password, acc.get("password_hash", "")):
            migrate_pw(password, acc.get("password_hash", ""), username)
            self._attempts = 0
            session.set_user({
                "username": username,
                "role": acc.get("role", "cashier"),
                "display_name": acc.get("display_name", username),
            })
            self.app.current_user = session.get_user()
            self.error_label.text = ""
            self.manager.current = "pos"
        else:
            self._attempts += 1
            remaining = MAX_ATTEMPTS - self._attempts
            if self._attempts >= MAX_ATTEMPTS:
                self._locked_until = time.time() + LOCKOUT_SECONDS
                self.error_label.text = "Too many attempts. Locked for 5 min."
                self.username_field.children[0].disabled = True
                self.password_field.children[0].disabled = True
            else:
                self.error_label.text = f"Invalid credentials ({remaining} left)"
            self.password_field.children[0].text = ""
