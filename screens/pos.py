from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.menu import MDDropdownMenu
from kivy.core.window import Window
from kivy.clock import Clock


class POSScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.cart = []
        self.current_category = ""
        self.category_buttons = []

    def set_app(self, app):
        self.app = app

    def on_enter(self):
        if not self.ids:
            self.build_ui()
        else:
            self.refresh_items()
            self.update_header()

    def build_ui(self):
        self.clear_widgets()
        main_layout = MDBoxLayout(orientation="vertical")

        top_bar = MDBoxLayout(
            size_hint_y=None,
            height=56,
            md_bg_color=[0.17, 0.24, 0.31, 1],
            padding=[10, 0, 10, 0],
            spacing=10,
        )
        top_bar.add_widget(MDLabel(
            text="SWEET WATERS PUB",
            font_style="H6",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            size_hint_x=0.3,
        ))
        self.user_label = MDLabel(
            text="",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=[0.95, 0.77, 0.06, 1],
            size_hint_x=0.3,
            halign="center",
        )
        top_bar.add_widget(self.user_label)

        btn_box = MDBoxLayout(spacing=5, size_hint_x=0.4)
        for text, action, color in [
            ("Report", self.show_report, [0.16, 0.5, 0.73, 1]),
            ("Debts", self.show_debts, [0.91, 0.3, 0.24, 1]),
            ("Admin", self.show_admin, [0.59, 0.65, 0.65, 1]),
        ]:
            btn = MDFlatButton(
                text=text,
                on_release=action,
                theme_text_color="Custom",
                text_color=[1, 1, 1, 1],
            )
            btn_box.add_widget(btn)
        top_bar.add_widget(btn_box)
        main_layout.add_widget(top_bar)

        content = MDBoxLayout(spacing=5, padding=5)

        left = MDBoxLayout(orientation="vertical", size_hint_x=0.6)

        self.search_field = MDTextField(
            hint_text="Search items...",
            icon_left="magnify",
            size_hint_y=None,
            height=45,
        )
        self.search_field.bind(text=self.on_search)
        left.add_widget(self.search_field)

        self.cat_box = MDBoxLayout(
            size_hint_y=None,
            height=40,
            spacing=5,
            padding=[0, 5, 0, 5],
        )
        left.add_widget(self.cat_box)

        self.items_scroll = MDScrollView()
        self.items_grid = MDGridLayout(
            cols=3,
            spacing=8,
            padding=8,
            size_hint_y=None,
        )
        self.items_grid.bind(minimum_height=self.items_grid.setter("height"))
        self.items_scroll.add_widget(self.items_grid)
        left.add_widget(self.items_scroll)

        content.add_widget(left)

        right = MDBoxLayout(orientation="vertical", size_hint_x=0.4)

        cart_header = MDLabel(
            text="CART",
            font_style="H6",
            halign="center",
            size_hint_y=None,
            height=40,
            md_bg_color=[0.17, 0.24, 0.31, 1],
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
        )
        right.add_widget(cart_header)

        self.cart_list = MDList()
        cart_scroll = MDScrollView()
        cart_scroll.add_widget(self.cart_list)
        right.add_widget(cart_scroll)

        cart_btns = MDBoxLayout(
            size_hint_y=None,
            height=40,
            spacing=5,
            padding=5,
        )
        cart_btns.add_widget(MDFlatButton(
            text="-1",
            on_release=self.decrement_selected,
            md_bg_color=[0.9, 0.49, 0.13, 1],
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
        ))
        cart_btns.add_widget(MDFlatButton(
            text="Remove",
            on_release=self.remove_selected,
            md_bg_color=[0.91, 0.3, 0.24, 1],
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
        ))
        cart_btns.add_widget(MDFlatButton(
            text="Clear",
            on_release=self.clear_cart,
            md_bg_color=[0.59, 0.65, 0.65, 1],
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
        ))
        right.add_widget(cart_btns)

        self.total_label = MDLabel(
            text="TOTAL: KES 0",
            font_style="H5",
            halign="center",
            size_hint_y=None,
            height=50,
        )
        right.add_widget(self.total_label)

        checkout_btn = MDRaisedButton(
            text="CHECKOUT",
            size_hint_y=None,
            height=50,
            md_bg_color=[0.15, 0.68, 0.38, 1],
            on_release=self.checkout,
        )
        right.add_widget(checkout_btn)

        content.add_widget(right)
        main_layout.add_widget(content)
        self.add_widget(main_layout)

        Clock.schedule_once(lambda dt: self.init_data(), 0.1)

    def init_data(self):
        from backend.stock import get_categories, get_stock_list
        self.all_items = get_stock_list()
        self.categories = get_categories()
        self.build_category_buttons()
        self.refresh_items()
        self.update_header()

    def update_header(self):
        if self.app and self.app.current_user:
            u = self.app.current_user
            self.user_label.text = f"{u['display_name']} ({u['role'].upper()})"

    def build_category_buttons(self):
        self.cat_box.clear_widgets()
        for cat_name in sorted(self.categories.keys()):
            btn = MDFlatButton(
                text=cat_name,
                on_release=lambda x, c=cat_name: self.select_category(c),
                theme_text_color="Custom",
                text_color=[0.17, 0.24, 0.31, 1],
            )
            self.cat_box.add_widget(btn)
            self.category_buttons.append(btn)
        if self.categories and not self.current_category:
            self.current_category = list(self.categories.keys())[0]
        self.highlight_category()

    def highlight_category(self):
        for btn in self.category_buttons:
            if btn.text == self.current_category:
                btn.md_bg_color = [0.17, 0.24, 0.31, 1]
                btn.theme_text_color = "Custom"
                btn.text_color = [1, 1, 1, 1]
            else:
                btn.md_bg_color = [0.8, 0.8, 0.8, 1]
                btn.theme_text_color = "Custom"
                btn.text_color = [0.17, 0.24, 0.31, 1]

    def select_category(self, cat_name):
        self.current_category = cat_name
        self.search_field.text = ""
        self.highlight_category()
        self.refresh_items()

    def refresh_items(self):
        self.items_grid.clear_widgets()
        query = self.search_field.text.strip().lower()
        if query:
            items = [n for n in self.all_items if query in n.lower()]
        else:
            items = self.categories.get(self.current_category, [])

        from backend.stock import calc_today_stock, get_effective_price
        stock = calc_today_stock()

        for name in items:
            info = self.all_items.get(name)
            if not info:
                continue
            price = get_effective_price(name)
            qty = stock.get(name, 0)
            oos = qty <= 0

            card = MDCard(
                orientation="vertical",
                padding=8,
                spacing=4,
                size_hint_y=None,
                height=80,
                elevation=2,
                md_bg_color=[0.99, 0.9, 0.89, 1] if oos else [0.96, 0.96, 0.96, 1],
                on_release=lambda x, n=name: self.add_item(n),
            )
            card.add_widget(MDLabel(
                text=name,
                font_style="Caption",
                size_hint_y=None,
                height=20,
                theme_text_color="Error" if oos else "Primary",
            ))
            stock_text = "OUT OF STOCK" if oos else f"Stock: {qty}"
            card.add_widget(MDLabel(
                text=f"KES {price:,.0f} | {stock_text}",
                font_style="Caption",
                size_hint_y=None,
                height=20,
                theme_text_color="Error" if oos else "Secondary",
            ))
            self.items_grid.add_widget(card)

    def on_search(self, instance, text):
        self.refresh_items()

    def add_item(self, name):
        if not self.app:
            return
        from backend.stock import get_effective_price, get_stock_item, calc_today_stock
        info = get_stock_item(name)
        if not info:
            return
        stock = calc_today_stock()
        if stock.get(name, 0) <= 0:
            from kivymd.uix.dialog import MDDialog
            from kivymd.uix.button import MDFlatButton
            dialog = MDDialog(
                title="Out of Stock",
                text=f"{name} is out of stock.",
                buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())],
            )
            dialog.open()
            return
        price = get_effective_price(name)
        self.show_quantity_dialog(name, price)

    def show_quantity_dialog(self, name, price):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton

        content = MDBoxLayout(orientation="vertical", spacing=10, padding=20)
        content.add_widget(MDLabel(
            text=name,
            font_style="H6",
            halign="center",
        ))
        content.add_widget(MDLabel(
            text=f"KES {price:,.0f} each",
            halign="center",
        ))

        qty_box = MDBoxLayout(spacing=10, size_hint_y=None, height=50)
        minus_btn = MDFlatButton(
            text="-",
            on_release=lambda x: self._dec_qty(qty_label),
            size_hint_x=0.2,
        )
        qty_box.add_widget(minus_btn)
        qty_label = MDLabel(
            text="1",
            halign="center",
            font_style="H5",
            size_hint_x=0.3,
        )
        qty_box.add_widget(qty_label)
        plus_btn = MDFlatButton(
            text="+",
            on_release=lambda x: self._inc_qty(qty_label),
            size_hint_x=0.2,
        )
        qty_box.add_widget(plus_btn)
        content.add_widget(qty_box)

        self._qty_dialog_result = None

        def confirm(dt):
            try:
                qty = int(qty_label.text)
            except ValueError:
                qty = 1
            self._qty_dialog_result = qty
            dialog.dismiss()
            self._add_to_cart(name, qty, price)

        dialog = MDDialog(
            title="Enter Quantity",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(
                    text="Add",
                    md_bg_color=[0.15, 0.68, 0.38, 1],
                    on_release=confirm,
                ),
            ],
        )
        dialog.open()

    def _dec_qty(self, label):
        try:
            v = int(label.text)
            if v > 1:
                label.text = str(v - 1)
        except ValueError:
            label.text = "1"

    def _inc_qty(self, label):
        try:
            v = int(label.text)
            label.text = str(v + 1)
        except ValueError:
            label.text = "1"

    def _add_to_cart(self, name, qty, price):
        for i, (n, q, p) in enumerate(self.cart):
            if n == name:
                self.cart[i] = (n, q + qty, p)
                break
        else:
            self.cart.append((name, qty, price))
        self.refresh_cart()

    def refresh_cart(self):
        self.cart_list.clear_widgets()
        total = 0
        for name, qty, price in self.cart:
            lt = qty * price
            total += lt
            item = TwoLineListItem(
                text=f"{name}  x{qty}",
                secondary_text=f"KES {price:,.0f}  |  Total: KES {lt:,.0f}",
                on_release=lambda x, n=name: self._select_cart_item(n),
            )
            self.cart_list.add_widget(item)
        self.total_label.text = f"TOTAL: KES {total:,.0f}"
        self._selected_cart_item = None

    def _select_cart_item(self, name):
        self._selected_cart_item = name

    def remove_selected(self, *args):
        if hasattr(self, '_selected_cart_item') and self._selected_cart_item:
            self.cart = [(n, q, p) for n, q, p in self.cart if n != self._selected_cart_item]
            self._selected_cart_item = None
            self.refresh_cart()

    def decrement_selected(self, *args):
        if hasattr(self, '_selected_cart_item') and self._selected_cart_item:
            for i, (n, q, p) in enumerate(self.cart):
                if n == self._selected_cart_item:
                    if q > 1:
                        self.cart[i] = (n, q - 1, p)
                    else:
                        self.cart.pop(i)
                    break
            self._selected_cart_item = None
            self.refresh_cart()

    def clear_cart(self, *args):
        if self.cart:
            self.cart.clear()
            self.refresh_cart()

    def checkout(self, *args):
        if not self.cart:
            from kivymd.uix.dialog import MDDialog
            from kivymd.uix.button import MDFlatButton
            dialog = MDDialog(
                title="Empty",
                text="Add items first.",
                buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())],
            )
            dialog.open()
            return

        total = sum(q * p for _, q, p in self.cart)
        self.show_payment_dialog(total)

    def show_payment_dialog(self, total):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton

        content = MDBoxLayout(orientation="vertical", spacing=10, padding=20, size_hint_y=None, height=300)
        content.add_widget(MDLabel(
            text=f"TOTAL DUE: KES {total:,.0f}",
            font_style="H5",
            halign="center",
        ))

        method_box = MDBoxLayout(spacing=5, size_hint_y=None, height=40)
        self._pay_method = "cash"
        for m, lbl in [("cash", "Cash"), ("mpesa", "M-Pesa"), ("till", "Till"), ("credit", "Credit")]:
            btn = MDFlatButton(
                text=lbl,
                on_release=lambda x, mm=m: self._set_pay_method(mm, method_box),
                md_bg_color=[0.8, 0.8, 0.8, 1] if m != "cash" else [0.15, 0.68, 0.38, 1],
                theme_text_color="Custom",
                text_color=[1, 1, 1, 1] if m == "cash" else [0, 0, 0, 1],
            )
            method_box.add_widget(btn)
        content.add_widget(method_box)

        self._pay_amount_field = MDTextField(
            hint_text="Amount",
            input_filter="float",
            size_hint_y=None,
            height=50,
        )
        content.add_widget(self._pay_amount_field)

        self._pay_customer_field = MDTextField(
            hint_text="Customer Name (for credit)",
            size_hint_y=None,
            height=50,
        )
        content.add_widget(self._pay_customer_field)

        def confirm_payment(dt):
            try:
                amt = float(self._pay_amount_field.text or 0)
            except ValueError:
                amt = 0

            method = self._pay_method
            if method == "cash" and amt < total:
                from kivymd.uix.dialog import MDDialog
                from kivymd.uix.button import MDFlatButton
                d = MDDialog(
                    title="Short Payment",
                    text=f"Need KES {total - amt:,.0f} more.",
                    buttons=[MDFlatButton(text="OK", on_release=lambda x: d.dismiss())],
                )
                d.open()
                return

            if method == "credit":
                cust = self._pay_customer_field.text.strip()
                if not cust:
                    d = MDDialog(
                        title="Required",
                        text="Enter customer name.",
                        buttons=[MDFlatButton(text="OK", on_release=lambda x: d.dismiss())],
                    )
                    d.open()
                    return

            from backend.database import today_key
            from backend.sales import record_sale
            from datetime import datetime

            dk = today_key()
            now = datetime.now()
            items_sold = {n: q for n, q, p in self.cart}

            txn = {
                "time": now.strftime("%H:%M:%S"),
                "items": items_sold,
                "total": total,
                "payment_method": method,
                "cashier": self.app.current_user["display_name"],
            }

            if method == "cash":
                txn["cash_received"] = amt
                txn["change"] = amt - total
                msg = f"Cash: KES {amt:,.2f}\nChange: KES {txn['change']:,.2f}"
            elif method == "mpesa":
                txn["mpesa_amount"] = amt
                msg = f"M-Pesa: KES {amt:,.2f}"
            elif method == "till":
                txn["till_amount"] = amt
                msg = f"Till: KES {amt:,.2f}"
            elif method == "credit":
                txn["customer"] = self._pay_customer_field.text.strip()
                msg = f"Credit: {txn['customer']}\nKES {total:,.2f}"
            else:
                msg = f"Paid: KES {total:,.2f}"

            record_sale(dk, txn)
            dialog.dismiss()

            d = MDDialog(
                title="Payment Complete",
                text=msg,
                buttons=[MDFlatButton(text="OK", on_release=lambda x: d.dismiss())],
            )
            d.open()

            self.cart.clear()
            self.refresh_cart()
            self.refresh_items()

        dialog = MDDialog(
            title="Payment",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(
                    text="CONFIRM",
                    md_bg_color=[0.15, 0.68, 0.38, 1],
                    on_release=confirm_payment,
                ),
            ],
        )
        self._pay_dialog = dialog
        dialog.open()

    def _set_pay_method(self, method, box):
        self._pay_method = method
        for child in box.children:
            if hasattr(child, 'text'):
                if child.text.lower() == method or (
                    method == "mpesa" and child.text == "M-Pesa"
                ):
                    child.md_bg_color = [0.15, 0.68, 0.38, 1]
                    child.text_color = [1, 1, 1, 1]
                else:
                    child.md_bg_color = [0.8, 0.8, 0.8, 1]
                    child.text_color = [0, 0, 0, 1]

    def show_report(self, *args):
        self.manager.current = "report"

    def show_debts(self, *args):
        self.manager.current = "debts"

    def show_admin(self, *args):
        if self.app and self.app.current_user and self.app.current_user["role"] == "admin":
            self.manager.current = "admin"
        else:
            from kivymd.uix.dialog import MDDialog
            from kivymd.uix.button import MDFlatButton
            dialog = MDDialog(
                title="Denied",
                text="Admin access required.",
                buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())],
            )
            dialog.open()
