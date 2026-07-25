import re
import os

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle

_MIN_PW_LEN = 6

BG = (0.07, 0.07, 0.14, 1)
CARD = (0.12, 0.12, 0.20, 1)
SURFACE = (0.14, 0.14, 0.24, 1)
INPUT_BG = (0.16, 0.16, 0.26, 1)
ACCENT = (0.42, 0.28, 0.82, 1)
SUCCESS = (0.2, 0.78, 0.55, 1)
DANGER = (0.95, 0.3, 0.3, 1)
WARNING = (1.0, 0.65, 0.1, 1)
INFO = (0.18, 0.4, 0.7, 1)
ORANGE = (0.88, 0.45, 0.1, 1)
PURPLE = (0.58, 0.28, 0.72, 1)
WHITE = (1, 1, 1, 1)
MUTED = (0.5, 0.5, 0.6, 1)
HINT = (0.4, 0.4, 0.5, 1)
DIVIDER = (0.2, 0.2, 0.3, 1)


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
        main = BoxLayout(orientation="vertical")

        with main.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=main.pos, size=main.size)
        main.bind(pos=lambda s, _: self._bg.__setattr__("pos", s.pos))
        main.bind(size=lambda s, _: self._bg.__setattr__("size", s.size))

        header = BoxLayout(size_hint_y=None, height=56, padding=[16, 0, 16, 0])
        with header.canvas.before:
            Color(*CARD)
            header._bg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda s, _: s._bg.__setattr__("pos", s.pos))
        header.bind(size=lambda s, _: s._bg.__setattr__("size", s.size))
        header.add_widget(Label(
            text="\u2699\ufe0f  Admin Tools", font_size="18sp", color=WHITE, bold=True,
        ))
        main.add_widget(header)

        scroll = ScrollView(bar_width=4, bar_color=(0.3, 0.3, 0.4, 0.3))
        btn_box = BoxLayout(
            orientation="vertical", size_hint_y=None,
            spacing=8, padding=[16, 14, 16, 14],
        )
        btn_box.bind(minimum_height=btn_box.setter("height"))

        actions = [
            ("\U0001f4e6  Manage Inventory", self.manage_inventory, SUCCESS),
            ("\U0001f465  Manage Staff", self.manage_staff, INFO),
            ("\U0001f4e5  Add Stock", self.add_stock, ORANGE),
            ("\U0001f4ca  Stock Taking", self.stock_take, PURPLE),
            ("\U0001f504  Edit Prices", self.edit_prices, WARNING),
            ("\U0001f4be  Export CSV Backup", self.export_backup, (0.2, 0.6, 0.8, 1)),
            ("\u26a0\ufe0f  Reset All Data", self.reset_data, DANGER),
        ]
        for text, action, color in actions:
            btn = Button(
                text=text, font_size="14sp", size_hint_y=None, height=54,
                background_color=color, color=WHITE,
                background_normal="", halign="left", padding=[14, 0],
            )
            btn.bind(on_release=lambda x, a=action: (self._haptic(), a()))
            btn_box.add_widget(btn)

        btn_box.add_widget(Widget(size_hint_y=None, height=8))
        scroll.add_widget(btn_box)
        main.add_widget(scroll)

        bottom = BoxLayout(size_hint_y=None, height=56, padding=8)
        back_btn = Button(
            text="Back to POS", font_size="14sp",
            background_color=SURFACE, color=MUTED, background_normal="",
        )
        back_btn.bind(on_release=lambda x: setattr(self.manager, "current", "pos"))
        bottom.add_widget(back_btn)
        main.add_widget(bottom)

        self.add_widget(main)

    def _haptic(self):
        from backend.database import haptic_click
        haptic_click()

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
        return TextInput(
            hint_text=hint, size_hint_y=None, height=44, multiline=False,
            font_size="14sp", password=is_password,
            background_color=INPUT_BG, background_normal="",
            foreground_color=WHITE, cursor_color=ACCENT,
            hint_text_color=HINT, padding=[12, 10],
            input_filter=input_filter,
        )

    def manage_inventory(self, *args):
        from backend.stock import get_stock_list, delete_stock_item

        content = BoxLayout(orientation="vertical", spacing=6, padding=12)

        self._inv_search = TextInput(
            hint_text="  Search inventory...", size_hint_y=None, height=40,
            multiline=False, font_size="13sp",
            background_color=INPUT_BG, background_normal="",
            foreground_color=WHITE, cursor_color=ACCENT,
            hint_text_color=HINT, padding=[10, 8],
        )
        self._inv_search.bind(text=self._filter_inventory)
        content.add_widget(self._inv_search)

        scroll = ScrollView()
        self._inv_list_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=2)
        self._inv_list_box.bind(minimum_height=self._inv_list_box.setter("height"))
        self._inv_items_data = get_stock_list()
        self._populate_inventory_list()
        scroll.add_widget(self._inv_list_box)
        content.add_widget(scroll)

        add_label = Label(text="Add new item:", font_size="11sp", color=MUTED,
                          size_hint_y=None, height=20)
        content.add_widget(add_label)

        add_box = BoxLayout(spacing=6, size_hint_y=None, height=48)
        self._inv_name = self._make_input("Name")
        self._inv_price = self._make_input("Price", input_filter="float")
        self._inv_cat = self._make_input("Category")
        add_box.add_widget(self._inv_name)
        add_box.add_widget(self._inv_price)
        add_box.add_widget(self._inv_cat)
        content.add_widget(add_box)

        add_btn = Button(text="+ Add Item", size_hint_y=None, height=44,
                         background_color=SUCCESS, color=WHITE, background_normal="")
        add_btn.bind(on_release=lambda x: self._do_add_inv())
        content.add_widget(add_btn)

        popup = Popup(title="Inventory Management", content=content, size_hint=(0.95, 0.88),
                      auto_dismiss=False, background_color=CARD,
                      title_color=WHITE, separator_color=DIVIDER)
        close_btn = Button(text="Close", size_hint_y=None, height=44,
                           background_color=SURFACE, color=MUTED, background_normal="")
        close_btn.bind(on_release=popup.dismiss)
        content.add_widget(close_btn)
        self._inv_popup = popup
        popup.open()

    def _populate_inventory_list(self, filter_text=""):
        self._inv_list_box.clear_widgets()
        self._inv_list_box.height = 0
        count = 0
        for name, info in sorted(self._inv_items_data.items()):
            if filter_text and filter_text.lower() not in name.lower():
                continue
            row = BoxLayout(size_hint_y=None, height=40, padding=[6, 2], spacing=4)
            row.add_widget(Label(text=name, font_size="11sp", halign="left",
                                 text_size=(None, None), size_hint_x=0.35, color=WHITE))
            row.add_widget(Label(text=f"KES {info['price']:,.0f}", font_size="11sp",
                                 size_hint_x=0.25, color=ACCENT))
            row.add_widget(Label(text=info.get("category", ""), font_size="9sp",
                                 size_hint_x=0.20, color=MUTED))
            del_btn = Button(text="Del", font_size="10sp", size_hint_x=0.12,
                             background_color=DANGER, color=WHITE, background_normal="")
            del_name = name
            del_btn.bind(on_release=lambda x, n=del_name: self._delete_inv_item(n))
            row.add_widget(del_btn)
            self._inv_list_box.add_widget(row)
            count += 1
        self._inv_list_box.height = count * 42

    def _filter_inventory(self, instance, text):
        self._populate_inventory_list(text)

    def _delete_inv_item(self, name):
        from backend.stock import delete_stock_item
        self._haptic()
        delete_stock_item(name)
        self._inv_items_data.pop(name, None)
        filter_text = self._inv_search.text if hasattr(self, '_inv_search') else ""
        self._populate_inventory_list(filter_text)
        self._log_audit(f"Deleted inventory item: {name}")

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
        self._inv_items_data[name] = {"price": price, "category": cat}
        filter_text = self._inv_search.text if hasattr(self, '_inv_search') else ""
        self._populate_inventory_list(filter_text)
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
        self._staff_widgets = []
        for user, info in sorted(staff.items()):
            row = BoxLayout(size_hint_y=None, height=42, padding=[6, 2], spacing=4)
            row.add_widget(Label(text=user, font_size="11sp", halign="left",
                                 text_size=(None, None), size_hint_x=0.20, color=WHITE))
            row.add_widget(Label(text=info.get("display_name", ""), font_size="11sp",
                                 size_hint_x=0.22, color=MUTED))

            role_btn = Button(
                text=info.get("role", "cashier"), font_size="10sp",
                size_hint_x=0.15, background_normal="",
                background_color=WARNING if info.get("role") == "admin" else SURFACE,
                color=WHITE,
            )
            role_u = user
            role_btn.bind(on_release=lambda x, u=role_u: self._toggle_staff_role(u))
            row.add_widget(role_btn)

            pin_btn = Button(
                text="PIN", font_size="10sp", size_hint_x=0.10,
                background_color=SURFACE, color=MUTED, background_normal="",
            )
            pin_u = user
            pin_btn.bind(on_release=lambda x, u=pin_u: self._set_staff_pin(u))
            row.add_widget(pin_btn)

            del_btn = Button(
                text="X", font_size="11sp", size_hint_x=0.10,
                background_color=DANGER, color=WHITE, background_normal="",
            )
            del_u = user
            del_btn.bind(on_release=lambda x, u=del_u: self._delete_staff(u))
            row.add_widget(del_btn)

            staff_box.add_widget(row)
            self._staff_widgets.append(user)
        scroll.add_widget(staff_box)
        content.add_widget(scroll)

        add_label = Label(text="Add new staff:", font_size="11sp", color=MUTED,
                          size_hint_y=None, height=20)
        content.add_widget(add_label)

        add_box = BoxLayout(spacing=6, size_hint_y=None, height=48)
        self._staff_user = self._make_input("Username")
        self._staff_name = self._make_input("Display Name")
        self._staff_pw = self._make_input("Password (min 6)", is_password=True)
        add_box.add_widget(self._staff_user)
        add_box.add_widget(self._staff_name)
        add_box.add_widget(self._staff_pw)
        content.add_widget(add_box)

        self._staff_error = Label(text="", font_size="11sp", size_hint_y=None,
                                  height=18, color=DANGER)
        content.add_widget(self._staff_error)

        add_btn = Button(text="+ Add Staff", size_hint_y=None, height=44,
                         background_color=SUCCESS, color=WHITE, background_normal="")
        add_btn.bind(on_release=lambda x: self._do_add_staff())
        content.add_widget(add_btn)

        popup = Popup(title="Staff Management", content=content,
                      size_hint=(0.95, 0.85), auto_dismiss=False,
                      background_color=CARD, title_color=WHITE,
                      separator_color=DIVIDER)
        close_btn = Button(text="Close", size_hint_y=None, height=44,
                           background_color=SURFACE, color=MUTED, background_normal="")
        close_btn.bind(on_release=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()

    def _toggle_staff_role(self, username):
        from backend.database import load_json, save_json, session
        self._haptic()
        data = load_json("staff", {"accounts": {}})
        acc = data.get("accounts", {}).get(username)
        if not acc:
            return
        if username == session.get_user()["username"]:
            return
        current = acc.get("role", "cashier")
        acc["role"] = "cashier" if current == "admin" else "admin"
        save_json("staff", data)
        self._log_audit(f"Changed role: {username} -> {acc['role']}")
        self.manage_staff()

    def _set_staff_pin(self, username):
        from backend.database import load_json, save_json
        self._haptic()
        content = BoxLayout(orientation="vertical", spacing=10, padding=16)
        content.add_widget(Label(
            text=f"Set PIN for {username}",
            font_size="14sp", color=WHITE,
        ))
        pin_input = TextInput(
            hint_text="4-digit PIN", input_filter="int", max_length=4,
            size_hint_y=None, height=44, multiline=False, font_size="18sp",
            background_color=INPUT_BG, background_normal="",
            foreground_color=WHITE, cursor_color=ACCENT,
            hint_text_color=HINT, padding=[12, 10],
        )
        content.add_widget(pin_input)

        err_label = Label(text="", font_size="11sp", color=DANGER,
                          size_hint_y=None, height=18)
        content.add_widget(err_label)

        btn_box = BoxLayout(spacing=8, size_hint_y=None, height=44)
        cancel = Button(text="Cancel", background_color=SURFACE, color=MUTED, background_normal="")
        save = Button(text="Save PIN", background_color=SUCCESS, color=WHITE, background_normal="")
        btn_box.add_widget(cancel)
        btn_box.add_widget(save)
        content.add_widget(btn_box)

        popup = Popup(title="Set PIN", content=content, size_hint=(0.8, 0.45),
                      auto_dismiss=False, background_color=CARD,
                      title_color=WHITE, separator_color=DIVIDER)
        cancel.bind(on_release=popup.dismiss)
        save.bind(on_release=lambda x: self._save_pin(popup, username, pin_input, err_label))
        popup.open()

    def _save_pin(self, popup, username, pin_input, err_label):
        from backend.database import load_json, save_json
        pin = pin_input.text.strip()
        if len(pin) != 4 or not pin.isdigit():
            err_label.text = "PIN must be exactly 4 digits"
            return
        data = load_json("staff", {"accounts": {}})
        acc = data.get("accounts", {}).get(username)
        if acc:
            acc["pin"] = pin
            save_json("staff", data)
            self._log_audit(f"Set PIN for {username}")
        popup.dismiss()

    def _delete_staff(self, username):
        from backend.database import load_json, save_json, session
        self._haptic()
        if username == session.get_user()["username"]:
            return
        data = load_json("staff", {"accounts": {}})
        if username in data.get("accounts", {}):
            del data["accounts"][username]
            save_json("staff", data)
            self._log_audit(f"Deleted staff: {username}")
            self.manage_staff()

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
        from backend.stock import load_stock_movements, save_stock_movements
        from backend.database import today_key

        dk = today_key()
        content = BoxLayout(orientation="vertical", spacing=6, padding=12)
        content.add_widget(Label(text=f"Date: {dk}", size_hint_y=None, height=32,
                                 color=MUTED))

        add_box = BoxLayout(spacing=6, size_hint_y=None, height=48)
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

        add_entry_btn = Button(text="+ Add Entry", size_hint_y=None, height=40,
                               background_color=ORANGE, color=WHITE, background_normal="")
        add_entry_btn.bind(on_release=lambda x: self._add_stock_entry())
        content.add_widget(add_entry_btn)

        popup = Popup(title="Add Stock", content=content, size_hint=(0.95, 0.8),
                      auto_dismiss=False, background_color=CARD,
                      title_color=WHITE, separator_color=DIVIDER)

        save_btn = Button(text="Save All", size_hint_y=None, height=44,
                          background_color=SUCCESS, color=WHITE, background_normal="")
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
        row = BoxLayout(size_hint_y=None, height=32)
        row.add_widget(Label(text=f"{name}: {qty}", font_size="12sp", halign="left",
                             text_size=(None, None), color=WHITE))
        self._stock_entries_box.add_widget(row)
        self._stock_entries_box.height += 32
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
                                 size_hint_y=None, height=28, color=MUTED))

        self._take_search = TextInput(
            hint_text="  Search items...", size_hint_y=None, height=38,
            multiline=False, font_size="13sp",
            background_color=INPUT_BG, background_normal="",
            foreground_color=WHITE, cursor_color=ACCENT,
            hint_text_color=HINT, padding=[10, 8],
        )
        self._take_search.bind(text=self._filter_stock_take)
        content.add_widget(self._take_search)

        self._take_fields = {}
        self._take_remaining = remaining
        scroll = ScrollView()
        self._take_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=2)
        self._take_box.bind(minimum_height=self._take_box.setter("height"))
        self._populate_stock_take()
        scroll.add_widget(self._take_box)
        content.add_widget(scroll)

        popup = Popup(title=f"Stock Taking - {dk}", content=content,
                      size_hint=(0.95, 0.88), auto_dismiss=False,
                      background_color=CARD, title_color=WHITE,
                      separator_color=DIVIDER)
        save_btn = Button(text="Save", size_hint_y=None, height=44,
                          background_color=SUCCESS, color=WHITE, background_normal="")
        save_btn.bind(on_release=lambda x: (self._save_stock_take(dk), popup.dismiss()))
        cancel_btn = Button(text="Cancel", size_hint_y=None, height=44,
                            background_color=SURFACE, color=MUTED, background_normal="")
        cancel_btn.bind(on_release=popup.dismiss)
        btn_box = BoxLayout(spacing=6, size_hint_y=None, height=48)
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(save_btn)
        content.add_widget(btn_box)
        popup.open()

    def _populate_stock_take(self, filter_text=""):
        self._take_box.clear_widgets()
        self._take_box.height = 0
        count = 0
        for name in sorted(get_stock_list().keys()):
            if filter_text and filter_text.lower() not in name.lower():
                continue
            exp = self._take_remaining.get(name, 0)
            row = BoxLayout(size_hint_y=None, height=40, spacing=4)
            row.add_widget(Label(text=name, font_size="11sp", halign="left",
                                 text_size=(None, None), size_hint_x=0.55, color=WHITE))
            field = TextInput(
                hint_text=f"exp: {exp}", input_filter="int",
                font_size="13sp", multiline=False, size_hint_x=0.3,
                background_color=INPUT_BG, background_normal="",
                foreground_color=WHITE, cursor_color=ACCENT,
                hint_text_color=HINT, padding=[8, 8],
            )
            if name in self._take_fields:
                field.text = self._take_fields[name].text
            self._take_fields[name] = field
            row.add_widget(field)
            self._take_box.add_widget(row)
            count += 1
        self._take_box.height = count * 42

    def _filter_stock_take(self, instance, text):
        saved = {}
        for name, field in self._take_fields.items():
            if field.text:
                saved[name] = field.text
        self._populate_stock_take(text)
        for name, field in self._take_fields.items():
            if name in saved:
                field.text = saved[name]

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
        from backend.stock import get_stock_list

        content = BoxLayout(orientation="vertical", spacing=4, padding=12)
        content.add_widget(Label(text="Enter new prices", size_hint_y=None,
                                 height=28, color=MUTED))

        self._price_fields = {}
        scroll = ScrollView()
        prices_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=2)
        prices_box.bind(minimum_height=prices_box.setter("height"))
        for name, info in sorted(get_stock_list().items()):
            row = BoxLayout(size_hint_y=None, height=40, spacing=4)
            row.add_widget(Label(text=name, font_size="11sp", halign="left",
                                 text_size=(None, None), size_hint_x=0.55, color=WHITE))
            field = TextInput(
                text=str(int(info["price"])), input_filter="float",
                font_size="13sp", multiline=False, size_hint_x=0.3,
                background_color=INPUT_BG, background_normal="",
                foreground_color=WHITE, cursor_color=ACCENT, padding=[8, 8],
            )
            self._price_fields[name] = field
            row.add_widget(field)
            prices_box.add_widget(row)
        scroll.add_widget(prices_box)
        content.add_widget(scroll)

        popup = Popup(title="Edit Prices", content=content, size_hint=(0.95, 0.85),
                      auto_dismiss=False, background_color=CARD,
                      title_color=WHITE, separator_color=DIVIDER)
        save_btn = Button(text="Save", size_hint_y=None, height=44,
                          background_color=SUCCESS, color=WHITE, background_normal="")
        save_btn.bind(on_release=lambda x: (self._save_prices(), popup.dismiss()))
        cancel_btn = Button(text="Cancel", size_hint_y=None, height=44,
                            background_color=SURFACE, color=MUTED, background_normal="")
        cancel_btn.bind(on_release=popup.dismiss)
        btn_box = BoxLayout(spacing=6, size_hint_y=None, height=48)
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

    def export_backup(self, *args):
        from backend.database import DATA_DIR, today_key
        from backend.reports import export_csv
        dk = today_key()
        try:
            backup_path = os.path.join(DATA_DIR, f"backup_{dk}.csv")
            export_csv(dk, backup_path)
            self._log_audit(f"Exported CSV backup: {backup_path}")
            content = BoxLayout(orientation="vertical", spacing=12, padding=20)
            content.add_widget(Label(
                text=f"Backup saved!\n\n{backup_path}",
                font_size="13sp", halign="center", color=WHITE,
                text_size=(280, None),
            ))
            ok_btn = Button(text="OK", size_hint_y=None, height=44,
                            background_color=SUCCESS, color=WHITE, background_normal="")
            content.add_widget(ok_btn)
            popup = Popup(title="Export Complete", content=content,
                          size_hint=(0.85, 0.4), background_color=CARD,
                          title_color=WHITE, separator_color=DIVIDER)
            ok_btn.bind(on_release=popup.dismiss)
            popup.open()
        except Exception as e:
            content = BoxLayout(orientation="vertical", spacing=12, padding=20)
            content.add_widget(Label(
                text=f"Export failed:\n{str(e)}",
                font_size="13sp", halign="center", color=DANGER,
                text_size=(280, None),
            ))
            ok_btn = Button(text="OK", size_hint_y=None, height=44,
                            background_color=SURFACE, color=MUTED, background_normal="")
            content.add_widget(ok_btn)
            popup = Popup(title="Error", content=content,
                          size_hint=(0.85, 0.35), background_color=CARD,
                          title_color=DANGER, separator_color=DIVIDER)
            ok_btn.bind(on_release=popup.dismiss)
            popup.open()

    def reset_data(self, *args):
        content = BoxLayout(orientation="vertical", spacing=12, padding=20)
        content.add_widget(Label(
            text="This will delete ALL data.\nThis cannot be undone!",
            font_size="14sp", halign="center", color=DANGER,
        ))
        content.add_widget(Label(
            text="Enter admin password to confirm:",
            font_size="13sp", halign="center", color=MUTED,
        ))
        self._reset_pw = TextInput(
            hint_text="Admin password", password=True,
            size_hint_y=None, height=44, multiline=False, font_size="14sp",
            background_color=INPUT_BG, background_normal="",
            foreground_color=WHITE, cursor_color=ACCENT,
            hint_text_color=HINT, padding=[12, 10],
        )
        content.add_widget(self._reset_pw)
        self._reset_error = Label(
            text="", font_size="11sp", size_hint_y=None, height=20, color=DANGER,
        )
        content.add_widget(self._reset_error)
        btn_box = BoxLayout(spacing=10, size_hint_y=None, height=48)
        cancel_btn = Button(text="Cancel", background_color=SURFACE,
                            color=MUTED, background_normal="")
        reset_btn = Button(text="RESET ALL", background_color=DANGER,
                           color=WHITE, background_normal="")
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(reset_btn)
        content.add_widget(btn_box)

        popup = Popup(title="Reset All Data?", content=content, size_hint=(0.85, 0.6),
                      auto_dismiss=False, background_color=CARD,
                      title_color=DANGER, separator_color=DIVIDER)
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
        import glob as glob_mod
        for f in glob_mod.glob(os.path.join(DATA_DIR, "*.json")):
            os.remove(f)
        save_json("staff", {
            "accounts": {
                "admin": {
                    "password_hash": hash_pw("changeme"),
                    "role": "admin",
                    "display_name": "Admin",
                }
            }
        })
        save_json("audit", {"entries": []})
        init_stock()
        self.build_ui()
