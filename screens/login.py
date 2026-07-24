from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None

    def set_app(self, app):
        self.app = app

    def on_enter(self):
        if not self.ids:
            self.build_ui()

    def build_ui(self):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=40, spacing=20)

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

    def do_login(self, *args):
        username = self.username_field.text.strip()
        password = self.password_field.text
        if not username or not password:
            self.error_label.text = "Enter username and password"
            return
        from backend.database import load_json, hash_pw
        staff = load_json("staff", {"accounts": {}}).get("accounts", {})
        acc = staff.get(username)
        if acc and acc.get("password_hash") == hash_pw(password):
            self.app.current_user = {
                "username": username,
                "role": acc.get("role", "cashier"),
                "display_name": acc.get("display_name", username),
            }
            self.error_label.text = ""
            self.manager.current = "pos"
        else:
            self.error_label.text = "Invalid credentials"
            self.password_field.text = ""
