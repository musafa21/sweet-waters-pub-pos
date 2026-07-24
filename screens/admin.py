from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, ThreeLineListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog


class AdminScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None

    def set_app(self, app):
        self.app = app

    def on_enter(self):
        self.build_ui()

    def build_ui(self):
        self.clear_widgets()
        main = MDBoxLayout(orientation="vertical", padding=10, spacing=10)
        header = MDBoxLayout(
            size_hint_y=None, height=50,
            md_bg_color=[0.17, 0.24, 0.31, 1], padding=[10, 0, 10, 0],
        )
        header.add_widget(MDLabel(
            text="ADMIN TOOLS", font_style="H6",
            theme_text_color="Custom", text_color=[1, 1, 1, 1],
        ))
        main.add_widget(header)

        content = MDBoxLayout(orientation="vertical", spacing=10, padding=10)
        for text, action, color in [
            ("Manage Inventory", self.manage_inventory, [0.15, 0.68, 0.38, 1]),
            ("Manage Staff", self.manage_staff, [0.16, 0.5, 0.73, 1]),
            ("Add Stock", self.add_stock, [0.9, 0.49, 0.13, 1]),
            ("Stock Taking", self.stock_take, [0.56, 0.27, 0.68, 1]),
            ("Edit Prices", self.edit_prices, [0.9, 0.49, 0.13, 1]),
            ("Reset All Data", self.reset_data, [0.91, 0.3, 0.24, 1]),
        ]:
            content.add_widget(MDRaisedButton(
                text=text, size_hint_y=None, height=50,
                md_bg_color=color, on_release=action,
            ))
        content.add_widget(MDLabel())
        main.add_widget(content)

        bottom = MDBoxLayout(size_hint_y=None, height=50, padding=5)
        bottom.add_widget(MDRaisedButton(
            text="Back",
            on_release=lambda x: setattr(self.manager, "current", "pos"),
            md_bg_color=[0.59, 0.65, 0.65, 1],
        ))
        main.add_widget(bottom)
        self.add_widget(main)

    def manage_inventory(self, *args):
        from backend.stock import get_stock_list, set_stock_item, delete_stock_item

        content = MDBoxLayout(orientation="vertical", spacing=5, padding=10)
        inv_list = MDList()
        for name, info in sorted(get_stock_list().items()):
            inv_list.add_widget(ThreeLineListItem(
                text=name,
                secondary_text=f"KES {info['price']:,.0f}",
                tertiary_text=info.get("category", ""),
            ))
        scroll = MDScrollView()
        scroll.add_widget(inv_list)
        content.add_widget(scroll)

        add_box = MDBoxLayout(spacing=5, size_hint_y=None, height=50)
        self._inv_name = MDTextField(hint_text="Name", size_hint_x=0.4)
        self._inv_price = MDTextField(hint_text="Price", input_filter="float", size_hint_x=0.25)
        self._inv_cat = MDTextField(hint_text="Category", size_hint_x=0.25)
        add_box.add_widget(self._inv_name)
        add_box.add_widget(self._inv_price)
        add_box.add_widget(self._inv_cat)
        content.add_widget(add_box)

        btn_box = MDBoxLayout(spacing=5, size_hint_y=None, height=40)
        btn_box.add_widget(MDRaisedButton(
            text="Add Item", md_bg_color=[0.15, 0.68, 0.38, 1],
            on_release=lambda x: self._add_inv_item(inv_list),
        ))
        content.add_widget(btn_box)

        dialog = MDDialog(
            title="Inventory Management", type="custom",
            content_cls=content,
            buttons=[MDFlatButton(text="Close", on_release=lambda x: dialog.dismiss())],
            size_hint=[0.95, 0.9],
        )
        dialog.open()

    def _add_inv_item(self, inv_list):
        from backend.stock import set_stock_item
        name = self._inv_name.text.strip()
        try:
            price = float(self._inv_price.text)
        except ValueError:
            return
        cat = self._inv_cat.text.strip() or "Uncategorized"
        set_stock_item(name, price, cat)
        inv_list.add_widget(ThreeLineListItem(
            text=name, secondary_text=f"KES {price:,.0f}", tertiary_text=cat,
        ))
        self._inv_name.text = ""
        self._inv_price.text = ""

    def manage_staff(self, *args):
        from backend.database import load_json, save_json, hash_pw

        content = MDBoxLayout(orientation="vertical", spacing=5, padding=10)
        staff_list = MDList()
        staff = load_json("staff", {"accounts": {}}).get("accounts", {})
        for user, info in sorted(staff.items()):
            staff_list.add_widget(ThreeLineListItem(
                text=user,
                secondary_text=info.get("display_name", ""),
                tertiary_text=info.get("role", ""),
            ))
        scroll = MDScrollView()
        scroll.add_widget(staff_list)
        content.add_widget(scroll)

        add_box = MDBoxLayout(spacing=5, size_hint_y=None, height=50)
        self._staff_user = MDTextField(hint_text="Username", size_hint_x=0.3)
        self._staff_name = MDTextField(hint_text="Name", size_hint_x=0.3)
        self._staff_pw = MDTextField(hint_text="Password", size_hint_x=0.25)
        add_box.add_widget(self._staff_user)
        add_box.add_widget(self._staff_name)
        add_box.add_widget(self._staff_pw)
        content.add_widget(add_box)

        btn_box = MDBoxLayout(spacing=5, size_hint_y=None, height=40)
        btn_box.add_widget(MDRaisedButton(
            text="Add Staff", md_bg_color=[0.15, 0.68, 0.38, 1],
            on_release=lambda x: self._add_staff(staff_list),
        ))
        content.add_widget(btn_box)

        dialog = MDDialog(
            title="Staff Management", type="custom",
            content_cls=content,
            buttons=[MDFlatButton(text="Close", on_release=lambda x: dialog.dismiss())],
            size_hint=[0.95, 0.8],
        )
        dialog.open()

    def _add_staff(self, staff_list):
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
        staff_list.add_widget(ThreeLineListItem(
            text=user, secondary_text=self._staff_name.text.strip() or user,
            tertiary_text="cashier",
        ))
        self._staff_user.text = ""
        self._staff_name.text = ""
        self._staff_pw.text = ""

    def add_stock(self, *args):
        from backend.stock import get_stock_list
        from backend.stock import load_stock_movements, save_stock_movements
        from backend.database import today_key

        dk = today_key()
        content = MDBoxLayout(orientation="vertical", spacing=5, padding=10, size_hint_y=None, height=350)
        content.add_widget(MDLabel(text=f"Date: {dk}", halign="center"))

        add_box = MDBoxLayout(spacing=5, size_hint_y=None, height=50)
        items = sorted(get_stock_list().keys())
        self._stock_item = MDTextField(hint_text="Item", size_hint_x=0.5)
        self._stock_qty = MDTextField(hint_text="Qty", input_filter="int", size_hint_x=0.3)
        add_box.add_widget(self._stock_item)
        add_box.add_widget(self._stock_qty)
        content.add_widget(add_box)

        self._stock_entries = MDList()
        scroll = MDScrollView()
        scroll.add_widget(self._stock_entries)
        content.add_widget(scroll)

        def add_entry(dt):
            name = self._stock_item.text.strip()
            try:
                qty = int(self._stock_qty.text)
            except ValueError:
                return
            self._stock_entries.add_widget(ThreeLineListItem(
                text=name, secondary_text=f"Qty: {qty}", tertiary_text="",
            ))
            self._stock_item.text = ""
            self._stock_qty.text = ""

        def save_entries(dt):
            entries = []
            for child in self._stock_entries.children:
                if hasattr(child, 'text'):
                    try:
                        qty = int(child.secondary_text.replace("Qty: ", ""))
                        entries.append({"item": child.text, "qty": qty})
                    except (ValueError, AttributeError):
                        pass
            movements = load_stock_movements()
            movements.setdefault("purchases", {})[dk] = entries
            save_stock_movements(movements)

        dialog = MDDialog(
            title="Add Stock", type="custom", content_cls=content,
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(text="Save", md_bg_color=[0.15, 0.68, 0.38, 1],
                               on_release=lambda x: (save_entries(None), dialog.dismiss())),
            ],
            size_hint=[0.95, 0.8],
        )
        dialog.open()

    def stock_take(self, *args):
        from backend.stock import get_stock_list, calc_remaining_stock
        from backend.stock import load_stock_movements, save_stock_movements
        from backend.database import today_key

        dk = today_key()
        remaining = calc_remaining_stock(dk)
        content = MDBoxLayout(orientation="vertical", spacing=5, padding=10, size_hint_y=None, height=400)
        content.add_widget(MDLabel(text="Enter closing stock counts", halign="center"))

        self._take_fields = {}
        fields_list = MDList()
        for name in sorted(get_stock_list().keys()):
            exp = remaining.get(name, 0)
            field = MDTextField(
                hint_text=f"{name} (exp: {exp})",
                input_filter="int",
                size_hint_y=None,
                height=45,
            )
            self._take_fields[name] = field
            fields_list.add_widget(field)
        scroll = MDScrollView()
        scroll.add_widget(fields_list)
        content.add_widget(scroll)

        def save_closing(dt):
            closing = {}
            for name, field in self._take_fields.items():
                try:
                    closing[name] = int(field.text)
                except (ValueError, TypeError):
                    pass
            movements = load_stock_movements()
            movements.setdefault("closing", {})[dk] = closing
            save_stock_movements(movements)

        dialog = MDDialog(
            title=f"Stock Taking - {dk}", type="custom", content_cls=content,
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(text="Save", md_bg_color=[0.15, 0.68, 0.38, 1],
                               on_release=lambda x: (save_closing(None), dialog.dismiss())),
            ],
            size_hint=[0.95, 0.9],
        )
        dialog.open()

    def edit_prices(self, *args):
        from backend.stock import get_stock_list, get_effective_price, set_stock_item

        content = MDBoxLayout(orientation="vertical", spacing=5, padding=10, size_hint_y=None, height=400)
        self._price_fields = {}
        prices_list = MDList()
        for name, info in sorted(get_stock_list().items()):
            field = MDTextField(
                hint_text=f"{name} (current: KES {info['price']:,.0f})",
                input_filter="float",
                size_hint_y=None,
                height=45,
            )
            self._price_fields[name] = field
            prices_list.add_widget(field)
        scroll = MDScrollView()
        scroll.add_widget(prices_list)
        content.add_widget(scroll)

        def save_prices(dt):
            for name, field in self._price_fields.items():
                try:
                    new_price = float(field.text)
                    set_stock_item(name, new_price)
                except (ValueError, TypeError):
                    pass

        dialog = MDDialog(
            title="Edit Prices", type="custom", content_cls=content,
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(text="Save", md_bg_color=[0.15, 0.68, 0.38, 1],
                               on_release=lambda x: (save_prices(None), dialog.dismiss())),
            ],
            size_hint=[0.95, 0.9],
        )
        dialog.open()

    def reset_data(self, *args):
        def confirm_reset(dt):
            from backend.database import save_json
            from backend.stock import init_stock
            from backend.database import load_json
            import os
            from backend.database import DATA_DIR
            import glob as glob_mod
            for f in glob_mod.glob(os.path.join(DATA_DIR, "*.json")):
                os.remove(f)
            init_staff_data()
            self.build_ui()

        def init_staff_data():
            from backend.database import save_json, hash_pw
            save_json("staff", {
                "accounts": {
                    "admin": {
                        "password_hash": hash_pw("admin123"),
                        "role": "admin",
                        "display_name": "Administrator",
                    }
                }
            })

        dialog = MDDialog(
            title="Reset All Data?",
            text="This will delete ALL data. This cannot be undone!",
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(
                    text="RESET", md_bg_color=[0.91, 0.3, 0.24, 1],
                    on_release=lambda x: (dialog.dismiss(), confirm_reset(None)),
                ),
            ],
        )
        dialog.open()
