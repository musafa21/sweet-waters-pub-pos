import time

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 300


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
        root = BoxLayout(orientation="vertical", padding=40, spacing=20, size_hint=(1, 1))

        with root.canvas.before:
            Color(0.17, 0.24, 0.31, 1)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._update_bg, size=self._update_bg)

        root.add_widget(Label(
            text="SWEET WATERS PUB",
            font_size="28sp",
            size_hint_y=None, height=60,
            color=(1, 1, 1, 1),
        ))
        root.add_widget(Label(
            text="Staff Login",
            font_size="18sp",
            size_hint_y=None, height=40,
            color=(0.7, 0.7, 0.7, 1),
        ))

        card = BoxLayout(
            orientation="vertical",
            padding=30, spacing=15,
            size_hint=(0.9, None), height=260,
            pos_hint={"center_x": 0.5},
        )
        with card.canvas.before:
            Color(0.1, 0.13, 0.2, 1)
            self._card_bg = Rectangle(pos=card.pos, size=card.size)
        card.bind(pos=self._update_card, size=self._update_card)

        self.username_field = TextInput(
            hint_text="Username",
            size_hint_y=None, height=45,
            multiline=False,
            font_size="16sp",
        )
        card.add_widget(self.username_field)

        self.password_field = TextInput(
            hint_text="Password",
            password=True,
            size_hint_y=None, height=45,
            multiline=False,
            font_size="16sp",
        )
        card.add_widget(self.password_field)

        self.error_label = Label(
            text="",
            color=(0.91, 0.3, 0.24, 1),
            size_hint_y=None, height=25,
            font_size="13sp",
        )
        card.add_widget(self.error_label)

        login_btn = Button(
            text="LOGIN",
            size_hint=(0.8, None), height=50,
            pos_hint={"center_x": 0.5},
            background_color=(0.15, 0.68, 0.38, 1),
            color=(1, 1, 1, 1),
            font_size="16sp",
            bold=True,
        )
        login_btn.bind(on_release=self.do_login)
        card.add_widget(login_btn)

        root.add_widget(card)
        root.add_widget(Label())
        self.add_widget(root)

        self.password_field.bind(on_text_validate=lambda x: self.do_login())

    def _update_bg(self, *args):
        self._bg.pos = self.children[0].pos
        self._bg.size = self.children[0].size

    def _update_card(self, *args):
        card = self.children[0].children[1]
        self._card_bg.pos = card.pos
        self._card_bg.size = card.size

    def _check_lockout(self):
        now = time.time()
        if self._locked_until > now:
            remaining = int(self._locked_until - now)
            self.error_label.text = f"Locked out. Try again in {remaining}s"
            self.username_field.disabled = True
            self.password_field.disabled = True
        else:
            self._locked_until = 0
            self.username_field.disabled = False
            self.password_field.disabled = False

    def do_login(self, *args):
        self._check_lockout()
        if self._locked_until > time.time():
            return

        username = self.username_field.text.strip()
        password = self.password_field.text
        if not username or not password:
            self.error_label.text = "Enter username and password"
            return

        from backend.database import load_json, verify_pw, session
        staff = load_json("staff", {"accounts": {}}).get("accounts", {})
        acc = staff.get(username)
        if acc and verify_pw(password, acc.get("password_hash", "")):
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
                self.username_field.disabled = True
                self.password_field.disabled = True
            else:
                self.error_label.text = f"Invalid credentials ({remaining} tries left)"
            self.password_field.text = ""
