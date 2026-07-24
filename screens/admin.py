from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput


class AdminScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None

    def set_app(self, app):
        self.app = app

    def on_enter(self):
        self.build_ui()

    def build_ui(self):
        self.clear_widgets()
        main = BoxLayout(orientation="vertical", padding=8, spacing=8)

        header = BoxLayout(size_hint_y=None, height=48, padding=[10, 0, 10, 0])
        with header.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0.1, 0.13, 0.24, 1)
            header._bg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda s, _: s._bg.__setattr__("pos", s.pos))
        header.bind(size=lambda s, _: s._bg.__setattr__("size", s.size))
        header.add_widget(Label(
            text="ADMIN TOOLS", font_size="16sp", color=(1, 1, 1, 1),
        ))
        main.add_widget(header)

        content = BoxLayout(orientation="vertical", spacing=8, padding=8)
        for text, action, color in [
            ("Manage Inventory", self.manage_inventory, (0.15, 0.68, 0.38, 1)),
            ("Manage Staff", self.manage_staff, (0.16, 0.5, 0.73, 1)),
            ("Add Stock", self.add_stock, (0.9, 0.49, 0.13, 1)),
            ("Stock Taking", self.stock_take, (0.56, 0.27, 0.68, 1)),
            ("Edit Prices", self.edit_prices, (0.9, 0.49, 0.13, 1)),
            ("Reset All Data", self.reset_data, (0.91, 0.3, 0.24, 1)),
        ]:
            btn = Button(
                text=text, font_size="14sp", size_hint_y=None, height=48,
                background_color=color, color=(1, 1, 1, 1),
            )
            btn.bind(on_release=action)
            content.add_widget(btn)
        content.add_widget(Label())
        main.add_widget(content)

        bottom = BoxLayout(size_hint_y=None, height=44, padding=5)
        back_btn = Button(text="Back", font_size="13sp",
                          background_color=(0.59, 0.65, 0.65, 1), color=(1, 1, 1, 1))
        back_btn.bind(on_release=lambda x: setattr(self.manager, "current", "pos"))
        bottom.add_widget(back_btn)
        main.add_widget(bottom)
        self.add_widget(main)

    def manage_inventory(self, *args):
        from backend.stock import get_stock_list, set_stock_item

        content = BoxLayout(orientation="vertical", spacing=5, padding=10)

        scroll = ScrollView()
        inv_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=2)
        inv_box.bind(minimum_height=inv_box.setter("height"))
        for name, info in sorted(get_stock_list().items()):
            row = BoxLayout(size_hint_y=None, height=32, padding=[4, 2])
            row.add_widget(Label(text=name, font_size="12sp", halign="left",
                                 text_size=(None, None), size_hint_x=0.45, color=(1, 1, 1, 1)))
            row.add_widget(Label(text=f"KES {info['price']:,.0f}", font_size="12sp",
                                 size_hint_x=0.3, color=(0.91, 0.3, 0.24, 1)))
            row.add_widget(Label(text=info.get("category", ""), font_size="10sp",
                                 size_hint_x=0.25, color=(0.7, 0.7, 0.7, 1)))
            inv_box.add_widget(row)
        scroll.add_widget(inv_box)
        content.add_widget(scroll)

        add_box = BoxLayout(spacing=4, size_hint_y=None, height=40)
        self._inv_name = TextInput(hint_text="Name", font_size="12sp", multiline=False)
        self._inv_price = TextInput(hint_text="Price", input_filter="float", font_size="12sp", multiline=False)
        self._inv_cat = TextInput(hint_text="Category", font_size="12sp", multiline=False)
        add_box.add_widget(self._inv_name)
        add_box.add_widget(self._inv_price)
        add_box.add_widget(self._inv_cat)
        content.add_widget(add_box)

        add_btn = Button(text="Add Item", size_hint_y=None, height=36,
                         background_color=(0.15, 0.68, 0.38, 1), color=(1, 1, 1, 1))
        add_btn.bind(on_release=lambda x: self._do_add_inv())
        content.add_widget(add_btn)

        popup = Popup(title="Inventory", content=content, size_hint=(0.95, 0.85), auto_dismiss=False)
        close_btn = Button(text="Close", size_hint_y=None, height=36,
                           background_color=(0.5, 0.5, 0.5, 1), color=(1, 1, 1, 1))
        close_btn.bind(on_release=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()

    def _do_add_inv(self):
        from backend.stock import set_stock_item
        name = self._inv_name.text.strip()
        try:
            price = float(self._inv_price.text)
        except ValueError:
            return
        cat = self._inv_cat.text.strip() or "Uncategorized"
        set_stock_item(name, price, cat)
        self._inv_name.text = ""
        self._inv_price.text = ""
        self._inv_cat.text = ""

    def manage_staff(self, *args):
        from backend.database import load_json, save_json, hash_pw

        content = BoxLayout(orientation="vertical", spacing=5, padding=10)

        scroll = ScrollView()
        staff_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=2)
        staff_box.bind(minimum_height=staff_box.setter("height"))
        staff = load_json("staff", {"accounts": {}}).get("accounts", {})
        for user, info in sorted(staff.items()):
            row = BoxLayout(size_hint_y=None, height=32, padding=[4, 2])
            row.add_widget(Label(text=user, font_size="12sp", halign="left",
                                 text_size=(None, None), size_hint_x=0.3, color=(1, 1, 1, 1)))
            row.add_widget(Label(text=info.get("display_name", ""), font_size="12sp",
                                 size_hint_x=0.35, color=(0.7, 0.7, 0.7, 1)))
            row.add_widget(Label(text=info.get("role", ""), font_size="12sp",
                                 size_hint_x=0.2, color=(0.95, 0.77, 0.06, 1)))
            staff_box.add_widget(row)
        scroll.add_widget(staff_box)
        content.add_widget(scroll)

        add_box = BoxLayout(spacing=4, size_hint_y=None, height=40)
        self._staff_user = TextInput(hint_text="Username", font_size="12sp", multiline=False)
        self._staff_name = TextInput(hint_text="Name", font_size="12sp", multiline=False)
        self._staff_pw = TextInput(hint_text="Password", font_size="12sp", multiline=False, password=True)
        add_box.add_widget(self._staff_user)
        add_box.add_widget(self._staff_name)
        add_box.add_widget(self._staff_pw)
        content.add_widget(add_box)

        add_btn = Button(text="Add Staff", size_hint_y=None, height=36,
                         background_color=(0.15, 0.68, 0.38, 1), color=(1, 1, 1, 1))
        add_btn.bind(on_release=lambda x: self._do_add_staff())
        content.add_widget(add_btn)

        popup = Popup(title="Staff Management", content=content, size_hint=(0.95, 0.8), auto_dismiss=False)
        close_btn = Button(text="Close", size_hint_y=None, height=36,
                           background_color=(0.5, 0.5, 0.5, 1), color=(1, 1, 1, 1))
        close_btn.bind(on_release=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()

    def _do_add_staff(self):
        from backend.database import load_json, save_json, hash_pw
        user = self._staff_user.text.strip()
        pw = self._staff_pw.text
        if not user or not pw:
            return
        data = load_json("staff", {"accounts": {}})
        data.setdefault("accounts", {})[user] = {
            "password_hash": hash_pw(pw),
            "role": "cashier",
            "display_name": self._staff_name.text.strip() or user,
        }
        save_json("staff", data)
        self._staff_user.text = ""
        self._staff_name.text = ""
        self._staff_pw.text = ""

    def add_stock(self, *args):
        from backend.stock import get_stock_list, load_stock_movements, save_stock_movements
        from backend.database import today_key

        dk = today_key()
        content = BoxLayout(orientation="vertical", spacing=5, padding=10)
        content.add_widget(Label(text=f"Date: {dk}", size_hint_y=None, height=30))

        add_box = BoxLayout(spacing=4, size_hint_y=None, height=40)
        self._stock_item = TextInput(hint_text="Item", font_size="12sp", multiline=False)
        self._stock_qty = TextInput(hint_text="Qty", input_filter="int", font_size="12sp", multiline=False)
        add_box.add_widget(self._stock_item)
        add_box.add_widget(self._stock_qty)
        content.add_widget(add_box)

        self._stock_entries_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=2)
        self._stock_entries_box.bind(minimum_height=self._stock_entries_box.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self._stock_entries_box)
        content.add_widget(scroll)

        add_entry_btn = Button(text="+ Add Entry", size_hint_y=None, height=32,
                               background_color=(0.9, 0.49, 0.13, 1), color=(1, 1, 1, 1))
        add_entry_btn.bind(on_release=lambda x: self._add_stock_entry())
        content.add_widget(add_entry_btn)

        popup = Popup(title="Add Stock", content=content, size_hint=(0.95, 0.8), auto_dismiss=False)

        save_btn = Button(text="Save All", size_hint_y=None, height=36,
                          background_color=(0.15, 0.68, 0.38, 1), color=(1, 1, 1, 1))
        save_btn.bind(on_release=lambda x: (self._save_stock_entries(dk), popup.dismiss()))
        content.add_widget(save_btn)
        popup.open()

    def _add_stock_entry(self):
        name = self._stock_item.text.strip()
        try:
            qty = int(self._stock_qty.text)
        except ValueError:
            return
        row = BoxLayout(size_hint_y=None, height=28)
        row.add_widget(Label(text=f"{name}: {qty}", font_size="12sp", halign="left",
                             text_size=(None, None), color=(1, 1, 1, 1)))
        self._stock_entries_box.add_widget(row)
        self._stock_entries_box.height += 28
        self._stock_entries_box.add_widget(row)
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
        self._last_stock_entries = []

    def stock_take(self, *args):
        from backend.stock import get_stock_list, calc_remaining_stock, load_stock_movements, save_stock_movements
        from backend.database import today_key

        dk = today_key()
        remaining = calc_remaining_stock(dk)
        content = BoxLayout(orientation="vertical", spacing=5, padding=10)
        content.add_widget(Label(text="Enter closing stock counts", size_hint_y=None, height=30))

        self._take_fields = {}
        scroll = ScrollView()
        fields_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=2)
        fields_box.bind(minimum_height=fields_box.setter("height"))
        for name in sorted(get_stock_list().keys()):
            exp = remaining.get(name, 0)
            row = BoxLayout(size_hint_y=None, height=36, spacing=4)
            row.add_widget(Label(text=name, font_size="11sp", halign="left", text_size=(None, None),
                                 size_hint_x=0.55, color=(1, 1, 1, 1)))
            field = TextInput(
                hint_text=f"exp: {exp}", input_filter="int",
                font_size="13sp", multiline=False, size_hint_x=0.3,
            )
            self._take_fields[name] = field
            row.add_widget(field)
            fields_box.add_widget(row)
        scroll.add_widget(fields_box)
        content.add_widget(scroll)

        popup = Popup(title=f"Stock Taking - {dk}", content=content, size_hint=(0.95, 0.85), auto_dismiss=False)
        save_btn = Button(text="Save", size_hint_y=None, height=36,
                          background_color=(0.15, 0.68, 0.38, 1), color=(1, 1, 1, 1))
        save_btn.bind(on_release=lambda x: (self._save_stock_take(dk), popup.dismiss()))
        cancel_btn = Button(text="Cancel", size_hint_y=None, height=36,
                            background_color=(0.5, 0.5, 0.5, 1), color=(1, 1, 1, 1))
        cancel_btn.bind(on_release=popup.dismiss)
        btn_box = BoxLayout(spacing=5, size_hint_y=None, height=40)
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

    def edit_prices(self, *args):
        from backend.stock import get_stock_list, set_stock_item

        content = BoxLayout(orientation="vertical", spacing=5, padding=10)
        content.add_widget(Label(text="Enter new prices", size_hint_y=None, height=28))

        self._price_fields = {}
        scroll = ScrollView()
        prices_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=2)
        prices_box.bind(minimum_height=prices_box.setter("height"))
        for name, info in sorted(get_stock_list().items()):
            row = BoxLayout(size_hint_y=None, height=36, spacing=4)
            row.add_widget(Label(text=name, font_size="11sp", halign="left", text_size=(None, None),
                                 size_hint_x=0.55, color=(1, 1, 1, 1)))
            field = TextInput(
                text=str(int(info["price"])), input_filter="float",
                font_size="13sp", multiline=False, size_hint_x=0.3,
            )
            self._price_fields[name] = field
            row.add_widget(field)
            prices_box.add_widget(row)
        scroll.add_widget(prices_box)
        content.add_widget(scroll)

        popup = Popup(title="Edit Prices", content=content, size_hint=(0.95, 0.85), auto_dismiss=False)
        save_btn = Button(text="Save", size_hint_y=None, height=36,
                          background_color=(0.15, 0.68, 0.38, 1), color=(1, 1, 1, 1))
        save_btn.bind(on_release=lambda x: (self._save_prices(), popup.dismiss()))
        cancel_btn = Button(text="Cancel", size_hint_y=None, height=36,
                            background_color=(0.5, 0.5, 0.5, 1), color=(1, 1, 1, 1))
        cancel_btn.bind(on_release=popup.dismiss)
        btn_box = BoxLayout(spacing=5, size_hint_y=None, height=40)
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(save_btn)
        content.add_widget(btn_box)
        popup.open()

    def _save_prices(self):
        from backend.stock import set_stock_item
        for name, field in self._price_fields.items():
            try:
                new_price = float(field.text)
                set_stock_item(name, new_price)
            except (ValueError, TypeError):
                pass

    def reset_data(self, *args):
        content = BoxLayout(orientation="vertical", spacing=10, padding=15)
        content.add_widget(Label(
            text="This will delete ALL data.\nThis cannot be undone!",
            font_size="14sp", halign="center",
        ))
        btn_box = BoxLayout(spacing=8, size_hint_y=None, height=44)
        cancel_btn = Button(text="Cancel", background_color=(0.5, 0.5, 0.5, 1), color=(1, 1, 1, 1))
        reset_btn = Button(text="RESET", background_color=(0.91, 0.3, 0.24, 1), color=(1, 1, 1, 1))
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(reset_btn)
        content.add_widget(btn_box)

        popup = Popup(title="Reset All Data?", content=content, size_hint=(0.8, 0.4), auto_dismiss=False)
        cancel_btn.bind(on_release=popup.dismiss)
        reset_btn.bind(on_release=lambda x: (popup.dismiss(), self._do_reset()))
        popup.open()

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
                    "password_hash": hash_pw("admin123"),
                    "role": "admin",
                    "display_name": "Administrator",
                }
            }
        })
        init_stock()
        self.build_ui()
