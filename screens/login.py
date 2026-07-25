import time

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 300

BG = (0.07, 0.07, 0.14, 1)
CARD = (0.12, 0.12, 0.20, 1)
INPUT_BG = (0.16, 0.16, 0.26, 1)
ACCENT = (0.42, 0.28, 0.82, 1)
ACCENT_PRESS = (0.34, 0.22, 0.68, 1)
WHITE = (1, 1, 1, 1)
MUTED = (0.5, 0.5, 0.6, 1)
HINT = (0.4, 0.4, 0.5, 1)
ERR = (0.95, 0.3, 0.3, 1)
GOLD = (1.0, 0.78, 0.2, 1)


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
        self.username_input.text = ""
        self.password_input.text = ""
        self.error_label.text = ""
        self._check_lockout()

    def build_ui(self):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical")

        with root.canvas.before:
            Color(*BG)
            self._bg_rect = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._update_bg, size=self._update_bg)

        root.add_widget(Widget(size_hint_y=0.2))

        brand = BoxLayout(orientation="vertical", size_hint_y=0.12, spacing=2)
        brand.add_widget(Label(
            text="SWEET WATERS",
            font_size="30sp", color=WHITE, bold=True,
            size_hint_y=0.6,
        ))
        sub = BoxLayout(size_hint_y=0.4, spacing=4)
        sub.add_widget(Label(text="", size_hint_x=0.2))
        sub.add_widget(Label(
            text="P U B",
            font_size="15sp", color=GOLD,
            size_hint_x=0.6,
        ))
        sub.add_widget(Label(text="", size_hint_x=0.2))
        brand.add_widget(sub)
        root.add_widget(brand)

        root.add_widget(Widget(size_hint_y=0.04))

        card_wrapper = BoxLayout(
            size_hint=(0.82, None), height=320,
            pos_hint={"center_x": 0.5},
        )
        card = BoxLayout(
            orientation="vertical",
            padding=[28, 24, 28, 20],
            spacing=12,
        )
        with card.canvas.before:
            Color(*CARD)
            self._card_rect = RoundedRectangle(
                pos=card.pos, size=card.size, radius=[16],
            )
            Color(*ACCENT[0], ACCENT[1], ACCENT[2], 0.15)
            self._card_border = RoundedRectangle(
                pos=(card.x - 1, card.y - 1),
                size=(card.width + 2, card.height + 2),
                radius=[17],
            )
        card.bind(pos=self._update_card, size=self._update_card)

        card.add_widget(Label(
            text="Staff Login",
            font_size="17sp", color=MUTED,
            size_hint_y=None, height=28,
        ))

        self.username_input = self._make_input("Username", False)
        card.add_widget(self.username_input)

        self.password_input = self._make_input("Password", True)
        card.add_widget(self.password_input)

        self.error_label = Label(
            text="", color=ERR,
            font_size="12sp", size_hint_y=None, height=20,
        )
        card.add_widget(self.error_label)

        self.login_btn = Button(
            text="SIGN IN",
            size_hint=(1, None), height=50,
            background_color=ACCENT, color=WHITE,
            font_size="16sp", bold=True,
            background_normal="",
        )
        self.login_btn.bind(on_release=self.do_login)
        self.login_btn.bind(color_down=lambda *a: None)
        card.add_widget(self.login_btn)

        self.login_hint = Label(
            text="Default: admin / changeme",
            font_size="11sp", color=MUTED,
            size_hint_y=None, height=20,
        )
        card.add_widget(self.login_hint)

        card_wrapper.add_widget(card)
        root.add_widget(card_wrapper)

        root.add_widget(Widget(size_hint_y=0.25))
        self.add_widget(root)

        self.password_input.bind(on_text_validate=lambda x: self.do_login())

    def _make_input(self, hint, is_password):
        box = BoxLayout(orientation="vertical", size_hint_y=None, height=56, spacing=2)
        lbl = Label(
            text=hint.upper(), font_size="10sp", color=MUTED,
            size_hint_y=None, height=14, halign="left",
            padding=[4, 0],
        )
        lbl.bind(size=lbl.setter("text_size"))
        inp = TextInput(
            hint_text=f"Enter {hint.lower()}",
            password=is_password,
            size_hint_y=None, height=36,
            multiline=False, font_size="16sp",
            foreground_color=WHITE,
            cursor_color=ACCENT,
            background_color=INPUT_BG,
            background_normal="",
            hint_text_color=HINT,
            padding=[12, 8, 12, 8],
        )
        box.add_widget(lbl)
        box.add_widget(inp)
        if is_password:
            self._pw_box = box
            self.password_input = inp
        else:
            self._usr_box = box
            self.username_input = inp
        return box

    def _update_bg(self, *args):
        self._bg_rect.pos = self.children[0].pos
        self._bg_rect.size = self.children[0].size

    def _update_card(self, *args):
        card = self.children[0].children[1]
        self._card_rect.pos = card.pos
        self._card_rect.size = card.size
        self._card_border.pos = (card.x - 1, card.y - 1)
        self._card_border.size = (card.width + 2, card.height + 2)

    def _check_lockout(self):
        now = time.time()
        if self._locked_until > now:
            remaining = int(self._locked_until - now)
            self.error_label.text = f"Locked out. Try again in {remaining}s"
            self.username_input.disabled = True
            self.password_input.disabled = True
            self.login_btn.disabled = True
        else:
            self._locked_until = 0
            self.username_input.disabled = False
            self.password_input.disabled = False
            self.login_btn.disabled = False

    def do_login(self, *args):
        self._check_lockout()
        if self._locked_until > time.time():
            return

        username = self.username_input.text.strip()
        password = self.password_input.text
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
                self.username_input.disabled = True
                self.password_input.disabled = True
                self.login_btn.disabled = True
            else:
                self.error_label.text = f"Wrong username or password ({remaining} left)"
            self.password_input.text = ""
