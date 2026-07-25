import re

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line

_MIN_PW_LEN = 6

BG_DARK = (0.06, 0.06, 0.12, 1)
BG_CARD = (0.10, 0.10, 0.18, 1)
BG_INPUT = (0.14, 0.14, 0.24, 1)
ACCENT = (0.36, 0.24, 0.73, 1)
ACCENT_BRIGHT = (0.48, 0.32, 0.92, 1)
SUCCESS = (0.2, 0.78, 0.55, 1)
DANGER = (0.91, 0.27, 0.27, 1)
WARNING = (0.95, 0.65, 0.06, 1)
INFO = (0.14, 0.38, 0.62, 1)
ORANGE = (0.85, 0.42, 0.08, 1)
PURPLE = (0.56, 0.27, 0.68, 1)
TEXT_PRIMARY = (1, 1, 1, 1)
TEXT_SECONDARY = (0.65, 0.65, 0.75, 1)
TEXT_MUTED = (0.45, 0.45, 0.55, 1)
BORDER_COLOR = (0.22, 0.22, 0.32, 1)


def _sanitize_input(text):
    return text.strip().replace("<", "").replace(">", "").replace("{", "").replace("}", "").replace("[", "").replace("]", "").strip()


class AdminScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None

    def set_app(self, app):
        self.app = app

    def on_enter(self):
        from backend.database import session
        if not session.is_logged_in():
            self.manager.current = "login"
            return
        user = session.get_user()
        if user["role"] != "admin":
            self.manager.current = "pos"
            return
        self.build_ui()

    def build_ui(self):
        self.clear_widgets()
        main = BoxLayout(orientation="vertical", size_hint=(1, 1))

        with main.canvas.before:
            Color(*BG_DARK)
            self._main_bg = Rectangle(pos=main.pos, size=main.size)
        main.bind(pos=lambda s, _: self._main_bg.__setattr__("pos", s.pos))
        main.bind(size=lambda s, _: self._main_bg.__setattr__("size", s.size))

        header = BoxLayout(size_hint_y=None, height=52, padding=[14, 0, 14, 0])
        with header.canvas.before:
            Color(*BG_CARD)
            header._bg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda s, _: s._bg.__setattr__("pos", s.pos))
        header.bind(size=lambda s, _: s._bg.__setattr__("size", s.size))
        header.add_widget(Label(
            text="ADMIN TOOLS", font_size="16sp", color=TEXT_PRIMARY, bold=True,
        ))
        main.add_widget(header)

        content = BoxLayout(orientation="vertical", spacing=10, padding=12)
        content.add_widget(Label())
        for text, action, color in [
            ("\U0001f4e6  Manage Inventory", self.manage_inventory, SUCCESS),
            ("\U0001f465  Manage Staff", self.manage_staff, INFO),
            ("\U0001f4e5  Add Stock", self.add_stock, ORANGE),
            ("\U0001f4ca  Stock Taking", self.stock_take, PURPLE),
            ("\U0001f504  Edit Prices", self.edit_prices, WARNING),
            ("\u26a0  Reset All Data", self.reset_data, DANGER),
        ]:
            btn = Button(
                text=text, font_size="14sp", size_hint_y=None, height=52,
                background_color=color, color=TEXT_PRIMARY,
                background_normal="", halign="left", padding=[16, 0],
            )
            btn.bind(on_release=action)
            content.add_widget(btn)
        content.add_widget(Label())
        main.add_widget(content)

        bottom = BoxLayout(size_hint_y=None, height=48, padding=8)
        back_btn = Button(text="Back to POS", font_size="13sp",
                          background_color=BG_INPUT, color=TEXT_SECONDARY,
                          background_normal="")
        back_btn.bind(on_release=lambda x: setattr(self.manager, "current", "pos"))
        bottom.add_widget(back_btn)
        main.add_widget(bottom)
        self.add_widget(main)

    def _log_audit(self, action):
        from backend.database import load_json, save_json, session
        from datetime import datetime
        audit = load_json("audit", {"entries": []})
        user = session.get_user()
        audit.setdefault("entries", []).append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": user["username"] if user else "unknown",
            "action": action,
        })
        if len(audit["entries"]) > 200:
            audit["entries"] = audit["entries"][-200:]
        save_json("audit", audit)

    def _make_input(self, hint, is_password=False, input_filter=None):
        inp = TextInput(
            hint_text=hint, size_hint_y=None, height=42, multiline=False,
            font_size="13sp", password=is_password,
            background_color=BG_INPUT, background_normal="",
            foreground_color=TEXT_PRIMARY, cursor_color=ACCENT_BRIGHT,
            hint_text_color=TEXT_MUTED, padding=[10, 10],
            input_filter=input_filter,
        )
        return inp

    def manage_inventory(self, *args):
        from backend.stock import get_stock_list, set_stock_item

        content = BoxLayout(orientation="vertical", spacing=6, padding=12)

        scroll = ScrollView()
        inv_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=2)
        inv_box.bind(minimum_height=inv_box.setter("height"))
        for name, info in sorted(get_stock_list().items()):
            row = BoxLayout(size_hint_y=None, height=36, padding=[6, 2])
            row.add_widget(Label(text=name, font_size="12sp", halign="left",
                                 text_size=(None, None), size_hint_x=0.45,
                                 color=TEXT_PRIMARY))
            row.add_widget(Label(text=f"KES {info['price']:,.0f}", font_size="12sp",
                                 size_hint_x=0.3, color=ACCENT_BRIGHT))
            row.add_widget(Label(text=info.get("category", ""), font_size="10sp",
                                 size_hint_x=0.25, color=TEXT_MUTED))
            inv_box.add_widget(row)
        scroll.add_widget(inv_box)
        content.add_widget(scroll)

        add_box = BoxLayout(spacing=6, size_hint_y=None, height=46)
        self._inv_name = self._make_input("Name")
        self._inv_price = self._make_input("Price", input_filter="float")
        self._inv_cat = self._make_input("Category")
        add_box.add_widget(self._inv_name)
        add_box.add_widget(self._inv_price)
        add_box.add_widget(self._inv_cat)
        content.add_widget(add_box)

        add_btn = Button(text="+ Add Item", size_hint_y=None, height=40,
                         background_color=SUCCESS, color=TEXT_PRIMARY,
                         background_normal="")
        add_btn.bind(on_release=lambda x: self._do_add_inv())
        content.add_widget(add_btn)

        popup = Popup(title="Inventory", content=content, size_hint=(0.95, 0.85),
                      auto_dismiss=False, background_color=BG_CARD,
                      title_color=TEXT_PRIMARY, separator_color=BORDER_COLOR)
        close_btn = Button(text="Close", size_hint_y=None, height=40,
                           background_color=BG_INPUT, color=TEXT_SECONDARY,
                           background_normal="")
        close_btn.bind(on_release=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()

    def _do_add_inv(self):
        from backend.stock import set_stock_item
        name = _sanitize_input(self._inv_name.text)
        if not name:
            return
        try:
            price = float(self._inv_price.text)
            if price <= 0:
                return
        except ValueError:
            return
        cat = _sanitize_input(self._inv_cat.text) or "Uncategorized"
        set_stock_item(name, price, cat)
        self._log_audit(f"Added/updated inventory: {name}")
        self._inv_name.text = ""
        self._inv_price.text = ""
        self._inv_cat.text = ""

    def manage_staff(self, *args):
        from backend.database import load_json, save_json, hash_pw

        content = BoxLayout(orientation="vertical", spacing=6, padding=12)

        scroll = ScrollView()
        staff_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=2)
        staff_box.bind(minimum_height=staff_box.setter("height"))
        staff = load_json("staff", {"accounts": {}}).get("accounts", {})
        for user, info in sorted(staff.items()):
            row = BoxLayout(size_hint_y=None, height=36, padding=[6, 2])
            row.add_widget(Label(text=user, font_size="12sp", halign="left",
                                 text_size=(None, None), size_hint_x=0.25,
                                 color=TEXT_PRIMARY))
            row.add_widget(Label(text=info.get("display_name", ""), font_size="12sp",
                                 size_hint_x=0.35, color=TEXT_SECONDARY))
            row.add_widget(Label(text=info.get("role", ""), font_size="12sp",
                                 size_hint_x=0.2, color=WARNING))
            staff_box.add_widget(row)
        scroll.add_widget(staff_box)
        content.add_widget(scroll)

        add_box = BoxLayout(spacing=6, size_hint_y=None, height=46)
        self._staff_user = self._make_input("Username")
        self._staff_name = self._make_input("Name")
        self._staff_pw = self._make_input("Password (min 6)", is_password=True)
        add_box.add_widget(self._staff_user)
        add_box.add_widget(self._staff_name)
        add_box.add_widget(self._staff_pw)
        content.add_widget(add_box)

        self._staff_error = Label(text="", font_size="11sp", size_hint_y=None,
                                  height=20, color=DANGER)
        content.add_widget(self._staff_error)

        add_btn = Button(text="+ Add Staff", size_hint_y=None, height=40,
                         background_color=SUCCESS, color=TEXT_PRIMARY,
                         background_normal="")
        add_btn.bind(on_release=lambda x: self._do_add_staff())
        content.add_widget(add_btn)

        popup = Popup(title="Staff Management", content=content,
                      size_hint=(0.95, 0.8), auto_dismiss=False,
                      background_color=BG_CARD, title_color=TEXT_PRIMARY,
                      separator_color=BORDER_COLOR)
        close_btn = Button(text="Close", size_hint_y=None, height=40,
                           background_color=BG_INPUT, color=TEXT_SECONDARY,
                           background_normal="")
        close_btn.bind(on_release=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()

    def _do_add_staff(self):
        from backend.database import load_json, save_json, hash_pw
        user = _sanitize_input(self._staff_user.text)
        pw = self._staff_pw.text
        if not user or not pw:
            self._staff_error.text = "Username and password required"
            return
        if len(pw) < _MIN_PW_LEN:
            self._staff_error.text = f"Password must be at least {_MIN_PW_LEN} chars"
            return
        data = load_json("staff", {"accounts": {}})
        data.setdefault("accounts", {})[user] = {
            "password_hash": hash_pw(pw),
            "role": "cashier",
            "display_name": _sanitize_input(self._staff_name.text) or user,
        }
        save_json("staff", data)
        self._log_audit(f"Added staff: {user}")
        self._staff_error.text = ""
        self._staff_user.text = ""
        self._staff_name.text = ""
        self._staff_pw.text = ""

    def add_stock(self, *args):
        from backend.stock import get_stock_list, load_stock_movements, save_stock_movements
        from backend.database import today_key

        dk = today_key()
        content = BoxLayout(orientation="vertical", spacing=6, padding=12)
        content.add_widget(Label(text=f"Date: {dk}", size_hint_y=None, height=32,
                                 color=TEXT_SECONDARY))

        add_box = BoxLayout(spacing=6, size_hint_y=None, height=46)
        self._stock_item = self._make_input("Item")
        self._stock_qty = self._make_input("Qty", input_filter="int")
        add_box.add_widget(self._stock_item)
        add_box.add_widget(self._stock_qty)
        content.add_widget(add_box)

        self._stock_entries_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=2)
        self._stock_entries_box.bind(minimum_height=self._stock_entries_box.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self._stock_entries_box)
        content.add_widget(scroll)

        add_entry_btn = Button(text="+ Add Entry", size_hint_y=None, height=36,
                               background_color=ORANGE, color=TEXT_PRIMARY,
                               background_normal="")
        add_entry_btn.bind(on_release=lambda x: self._add_stock_entry())
        content.add_widget(add_entry_btn)

        popup = Popup(title="Add Stock", content=content, size_hint=(0.95, 0.8),
                      auto_dismiss=False, background_color=BG_CARD,
                      title_color=TEXT_PRIMARY, separator_color=BORDER_COLOR)

        save_btn = Button(text="Save All", size_hint_y=None, height=40,
                          background_color=SUCCESS, color=TEXT_PRIMARY,
                          background_normal="")
        save_btn.bind(on_release=lambda x: (self._save_stock_entries(dk), popup.dismiss()))
        content.add_widget(save_btn)
        popup.open()

    def _add_stock_entry(self):
        name = _sanitize_input(self._stock_item.text)
        if not name:
            return
        try:
            qty = int(self._stock_qty.text)
            if qty <= 0:
                return
        except ValueError:
            return
        row = BoxLayout(size_hint_y=None, height=30)
        row.add_widget(Label(text=f"{name}: {qty}", font_size="12sp", halign="left",
                             text_size=(None, None), color=TEXT_PRIMARY))
        self._stock_entries_box.add_widget(row)
        self._stock_entries_box.height += 30
        self._stock_item.text = ""
        self._stock_qty.text = ""
        self._last_stock_entries = getattr(self, '_last_stock_entries', [])
        self._last_stock_entries.append({"item": name, "qty": qty})

    def _save_stock_entries(self, dk):
        from backend.stock import load_stock_movements, save_stock_movements
        entries = getattr(self, '_last_stock_entries', [])
        if not entries:
            return
        movements = load_stock_movements()
        movements.setdefault("purchases", {})[dk] = entries
        save_stock_movements(movements)
        self._log_audit(f"Added stock entries for {dk}: {len(entries)} items")
        self._last_stock_entries = []

    def stock_take(self, *args):
        from backend.stock import get_stock_list, calc_remaining_stock, load_stock_movements, save_stock_movements
        from backend.database import today_key

        dk = today_key()
        remaining = calc_remaining_stock(dk)
        content = BoxLayout(orientation="vertical", spacing=4, padding=12)
        content.add_widget(Label(text="Enter closing stock counts",
                                 size_hint_y=None, height=28, color=TEXT_SECONDARY))

        self._take_fields = {}
        scroll = ScrollView()
        fields_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=2)
        fields_box.bind(minimum_height=fields_box.setter("height"))
        for name in sorted(get_stock_list().keys()):
            exp = remaining.get(name, 0)
            row = BoxLayout(size_hint_y=None, height=38, spacing=4)
            row.add_widget(Label(text=name, font_size="11sp", halign="left",
                                 text_size=(None, None), size_hint_x=0.55,
                                 color=TEXT_PRIMARY))
            field = TextInput(
                hint_text=f"exp: {exp}", input_filter="int",
                font_size="13sp", multiline=False, size_hint_x=0.3,
                background_color=BG_INPUT, background_normal="",
                foreground_color=TEXT_PRIMARY, cursor_color=ACCENT_BRIGHT,
                hint_text_color=TEXT_MUTED, padding=[8, 8],
            )
            self._take_fields[name] = field
            row.add_widget(field)
            fields_box.add_widget(row)
        scroll.add_widget(fields_box)
        content.add_widget(scroll)

        popup = Popup(title=f"Stock Taking - {dk}", content=content,
                      size_hint=(0.95, 0.85), auto_dismiss=False,
                      background_color=BG_CARD, title_color=TEXT_PRIMARY,
                      separator_color=BORDER_COLOR)
        save_btn = Button(text="Save", size_hint_y=None, height=40,
                          background_color=SUCCESS, color=TEXT_PRIMARY,
                          background_normal="")
        save_btn.bind(on_release=lambda x: (self._save_stock_take(dk), popup.dismiss()))
        cancel_btn = Button(text="Cancel", size_hint_y=None, height=40,
                            background_color=BG_INPUT, color=TEXT_SECONDARY,
                            background_normal="")
        cancel_btn.bind(on_release=popup.dismiss)
        btn_box = BoxLayout(spacing=6, size_hint_y=None, height=44)
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(save_btn)
        content.add_widget(btn_box)
        popup.open()

    def _save_stock_take(self, dk):
        from backend.stock import load_stock_movements, save_stock_movements
        closing = {}
        for name, field in self._take_fields.items():
            try:
                closing[name] = int(field.text)
            except (ValueError, TypeError):
                pass
        movements = load_stock_movements()
        movements.setdefault("closing", {})[dk] = closing
        save_stock_movements(movements)
        self._log_audit(f"Saved stock take for {dk}")

    def edit_prices(self, *args):
        from backend.stock import get_stock_list, set_stock_item

        content = BoxLayout(orientation="vertical", spacing=4, padding=12)
        content.add_widget(Label(text="Enter new prices", size_hint_y=None,
                                 height=28, color=TEXT_SECONDARY))

        self._price_fields = {}
        scroll = ScrollView()
        prices_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=2)
        prices_box.bind(minimum_height=prices_box.setter("height"))
        for name, info in sorted(get_stock_list().items()):
            row = BoxLayout(size_hint_y=None, height=38, spacing=4)
            row.add_widget(Label(text=name, font_size="11sp", halign="left",
                                 text_size=(None, None), size_hint_x=0.55,
                                 color=TEXT_PRIMARY))
            field = TextInput(
                text=str(int(info["price"])), input_filter="float",
                font_size="13sp", multiline=False, size_hint_x=0.3,
                background_color=BG_INPUT, background_normal="",
                foreground_color=TEXT_PRIMARY, cursor_color=ACCENT_BRIGHT,
                padding=[8, 8],
            )
            self._price_fields[name] = field
            row.add_widget(field)
            prices_box.add_widget(row)
        scroll.add_widget(prices_box)
        content.add_widget(scroll)

        popup = Popup(title="Edit Prices", content=content, size_hint=(0.95, 0.85),
                      auto_dismiss=False, background_color=BG_CARD,
                      title_color=TEXT_PRIMARY, separator_color=BORDER_COLOR)
        save_btn = Button(text="Save", size_hint_y=None, height=40,
                          background_color=SUCCESS, color=TEXT_PRIMARY,
                          background_normal="")
        save_btn.bind(on_release=lambda x: (self._save_prices(), popup.dismiss()))
        cancel_btn = Button(text="Cancel", size_hint_y=None, height=40,
                            background_color=BG_INPUT, color=TEXT_SECONDARY,
                            background_normal="")
        cancel_btn.bind(on_release=popup.dismiss)
        btn_box = BoxLayout(spacing=6, size_hint_y=None, height=44)
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(save_btn)
        content.add_widget(btn_box)
        popup.open()

    def _save_prices(self):
        from backend.stock import set_stock_item
        count = 0
        for name, field in self._price_fields.items():
            try:
                new_price = float(field.text)
                if new_price > 0:
                    set_stock_item(name, new_price)
                    count += 1
            except (ValueError, TypeError):
                pass
        self._log_audit(f"Updated {count} item prices")

    def reset_data(self, *args):
        content = BoxLayout(orientation="vertical", spacing=12, padding=20)
        content.add_widget(Label(
            text="This will delete ALL data.\nThis cannot be undone!",
            font_size="14sp", halign="center", color=DANGER,
        ))
        content.add_widget(Label(
            text="Enter admin password to confirm:",
            font_size="13sp", halign="center", color=TEXT_SECONDARY,
        ))
        self._reset_pw = TextInput(
            hint_text="Admin password", password=True,
            size_hint_y=None, height=44, multiline=False, font_size="14sp",
            background_color=BG_INPUT, background_normal="",
            foreground_color=TEXT_PRIMARY, cursor_color=ACCENT_BRIGHT,
            hint_text_color=TEXT_MUTED, padding=[12, 10],
        )
        content.add_widget(self._reset_pw)
        self._reset_error = Label(
            text="", font_size="11sp", size_hint_y=None, height=20, color=DANGER,
        )
        content.add_widget(self._reset_error)
        btn_box = BoxLayout(spacing=10, size_hint_y=None, height=48)
        cancel_btn = Button(text="Cancel", background_color=BG_INPUT,
                            color=TEXT_SECONDARY, background_normal="")
        reset_btn = Button(text="RESET", background_color=DANGER,
                           color=TEXT_PRIMARY, background_normal="")
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(reset_btn)
        content.add_widget(btn_box)

        popup = Popup(title="Reset All Data?", content=content, size_hint=(0.85, 0.6),
                      auto_dismiss=False, background_color=BG_CARD,
                      title_color=DANGER, separator_color=BORDER_COLOR)
        cancel_btn.bind(on_release=popup.dismiss)
        reset_btn.bind(on_release=lambda x: self._verify_and_reset(popup))
        popup.open()

    def _verify_and_reset(self, popup):
        from backend.database import load_json, verify_pw, session
        pw = self._reset_pw.text
        user = session.get_user()
        if not user:
            return
        staff = load_json("staff", {"accounts": {}}).get("accounts", {})
        acc = staff.get(user["username"])
        if not acc or not verify_pw(pw, acc.get("password_hash", "")):
            self._reset_error.text = "Incorrect password"
            return
        popup.dismiss()
        self._log_audit("RESET ALL DATA")
        self._do_reset()

    def _do_reset(self):
        from backend.database import save_json, hash_pw, DATA_DIR
        from backend.stock import init_stock
        import os
        import glob as glob_mod
        for f in glob_mod.glob(os.path.join(DATA_DIR, "*.json")):
            os.remove(f)
        save_json("staff", {
            "accounts": {
                "admin": {
                    "password_hash": hash_pw("CHANGE_ME_NOW"),
                    "role": "admin",
                    "display_name": "Administrator",
                }
            }
        })
        save_json("audit", {"entries": []})
        init_stock()
        self.build_ui()
