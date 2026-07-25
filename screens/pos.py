from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle

BG = (0.07, 0.07, 0.14, 1)
CARD = (0.12, 0.12, 0.20, 1)
SURFACE = (0.14, 0.14, 0.24, 1)
INPUT_BG = (0.16, 0.16, 0.26, 1)
ACCENT = (0.42, 0.28, 0.82, 1)
SUCCESS = (0.2, 0.78, 0.55, 1)
DANGER = (0.95, 0.3, 0.3, 1)
WARNING = (1.0, 0.65, 0.1, 1)
GOLD = (1.0, 0.78, 0.2, 1)
WHITE = (1, 1, 1, 1)
MUTED = (0.5, 0.5, 0.6, 1)
HINT = (0.4, 0.4, 0.5, 1)
DIVIDER = (0.2, 0.2, 0.3, 1)

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


class POSScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.cart = []
        self.all_items = {}
        self.categories = {}
        self.current_category = "All"
        self._cart_expanded = False

    def set_app(self, app):
        self.app = app

    def on_enter(self):
        if not self.ids:
            self.build_ui()
        self._touch_session()
        self._load_data()
        self._refresh_items()
        self._refresh_cart_bar()
        self._update_user_label()
        if self._cart_expanded:
            self._collapse_cart()

    def _touch_session(self):
        from backend.database import session
        if not session.is_logged_in():
            self.manager.current = "login"
            return
        self.app.current_user = session.get_user()
        session.touch()

    def build_ui(self):
        self.clear_widgets()
        self.root_box = BoxLayout(orientation="vertical")

        with self.root_box.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=self.root_box.pos, size=self.root_box.size)
        self.root_box.bind(pos=self._update_bg, size=self._update_bg)

        self._build_top_bar()
        self._build_search()
        self._build_categories()
        self._build_items_area()
        self._build_cart_bar()
        self._build_cart_overlay()

        self.add_widget(self.root_box)
        Clock.schedule_once(lambda dt: self._load_data(), 0.1)

    def _build_top_bar(self):
        bar = BoxLayout(
            size_hint_y=None, height=56,
            padding=[14, 0, 14, 0], spacing=8,
        )
        with bar.canvas.before:
            Color(*CARD)
            bar._bg = Rectangle(pos=bar.pos, size=bar.size)
        bar.bind(pos=lambda s, _: s._bg.__setattr__("pos", s.pos))
        bar.bind(size=lambda s, _: s._bg.__setattr__("size", s.size))

        bar.add_widget(Label(
            text="Sweet Waters",
            font_size="18sp", color=WHITE, bold=True,
            size_hint_x=0.40,
        ))

        self.user_label = Label(
            text="", font_size="11sp", color=GOLD,
            size_hint_x=0.25,
        )
        bar.add_widget(self.user_label)

        btn_box = BoxLayout(spacing=4, size_hint_x=0.35)
        for text, action, color in [
            ("\U0001f4ca", self._goto_report, (0.18, 0.4, 0.7, 1)),
            ("\U0001f4b5", self._goto_debts, (0.75, 0.25, 0.25, 1)),
            ("\u2699\ufe0f", self._goto_admin, (0.35, 0.38, 0.42, 1)),
        ]:
            btn = Button(
                text=text, font_size="18sp",
                background_color=color, color=WHITE,
                size_hint_x=0.33, background_normal="",
            )
            btn.bind(on_release=action)
            btn_box.add_widget(btn)
        bar.add_widget(btn_box)
        self.root_box.add_widget(bar)

    def _build_search(self):
        self.search_input = TextInput(
            hint_text="  \U0001f50d  Search drinks...",
            size_hint_y=None, height=46,
            multiline=False, font_size="15sp",
            background_color=INPUT_BG, background_normal="",
            foreground_color=WHITE, cursor_color=ACCENT,
            hint_text_color=HINT, padding=[12, 10, 12, 10],
        )
        self.search_input.bind(text=self._on_search)
        self.root_box.add_widget(self.search_input)

    def _build_categories(self):
        self.cat_scroll = ScrollView(
            size_hint_y=None, height=44,
            do_scroll_x=True, do_scroll_y=False,
            bar_color=(0.3, 0.3, 0.4, 0.5),
        )
        self.cat_box = BoxLayout(
            size_hint_y=None, height=40,
            size_hint_x=None, spacing=6,
            padding=[8, 4, 8, 4],
        )
        self.cat_box.bind(minimum_width=self.cat_box.setter("width"))
        self.cat_scroll.add_widget(self.cat_box)
        self.root_box.add_widget(self.cat_scroll)

    def _build_items_area(self):
        self.items_scroll = ScrollView(
            bar_width=4, bar_color=(0.3, 0.3, 0.4, 0.3),
        )
        self.items_grid = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=8,
            padding=[6, 6, 6, 6],
        )
        self.items_grid.bind(minimum_height=self.items_grid.setter("height"))
        self.items_scroll.add_widget(self.items_grid)
        self.root_box.add_widget(self.items_scroll)

    def _build_cart_bar(self):
        self.cart_bar = BoxLayout(
            size_hint_y=None, height=64,
            padding=[16, 8, 16, 8], spacing=12,
        )
        with self.cart_bar.canvas.before:
            Color(*CARD)
            self._cart_bar_bg = Rectangle(pos=self.cart_bar.pos, size=self.cart_bar.size)
            Color(*DIVIDER)
            self._cart_bar_line = Rectangle(
                pos=(self.cart_bar.x, self.cart_bar.y + self.cart_bar.height - 1),
                size=(self.cart_bar.width, 1),
            )
        self.cart_bar.bind(pos=self._update_cart_bar_bg, size=self._update_cart_bar_bg)

        self.cart_icon = Label(
            text="\U0001f6d2", font_size="24sp", size_hint_x=0.12,
        )
        self.cart_bar.add_widget(self.cart_icon)

        info = BoxLayout(orientation="vertical", size_hint_x=0.50)
        self.cart_count_label = Label(
            text="Cart empty", font_size="13sp", color=MUTED,
            size_hint_y=0.5, halign="left",
        )
        self.cart_count_label.bind(size=self.cart_count_label.setter("text_size"))
        self.cart_total_label = Label(
            text="KES 0", font_size="16sp", color=WHITE, bold=True,
            size_hint_y=0.5, halign="left",
        )
        self.cart_total_label.bind(size=self.cart_total_label.setter("text_size"))
        info.add_widget(self.cart_count_label)
        info.add_widget(self.cart_total_label)
        self.cart_bar.add_widget(info)

        self.checkout_btn = Button(
            text="CHECKOUT", font_size="14sp", bold=True,
            background_color=SUCCESS, color=WHITE,
            size_hint_x=0.30, background_normal="",
        )
        self.checkout_btn.bind(on_release=self._checkout)
        self.cart_bar.add_widget(self.checkout_btn)

        self.cart_bar.bind(on_touch_down=self._on_cart_bar_touch)
        self.root_box.add_widget(self.cart_bar)

    def _build_cart_overlay(self):
        self.cart_overlay = BoxLayout(
            orientation="vertical", size_hint=(1, 1),
            opacity=0,
        )
        with self.cart_overlay.canvas.before:
            Color(0, 0, 0, 0.7)
            self._overlay_bg = Rectangle(pos=self.cart_overlay.pos, size=self.cart_overlay.size)
        self.cart_overlay.bind(pos=self._update_overlay_bg, size=self._update_overlay_bg)

        overlay_card = BoxLayout(
            orientation="vertical", size_hint=(0.95, 0.88),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        with overlay_card.canvas.before:
            Color(*CARD)
            self._overlay_card_bg = RoundedRectangle(
                pos=overlay_card.pos, size=overlay_card.size, radius=[20],
            )
        overlay_card.bind(pos=self._update_overlay_card, size=self._update_overlay_card)

        oh_header = BoxLayout(size_hint_y=None, height=56, padding=[16, 0, 16, 0])
        oh_header.add_widget(Label(
            text="\U0001f6d2  Your Order",
            font_size="18sp", color=WHITE, bold=True, halign="left",
        ))
        self.overlay_count = Label(
            text="0 items", font_size="13sp", color=MUTED,
        )
        oh_header.add_widget(self.overlay_count)
        close_btn = Button(
            text="\u2715", font_size="20sp", size_hint_x=None, width=44,
            background_color=DANGER, color=WHITE, background_normal="",
        )
        close_btn.bind(on_release=lambda x: self._collapse_cart())
        oh_header.add_widget(close_btn)
        overlay_card.add_widget(oh_header)

        self.cart_items_box = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=4,
            padding=[8, 4, 8, 4],
        )
        self.cart_items_box.bind(minimum_height=self.cart_items_box.setter("height"))
        cart_scroll = ScrollView(bar_width=4)
        cart_scroll.add_widget(self.cart_items_box)
        overlay_card.add_widget(cart_scroll)

        oh_footer = BoxLayout(
            orientation="vertical", size_hint_y=None, height=130,
            spacing=8, padding=[16, 8, 16, 8],
        )

        self.overlay_total = Label(
            text="TOTAL: KES 0", font_size="22sp", color=WHITE, bold=True,
            size_hint_y=None, height=40,
        )
        oh_footer.add_widget(self.overlay_total)

        pay_box = BoxLayout(spacing=8, size_hint_y=None, height=44)
        self._pay_method = "cash"
        self._method_btns = {}
        for m, lbl in [("cash", "\U0001f4b5 Cash"), ("mpesa", "\U0001f4f1 M-Pesa"), ("credit", "\U0001f4b3 Credit")]:
            btn = Button(
                text=lbl, font_size="12sp",
                background_color=SUCCESS if m == "cash" else SURFACE,
                color=WHITE, background_normal="",
            )
            btn.m = m
            btn.bind(on_release=lambda x: self._select_method(x.m))
            self._method_btns[m] = btn
            pay_box.add_widget(btn)
        oh_footer.add_widget(pay_box)

        action_box = BoxLayout(spacing=8, size_hint_y=None, height=48)
        self._clear_overlay_btn = Button(
            text="Clear Cart", font_size="13sp",
            background_color=DANGER, color=WHITE, background_normal="",
        )
        self._clear_overlay_btn.bind(on_release=lambda x: self._clear_cart())
        self._confirm_pay_btn = Button(
            text="CONFIRM PAYMENT", font_size="14sp", bold=True,
            background_color=SUCCESS, color=WHITE, background_normal="",
        )
        self._confirm_pay_btn.bind(on_release=lambda x: self._confirm_payment())
        action_box.add_widget(self._clear_overlay_btn)
        action_box.add_widget(self._confirm_pay_btn)
        oh_footer.add_widget(action_box)

        overlay_card.add_widget(oh_footer)
        self.cart_overlay.add_widget(overlay_card)
        self.root_box.add_widget(self.cart_overlay)

    def _update_bg(self, *args):
        self._bg.pos = self.root_box.pos
        self._bg.size = self.root_box.size

    def _update_cart_bar_bg(self, *args):
        self._cart_bar_bg.pos = self.cart_bar.pos
        self._cart_bar_bg.size = self.cart_bar.size
        self._cart_bar_line.pos = (self.cart_bar.x, self.cart_bar.y + self.cart_bar.height - 1)
        self._cart_bar_line.size = (self.cart_bar.width, 1)

    def _update_overlay_bg(self, *args):
        self._overlay_bg.pos = self.cart_overlay.pos
        self._overlay_bg.size = self.cart_overlay.size

    def _update_overlay_card(self, *args):
        card = self.cart_overlay.children[0]
        self._overlay_card_bg.pos = card.pos
        self._overlay_card_bg.size = card.size

    def _on_cart_bar_touch(self, touch):
        if self.cart_bar.collide_point(*touch.pos) and not self._cart_expanded:
            if self.cart:
                self._expand_cart()
            return True
        return False

    def _expand_cart(self):
        self._cart_expanded = True
        self.cart_overlay.opacity = 1
        self._refresh_cart_overlay()

    def _collapse_cart(self):
        self._cart_expanded = False
        self.cart_overlay.opacity = 0

    def _load_data(self):
        from backend.stock import get_categories, get_stock_list
        self.all_items = get_stock_list()
        self.categories = get_categories()
        self._build_category_buttons()
        self._refresh_items()

    def _update_user_label(self):
        if self.app and self.app.current_user:
            u = self.app.current_user
            self.user_label.text = f"{u['display_name']}"

    def _build_category_buttons(self):
        self.cat_box.clear_widgets()
        all_btn = Button(
            text="All", font_size="12sp", size_hint_x=None, width=56,
            background_color=ACCENT, color=WHITE, background_normal="",
        )
        all_btn.bind(on_release=lambda x: self._select_category("All"))
        self.cat_box.add_widget(all_btn)

        for cat_name in sorted(self.categories.keys()):
            icon = CATEGORY_ICONS.get(cat_name, "\U0001f37d\ufe0f")
            btn = Button(
                text=f"{icon}", font_size="18sp",
                size_hint_x=None, width=50,
                background_color=SURFACE, color=WHITE, background_normal="",
            )
            btn.cat_name = cat_name
            btn.bind(on_release=lambda x: self._select_category(x.cat_name))
            btn.bind(on_touch_down=lambda b, t, cn=cat_name: self._show_cat_tooltip(b, t, cn))
            self.cat_box.add_widget(btn)
        self._highlight_category()

    def _show_cat_tooltip(self, btn, touch, cat_name):
        pass

    def _highlight_category(self):
        for child in self.cat_box.children:
            if hasattr(child, 'text') and child.text in ("All",) or (hasattr(child, 'cat_name') if hasattr(child, 'cat_name') else False):
                pass
        for child in self.cat_box.children:
            text = child.text if hasattr(child, 'text') else ""
            cat = getattr(child, 'cat_name', None)
            if text == "All" and self.current_category == "All":
                child.background_color = ACCENT
            elif cat == self.current_category:
                child.background_color = ACCENT
            else:
                child.background_color = SURFACE

    def _select_category(self, cat_name):
        self.current_category = cat_name
        self.search_input.text = ""
        self._highlight_category()
        self._refresh_items()

    def _on_search(self, instance, text):
        self._refresh_items()

    def _refresh_items(self):
        query = self.search_input.text.strip().lower()
        if query:
            items = [n for n in self.all_items if query in n.lower()]
        elif self.current_category == "All":
            items = list(self.all_items.keys())
        else:
            items = self.categories.get(self.current_category, [])

        self.items_grid.clear_widgets()
        self.items_grid.height = 0

        cols = 3
        row_box = None
        cell_w = 1.0 / cols

        for i, name in enumerate(items):
            info = self.all_items.get(name)
            if not info:
                continue
            from backend.stock import get_effective_price
            price = get_effective_price(name)
            cat = info.get("category", "Other")
            icon = CATEGORY_ICONS.get(cat, CATEGORY_ICONS["Other"])

            if i % cols == 0:
                row_box = BoxLayout(
                    orientation="horizontal", size_hint_y=None, height=100,
                    spacing=6,
                )
                self.items_grid.add_widget(row_box)

            cell = BoxLayout(
                orientation="vertical",
                size_hint_x=cell_w, size_hint_y=None, height=100,
                spacing=2, padding=[4, 6, 4, 6],
            )
            with cell.canvas.before:
                Color(*(0.14, 0.14, 0.24, 1))
                cell._bg = RoundedRectangle(pos=cell.pos, size=cell.size, radius=[12])
                Color(*(ACCENT[0], ACCENT[1], ACCENT[2], 0.0))
                cell._border = RoundedRectangle(
                    pos=(cell.x, cell.y), size=cell.size, radius=[12],
                )
            cell.bind(pos=lambda c, *_: (setattr(c._bg, 'pos', c.pos), setattr(c._border, 'pos', (c.x, c.y))))
            cell.bind(size=lambda c, *_: (setattr(c._bg, 'size', c.size), setattr(c._border, 'size', c.size)))

            cell.add_widget(Label(
                text=icon, font_size="28sp", size_hint_y=0.40,
                color=WHITE,
            ))
            cell.add_widget(Label(
                text=name, font_size="10sp", size_hint_y=0.30,
                color=WHITE, halign="center", shorten=True,
                shorten_from="right", text_size=(None, None),
            ))
            cell.add_widget(Label(
                text=f"KES {price:,.0f}", font_size="11sp", size_hint_y=0.30,
                color=GOLD,
            ))

            item_name = name
            cell.bind(on_touch_down=lambda c, t, n=item_name: self._on_item_touch(c, t, n))
            row_box.add_widget(cell)

        remainder = len(items) % cols
        if remainder > 0 and row_box is not None:
            for _ in range(cols - remainder):
                row_box.add_widget(Label(size_hint_x=cell_w))

        total_rows = (len(items) + cols - 1) // cols if items else 0
        self.items_grid.height = total_rows * 106

    def _on_item_touch(self, cell, touch, name):
        if cell.collide_point(*touch.pos):
            self._add_to_cart(name)
            return True
        return False

    def _add_to_cart(self, name):
        self._touch_session()
        from backend.stock import get_effective_price
        price = get_effective_price(name)
        for i, (n, q, p) in enumerate(self.cart):
            if n == name:
                self.cart[i] = (n, q + 1, p)
                self._refresh_cart_bar()
                if self._cart_expanded:
                    self._refresh_cart_overlay()
                return
        self.cart.append((name, 1, price))
        self._refresh_cart_bar()
        if self._cart_expanded:
            self._refresh_cart_overlay()

    def _cart_plus(self, name):
        self._touch_session()
        for i, (n, q, p) in enumerate(self.cart):
            if n == name:
                self.cart[i] = (n, q + 1, p)
                self._refresh_cart_bar()
                if self._cart_expanded:
                    self._refresh_cart_overlay()
                return

    def _cart_minus(self, name):
        self._touch_session()
        for i, (n, q, p) in enumerate(self.cart):
            if n == name:
                if q > 1:
                    self.cart[i] = (n, q - 1, p)
                else:
                    self.cart.pop(i)
                self._refresh_cart_bar()
                if self._cart_expanded:
                    self._refresh_cart_overlay()
                return

    def _clear_cart(self):
        self._touch_session()
        self.cart.clear()
        self._refresh_cart_bar()
        if self._cart_expanded:
            self._refresh_cart_overlay()

    def _refresh_cart_bar(self):
        total = sum(q * p for _, q, p in self.cart)
        count = sum(q for _, q, _ in self.cart)
        if count > 0:
            self.cart_count_label.text = f"{count} item{'s' if count != 1 else ''}"
            self.cart_count_label.color = WHITE
        else:
            self.cart_count_label.text = "Cart empty"
            self.cart_count_label.color = MUTED
        self.cart_total_label.text = f"KES {total:,.0f}"

    def _refresh_cart_overlay(self):
        total = sum(q * p for _, q, p in self.cart)
        count = sum(q for _, q, _ in self.cart)
        self.overlay_count.text = f"{count} item{'s' if count != 1 else ''}"
        self.overlay_total.text = f"TOTAL: KES {total:,.0f}"

        self.cart_items_box.clear_widgets()
        self.cart_items_box.height = 0

        for name, qty, price in self.cart:
            row = BoxLayout(
                orientation="horizontal", size_hint_y=None, height=52,
                spacing=8, padding=[8, 4, 8, 4],
            )
            with row.canvas.before:
                Color(*(0.14, 0.14, 0.24, 1))
                row._bg = RoundedRectangle(pos=row.pos, size=row.size, radius=[10])
            row.bind(pos=lambda r, _: r._bg.__setattr__("pos", r.pos))
            row.bind(size=lambda r, _: r._bg.__setattr__("size", r.size))

            info = BoxLayout(orientation="vertical", size_hint_x=0.50)
            info.add_widget(Label(
                text=name, font_size="13sp", color=WHITE,
                halign="left", text_size=(None, None),
                size_hint_y=0.55,
            ))
            info.add_widget(Label(
                text=f"KES {price:,.0f} each", font_size="10sp", color=MUTED,
                halign="left", text_size=(None, None),
                size_hint_y=0.45,
            ))
            row.add_widget(info)

            minus = Button(
                text="\u2212", font_size="18sp", size_hint_x=None, width=40,
                background_color=DANGER, color=WHITE, background_normal="",
            )
            item_n = name
            minus.bind(on_release=lambda x, n=item_n: self._cart_minus(n))
            row.add_widget(minus)

            row.add_widget(Label(
                text=str(qty), font_size="16sp", color=WHITE,
                size_hint_x=None, width=36,
            ))

            plus = Button(
                text="+", font_size="18sp", size_hint_x=None, width=40,
                background_color=SUCCESS, color=WHITE, background_normal="",
            )
            plus.bind(on_release=lambda x, n=item_n: self._cart_plus(n))
            row.add_widget(plus)

            self.cart_items_box.add_widget(row)

        self.cart_items_box.height = len(self.cart) * 56

    def _select_method(self, method):
        self._pay_method = method
        for m, btn in self._method_btns.items():
            btn.background_color = SUCCESS if m == method else SURFACE

    def _checkout(self, *args):
        self._touch_session()
        if not self.cart:
            return
        self._expand_cart()

    def _confirm_payment(self):
        if not self.cart:
            return

        total = sum(q * p for _, q, p in self.cart)
        method = self._pay_method

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
            txn["cash_received"] = total
            txn["change"] = 0
        elif method == "mpesa":
            txn["mpesa_amount"] = total
        elif method == "credit":
            content = BoxLayout(orientation="vertical", spacing=12, padding=20)
            content.add_widget(Label(
                text=f"Credit sale: KES {total:,.0f}",
                font_size="16sp", color=WHITE, bold=True,
            ))
            cust_input = TextInput(
                hint_text="Customer name",
                size_hint_y=None, height=44, multiline=False,
                font_size="15sp",
                background_color=INPUT_BG, background_normal="",
                foreground_color=WHITE, cursor_color=ACCENT,
                hint_text_color=HINT, padding=[12, 10],
            )
            content.add_widget(cust_input)
            btn_box = BoxLayout(spacing=8, size_hint_y=None, height=48)
            cancel = Button(text="Cancel", background_color=SURFACE, color=MUTED, background_normal="")
            confirm = Button(text="CONFIRM", background_color=SUCCESS, color=WHITE, bold=True, background_normal="")
            btn_box.add_widget(cancel)
            btn_box.add_widget(confirm)
            content.add_widget(btn_box)

            popup = Popup(
                title="Credit Sale", content=content,
                size_hint=(0.85, 0.45), auto_dismiss=False,
                background_color=CARD, title_color=WHITE,
                separator_color=DIVIDER,
            )
            cancel.bind(on_release=popup.dismiss)
            confirm.bind(on_release=lambda x: self._confirm_credit(popup, txn, dk))
            popup.open()
            return

        record_sale(dk, txn)
        self.cart.clear()
        self._refresh_cart_bar()
        self._collapse_cart()
        self._refresh_items()
        session.touch()

    def _confirm_credit(self, popup, txn, dk):
        cust = popup.children[0].children[1].text.strip()
        if not cust:
            return
        from backend.sales import record_sale
        from backend.database import session
        txn["customer"] = cust
        record_sale(dk, txn)
        popup.dismiss()
        self.cart.clear()
        self._refresh_cart_bar()
        self._collapse_cart()
        self._refresh_items()
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
            return

        items_str = ", ".join(f"{n}x{q}" for n, q in last.get("items", {}).items())
        content = BoxLayout(orientation="vertical", spacing=12, padding=20)
        content.add_widget(Label(
            text=f"Undo this sale?\n\n"
                 f"Time: {last.get('time', '')}\n"
                 f"Cashier: {last.get('cashier', '')}\n"
                 f"Items: {items_str}\n"
                 f"Total: KES {last.get('total', 0):,.0f}",
            font_size="14sp", halign="center",
            text_size=(280, None), color=WHITE,
        ))
        btn_box = BoxLayout(spacing=10, size_hint_y=None, height=48)
        cancel = Button(text="Cancel", background_color=SURFACE, color=MUTED, background_normal="")
        undo = Button(text="Undo Sale", background_color=DANGER, color=WHITE, background_normal="")
        btn_box.add_widget(cancel)
        btn_box.add_widget(undo)
        content.add_widget(btn_box)

        popup = Popup(
            title="Confirm Undo", content=content,
            size_hint=(0.85, 0.50), auto_dismiss=False,
            background_color=CARD, title_color=DANGER,
            separator_color=DIVIDER,
        )
        cancel.bind(on_release=popup.dismiss)
        undo.bind(on_release=lambda x: (popup.dismiss(), self._do_undo(dk)))
        popup.open()

    def _do_undo(self, dk):
        from backend.sales import undo_last_sale
        undo_last_sale(dk)
        self._refresh_items()
        self._refresh_cart_bar()

    def _goto_report(self, *args):
        self._touch_session()
        self.manager.current = "report"

    def _goto_debts(self, *args):
        self._touch_session()
        self.manager.current = "debts"

    def _goto_admin(self, *args):
        self._touch_session()
        from backend.database import session
        user = session.get_user()
        if user and user["role"] == "admin":
            self.manager.current = "admin"
