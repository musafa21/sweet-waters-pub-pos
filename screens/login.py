from kivy.uix.screenmanager import Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.card import MDCard


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
        root = MDBoxLayout(
            orientation="vertical",
            padding=40,
            spacing=20,
            md_bg_color=[0.17, 0.24, 0.31, 1],
        )
        root.add_widget(MDLabel(
            text="SWEET WATERS PUB",
            font_style="H4",
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            size_hint_y=None,
            height=60,
        ))
        root.add_widget(MDLabel(
            text="Staff Login",
            font_style="H6",
            halign="center",
            theme_text_color="Custom",
            text_color=[0.74, 0.76, 0.78, 1],
            size_hint_y=None,
            height=40,
        ))

        card = MDCard(
            orientation="vertical",
            padding=30,
            spacing=15,
            size_hint=[0.9, None],
            height=280,
            pos_hint={"center_x": 0.5},
            elevation=8,
        )

        self.username_field = MDTextField(
            hint_text="Username",
            icon_left="account",
            size_hint_y=None,
            height=50,
        )
        card.add_widget(self.username_field)

        self.password_field = MDTextField(
            hint_text="Password",
            icon_left="lock",
            password=True,
            size_hint_y=None,
            height=50,
        )
        card.add_widget(self.password_field)

        self.error_label = MDLabel(
            text="",
            theme_text_color="Error",
            halign="center",
            size_hint_y=None,
            height=30,
        )
        card.add_widget(self.error_label)

        login_btn = MDRaisedButton(
            text="LOGIN",
            pos_hint={"center_x": 0.5},
            size_hint=[0.8, None],
            height=50,
            md_bg_color=[0.15, 0.68, 0.38, 1],
            on_release=self.do_login,
        )
        card.add_widget(login_btn)

        root.add_widget(card)
        root.add_widget(MDLabel())  # spacer
        self.add_widget(root)

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
