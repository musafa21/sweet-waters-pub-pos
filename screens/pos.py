from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle

BG_DARK = (0.06, 0.06, 0.12, 1)
BG_CARD = (0.10, 0.10, 0.18, 1)
BG_INPUT = (0.14, 0.14, 0.24, 1)
BG_ITEM = (0.12, 0.12, 0.20, 1)
BG_ITEM_PRESS = (0.16, 0.14, 0.28, 1)
ACCENT = (0.36, 0.24, 0.73, 1)
ACCENT_BRIGHT = (0.48, 0.32, 0.92, 1)
SUCCESS = (0.2, 0.78, 0.55, 1)
DANGER = (0.91, 0.27, 0.27, 1)
WARNING = (0.95, 0.65, 0.06, 1)
TEXT_PRIMARY = (1, 1, 1, 1)
TEXT_SECONDARY = (0.65, 0.65, 0.75, 1)
TEXT_MUTED = (0.45, 0.45, 0.55, 1)
BORDER_COLOR = (0.22, 0.22, 0.32, 1)

CATEGORY_ICONS = {
    "Beers & Lagers": "\U0001f37a",
    "Rum & Spirits": "\U0001f378",
    "Whiskey": "\U0001f943",
    "Gin": "\U0001f377",
    "Vodka": "\U0001f379",
    "Wines": "\U0001f377",
    "Water & Soft Drinks": "\U0001f9c4",
    "Other": "\U0001f37d\ufe0f",
}


class ItemView(RecycleDataViewBehavior, BoxLayout):
    index = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = [6, 8, 6, 8]
        self.spacing = 2
        self._icon_label = Label(
            font_size="26sp", size_hint_y=None, height=32, color=TEXT_PRIMARY,
        )
        self._name_label = Label(
            font_size="11sp", size_hint_y=None, height=16,
            color=TEXT_PRIMARY, text_size=(None, None),
            halign="center", shorten=True, shorten_from="right",
        )
        self._price_label = Label(
            font_size="12sp", size_hint_y=None, height=16,
            color=ACCENT_BRIGHT,
        )
        self.add_widget(self._icon_label)
        self.add_widget(self._name_label)
        self.add_widget(self._price_label)
        with self.canvas.before:
            Color(*BG_ITEM)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self._name_label.text = data.get("name", "")
        self._price_label.text = data.get("price_text", "")
        cat = data.get("category", "Other")
        icon = CATEGORY_ICONS.get(cat, CATEGORY_ICONS["Other"])
        self._icon_label.text = icon


class CartItemView(RecycleDataViewBehavior, BoxLayout):
    index = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.padding = [10, 6, 10, 6]
        self.spacing = 8
        self._info = Label(
            text="", font_size="12sp", halign="left", valign="center",
            size_hint_x=0.5, color=TEXT_PRIMARY,
        )
        self._info.bind(size=self._info.setter("text_size"))
        self._qty_label = Label(
            text="", font_size="14sp", size_hint_x=0.12, color=TEXT_PRIMARY,
        )
        self._minus_btn = Button(text="\u2212", size_hint_x=0.14, font_size="16sp",
                                 background_color=BG_INPUT, color=DANGER,
                                 background_normal="")
        self._plus_btn = Button(text="+", size_hint_x=0.14, font_size="16sp",
                                background_color=BG_INPUT, color=SUCCESS,
                                background_normal="")
        self.add_widget(self._info)
        self.add_widget(self._minus_btn)
        self.add_widget(self._qty_label)
        self.add_widget(self._plus_btn)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        name = data.get("name", "")
        qty = data.get("qty", 1)
        price = data.get("price", 0)
        self._info.text = f"{name}\nKES {price:,.0f}"
        self._qty_label.text = str(qty)
        self._minus_btn.bind(on_release=lambda x: rv.parent_app.cart_minus(name))
        self._plus_btn.bind(on_release=lambda x: rv.parent_app.cart_plus(name))


class POSScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.cart = []
        self.all_items = {}
        self.categories = {}
        self.current_category = ""
        self.category_buttons = []
        self.search_text = ""

    def set_app(self, app):
        self.app = app

    def on_enter(self):
        if not self.ids:
            self.build_ui()
        self._touch_session()
        self.refresh_items()
        self.refresh_cart()
        self.update_header()

    def _touch_session(self):
        from backend.database import session
        if not session.is_logged_in():
            self.manager.current = "login"
            return
        self.app.current_user = session.get_user()
        session.touch()

    def build_ui(self):
        self.clear_widgets()
        main = BoxLayout(orientation="vertical", size_hint=(1, 1))

        with main.canvas.before:
            Color(*BG_DARK)
            self._main_bg = Rectangle(pos=main.pos, size=main.size)
        main.bind(pos=self._update_main_bg, size=self._update_main_bg)

        top_bar = BoxLayout(
            size_hint_y=None, height=52,
            padding=[14, 0, 14, 0], spacing=10,
        )
        with top_bar.canvas.before:
            Color(*BG_CARD)
            self._top_bg = Rectangle(pos=top_bar.pos, size=top_bar.size)
            Color(*BORDER_COLOR)
            self._top_border = Line(points=[0, 0, 0, 0], width=0.5)
        top_bar.bind(pos=self._update_top_bg, size=self._update_top_bg)

        top_bar.add_widget(Label(
            text="SWEET WATERS PUB",
            font_size="15sp", size_hint_x=0.30,
            color=TEXT_PRIMARY, bold=True,
        ))
        self.user_label = Label(
            text="", font_size="10sp", size_hint_x=0.22,
            color=WARNING, halign="center",
        )
        top_bar.add_widget(self.user_label)

        btn_box = BoxLayout(spacing=6, size_hint_x=0.48)
        for text, action, color in [
            ("\u2139 Report", self.show_report, (0.14, 0.38, 0.62, 1)),
            ("\u2696 Debts", self.show_debts, (0.72, 0.22, 0.22, 1)),
            ("\u2699 Admin", self.show_admin, (0.35, 0.38, 0.42, 1)),
        ]:
            btn = Button(
                text=text, font_size="11sp",
                background_color=color, color=TEXT_PRIMARY,
                size_hint_x=0.33, background_normal="",
            )
            btn.bind(on_release=action)
            btn_box.add_widget(btn)
        top_bar.add_widget(btn_box)
        main.add_widget(top_bar)

        content = BoxLayout(spacing=6, padding=6)

        left = BoxLayout(orientation="vertical", size_hint_x=0.58)

        self.search_field = TextInput(
            hint_text="  \U0001f50d  Search items...",
            size_hint_y=None, height=42,
            multiline=False, font_size="14sp",
            background_color=BG_INPUT, background_normal="",
            foreground_color=TEXT_PRIMARY, cursor_color=ACCENT_BRIGHT,
            hint_text_color=TEXT_MUTED, padding=[10, 10, 10, 10],
        )
        self.search_field.bind(text=self.on_search)
        left.add_widget(self.search_field)

        self.cat_scroll = ScrollView(
            size_hint_y=None, height=38,
            do_scroll_x=True, do_scroll_y=False,
        )
        self.cat_box = BoxLayout(
            size_hint_y=None, height=36, spacing=6,
            size_hint_x=None, padding=[0, 2],
        )
        self.cat_box.bind(minimum_width=self.cat_box.setter("width"))
        self.cat_scroll.add_widget(self.cat_box)
        left.add_widget(self.cat_scroll)

        self.items_rv = RecycleView(
            viewclass=ItemView,
            size_hint_y=1,
        )
        self.items_rv.parent_app = self
        self.items_rv.layout_manager = RecycleBoxLayout(
            default_size_hint=(None, None),
            default_size=(105, 85),
            orientation="vertical",
            cols=3,
            spacing=8,
            padding=8,
        )
        self.items_rv.layout_manager.bind(minimum_height=self.items_rv.layout_manager.setter("height"))
        left.add_widget(self.items_rv)

        content.add_widget(left)

        right = BoxLayout(orientation="vertical", size_hint_x=0.42)
        with right.canvas.before:
            Color(*BG_CARD)
            self._right_bg = Rectangle(pos=right.pos, size=right.size)
        right.bind(pos=self._update_right_bg, size=self._update_right_bg)

        cart_header = BoxLayout(size_hint_y=None, height=40, padding=[12, 0])
        cart_header.add_widget(Label(
            text="CART", font_size="13sp", color=TEXT_PRIMARY, bold=True,
        ))
        self.cart_count_label = Label(
            text="0", font_size="11sp", color=ACCENT_BRIGHT,
        )
        cart_header.add_widget(self.cart_count_label)
        clear_btn = Button(text="Clear", size_hint_x=0.3, font_size="10sp",
                           background_color=DANGER, color=TEXT_PRIMARY,
                           background_normal="")
        clear_btn.bind(on_release=lambda x: self.clear_cart())
        cart_header.add_widget(clear_btn)
        right.add_widget(cart_header)

        self.cart_rv = RecycleView(
            viewclass=CartItemView,
            size_hint_y=1,
        )
        self.cart_rv.parent_app = self
        self.cart_rv.layout_manager = RecycleBoxLayout(
            default_size_hint=(1, None),
            default_size=(None, 48),
            orientation="vertical",
            spacing=4,
            padding=6,
        )
        self.cart_rv.layout_manager.bind(minimum_height=self.cart_rv.layout_manager.setter("height"))
        right.add_widget(self.cart_rv)

        self.total_label = Label(
            text="TOTAL: KES 0",
            font_size="18sp", size_hint_y=None, height=48,
            color=TEXT_PRIMARY, bold=True,
        )
        right.add_widget(self.total_label)

        checkout_btn = Button(
            text="C H E C K O U T",
            size_hint_y=None, height=50,
            background_color=SUCCESS, color=TEXT_PRIMARY,
            font_size="15sp", bold=True, background_normal="",
        )
        checkout_btn.bind(on_release=self.checkout)
        right.add_widget(checkout_btn)

        undo_btn = Button(
            text="Undo Last Sale",
            size_hint_y=None, height=36,
            background_color=BG_INPUT, color=TEXT_SECONDARY,
            font_size="11sp", background_normal="",
        )
        undo_btn.bind(on_release=lambda x: self.undo_sale())
        right.add_widget(undo_btn)

        content.add_widget(right)
        main.add_widget(content)
        self.add_widget(main)

        Clock.schedule_once(lambda dt: self.init_data(), 0.1)

    def _update_main_bg(self, *args):
        self._main_bg.pos = self.children[0].pos
        self._main_bg.size = self.children[0].size

    def _update_top_bg(self, *args):
        self._top_bg.pos = self.children[0].children[2].pos
        self._top_bg.size = self.children[0].children[2].size

    def _update_right_bg(self, *args):
        pass

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
        self.category_buttons = []
        all_btn = Button(
            text="All", font_size="11sp", size_hint_x=None, width=60,
            background_color=ACCENT, color=TEXT_PRIMARY,
            background_normal="",
        )
        all_btn.bind(on_release=lambda x: self.select_category("All"))
        self.cat_box.add_widget(all_btn)
        self.category_buttons.append(("All", all_btn))

        for cat_name in sorted(self.categories.keys()):
            icon = CATEGORY_ICONS.get(cat_name, "\U0001f37d\ufe0f")
            btn = Button(
                text=f"{icon} {cat_name}", font_size="10sp",
                size_hint_x=None, width=130,
                background_color=BG_INPUT, color=TEXT_SECONDARY,
                background_normal="",
            )
            btn.bind(on_release=lambda x, c=cat_name: self.select_category(c))
            self.cat_box.add_widget(btn)
            self.category_buttons.append((cat_name, btn))

        if self.categories and not self.current_category:
            self.current_category = "All"
        self.highlight_category()

    def highlight_category(self):
        for cat_name, btn in self.category_buttons:
            if cat_name == self.current_category:
                btn.background_color = ACCENT
                btn.color = TEXT_PRIMARY
            else:
                btn.background_color = BG_INPUT
                btn.color = TEXT_SECONDARY

    def select_category(self, cat_name):
        self.current_category = cat_name
        self.search_field.text = ""
        self.highlight_category()
        self.refresh_items()

    def refresh_items(self):
        query = self.search_field.text.strip().lower()
        if query:
            items = [n for n in self.all_items if query in n.lower()]
        elif self.current_category == "All":
            items = list(self.all_items.keys())
        else:
            items = self.categories.get(self.current_category, [])

        rv_data = []
        for name in items:
            info = self.all_items.get(name)
            if not info:
                continue
            from backend.stock import get_effective_price
            price = get_effective_price(name)
            cat = info.get("category", "Other")
            icon = CATEGORY_ICONS.get(cat, CATEGORY_ICONS["Other"])
            rv_data.append({
                "name": name,
                "icon": icon,
                "price": price,
                "price_text": f"KES {price:,.0f}",
                "category": cat,
            })
        self.items_rv.data = rv_data

    def on_search(self, instance, text):
        self.search_text = text
        self.refresh_items()

    def add_item(self, name):
        if not self.app:
            return
        self._touch_session()
        from backend.stock import get_effective_price
        info = self.all_items.get(name)
        if not info:
            return
        price = get_effective_price(name)
        for i, (n, q, p) in enumerate(self.cart):
            if n == name:
                self.cart[i] = (n, q + 1, p)
                self.refresh_cart()
                return
        self.cart.append((name, 1, price))
        self.refresh_cart()

    def cart_plus(self, name):
        self._touch_session()
        for i, (n, q, p) in enumerate(self.cart):
            if n == name:
                self.cart[i] = (n, q + 1, p)
                self.refresh_cart()
                return

    def cart_minus(self, name):
        self._touch_session()
        for i, (n, q, p) in enumerate(self.cart):
            if n == name:
                if q > 1:
                    self.cart[i] = (n, q - 1, p)
                else:
                    self.cart.pop(i)
                self.refresh_cart()
                return

    def clear_cart(self):
        self._touch_session()
        if self.cart:
            self.cart.clear()
            self.refresh_cart()

    def refresh_cart(self):
        total = 0
        rv_data = []
        for name, qty, price in self.cart:
            total += qty * price
            rv_data.append({"name": name, "qty": qty, "price": price})
        self.cart_rv.data = rv_data
        self.total_label.text = f"TOTAL: KES {total:,.0f}"
        self.cart_count_label.text = str(sum(q for _, q, _ in self.cart))

    def checkout(self, *args):
        self._touch_session()
        if not self.cart:
            return
        total = sum(q * p for _, q, p in self.cart)
        self.show_payment_dialog(total)

    def show_payment_dialog(self, total):
        content = BoxLayout(orientation="vertical", spacing=12, padding=20)

        content.add_widget(Label(
            text=f"KES {total:,.0f}",
            font_size="28sp", size_hint_y=None, height=48,
            color=TEXT_PRIMARY, bold=True,
        ))
        content.add_widget(Label(
            text="Total Due",
            font_size="13sp", size_hint_y=None, height=20,
            color=TEXT_SECONDARY,
        ))

        method_box = BoxLayout(spacing=6, size_hint_y=None, height=42)
        self._pay_method = "cash"
        self._method_btns = {}
        for m, lbl in [("cash", "Cash"), ("mpesa", "M-Pesa"), ("credit", "Credit")]:
            btn = Button(
                text=lbl, font_size="12sp",
                background_color=SUCCESS if m == "cash" else BG_INPUT,
                color=TEXT_PRIMARY, background_normal="",
            )
            btn.method = m
            btn.bind(on_release=lambda x: self._select_method(x.method))
            self._method_btns[m] = btn
            method_box.add_widget(btn)
        content.add_widget(method_box)

        self._pay_amount = TextInput(
            hint_text="Amount", input_filter="float",
            size_hint_y=None, height=44, font_size="18sp",
            multiline=False, text=str(int(total)),
            background_color=BG_INPUT, background_normal="",
            foreground_color=TEXT_PRIMARY, cursor_color=ACCENT_BRIGHT,
            hint_text_color=TEXT_MUTED, padding=[12, 10],
        )
        content.add_widget(self._pay_amount)

        self._pay_customer = TextInput(
            hint_text="Customer Name (for credit)",
            size_hint_y=None, height=44, multiline=False,
            background_color=BG_INPUT, background_normal="",
            foreground_color=TEXT_PRIMARY, cursor_color=ACCENT_BRIGHT,
            hint_text_color=TEXT_MUTED, padding=[12, 10],
        )
        content.add_widget(self._pay_customer)

        btn_box = BoxLayout(spacing=10, size_hint_y=None, height=48)
        cancel_btn = Button(text="Cancel", background_color=BG_INPUT,
                            color=TEXT_SECONDARY, background_normal="")
        confirm_btn = Button(text="CONFIRM", background_color=SUCCESS,
                             color=TEXT_PRIMARY, font_size="14sp", bold=True,
                             background_normal="")
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(confirm_btn)
        content.add_widget(btn_box)

        popup = Popup(
            title="", content=content,
            size_hint=(0.92, 0.7), auto_dismiss=False,
            background_color=BG_CARD,
            separator_color=BORDER_COLOR,
            title_color=TEXT_PRIMARY,
        )
        cancel_btn.bind(on_release=popup.dismiss)
        confirm_btn.bind(on_release=lambda x: self._confirm_payment(popup, total))
        popup.open()

    def _select_method(self, method):
        self._pay_method = method
        for m, btn in self._method_btns.items():
            btn.background_color = SUCCESS if m == method else BG_INPUT

    def _confirm_payment(self, popup, total):
        try:
            amt = float(self._pay_amount.text or 0)
        except ValueError:
            amt = 0

        method = self._pay_method
        if method == "cash" and amt < total:
            return
        if method == "credit":
            cust = self._pay_customer.text.strip()
            if not cust:
                return

        from backend.database import today_key, session
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
            "cashier": session.get_user()["display_name"],
        }
        if method == "cash":
            txn["cash_received"] = amt
            txn["change"] = amt - total
        elif method == "mpesa":
            txn["mpesa_amount"] = amt
        elif method == "credit":
            txn["customer"] = self._pay_customer.text.strip()

        record_sale(dk, txn)
        popup.dismiss()
        self.cart.clear()
        self.refresh_cart()
        self.refresh_items()
        session.touch()

    def undo_sale(self):
        from backend.database import today_key, session
        user = session.get_user()
        if not user:
            return
        dk = today_key()
        from backend.sales import load_sales
        sales = load_sales(dk)
        txns = sales.get("transactions", [])
        if not txns:
            return
        last = txns[-1]

        if last.get("cashier") != user["display_name"] and user["role"] != "admin":
            content = BoxLayout(orientation="vertical", spacing=12, padding=20)
            content.add_widget(Label(
                text="Only admin can undo\nanother cashier's sale.",
                font_size="14sp", halign="center", color=TEXT_PRIMARY,
            ))
            popup = Popup(title="Access Denied", content=content,
                          size_hint=(0.8, 0.35), auto_dismiss=False,
                          background_color=BG_CARD, title_color=DANGER,
                          separator_color=BORDER_COLOR)
            ok_btn = Button(text="OK", background_color=BG_INPUT,
                            color=TEXT_PRIMARY, size_hint_y=None, height=44,
                            background_normal="")
            ok_btn.bind(on_release=popup.dismiss)
            content.add_widget(ok_btn)
            popup.open()
            return

        content = BoxLayout(orientation="vertical", spacing=12, padding=20)
        items_str = ", ".join(f"{n}x{q}" for n, q in last.get("items", {}).items())
        content.add_widget(Label(
            text=f"Undo sale?\nTime: {last.get('time', '')}\n"
                 f"Cashier: {last.get('cashier', '')}\n"
                 f"Items: {items_str}\n"
                 f"Total: KES {last.get('total', 0):,.0f}",
            font_size="14sp", halign="center",
            text_size=(300, None), color=TEXT_PRIMARY,
        ))
        btn_box = BoxLayout(spacing=10, size_hint_y=None, height=48)
        cancel_btn = Button(text="Cancel", background_color=BG_INPUT,
                            color=TEXT_SECONDARY, background_normal="")
        undo_btn = Button(text="Undo", background_color=DANGER,
                          color=TEXT_PRIMARY, background_normal="")
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(undo_btn)
        content.add_widget(btn_box)

        popup = Popup(title="Confirm", content=content, size_hint=(0.85, 0.55),
                      auto_dismiss=False, background_color=BG_CARD,
                      title_color=TEXT_PRIMARY, separator_color=BORDER_COLOR)
        cancel_btn.bind(on_release=popup.dismiss)
        undo_btn.bind(on_release=lambda x: (popup.dismiss(), self._do_undo(dk)))
        popup.open()

    def _do_undo(self, dk):
        from backend.sales import undo_last_sale
        undo_last_sale(dk)
        self.refresh_items()

    def show_report(self, *args):
        self._touch_session()
        self.manager.current = "report"

    def show_debts(self, *args):
        self._touch_session()
        self.manager.current = "debts"

    def show_admin(self, *args):
        self._touch_session()
        from backend.database import session
        user = session.get_user()
        if user and user["role"] == "admin":
            self.manager.current = "admin"
