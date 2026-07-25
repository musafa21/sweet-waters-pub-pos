from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, Line

BG_DARK = (0.06, 0.06, 0.12, 1)
BG_CARD = (0.10, 0.10, 0.18, 1)
BG_INPUT = (0.14, 0.14, 0.24, 1)
ACCENT = (0.36, 0.24, 0.73, 1)
ACCENT_BRIGHT = (0.48, 0.32, 0.92, 1)
SUCCESS = (0.2, 0.78, 0.55, 1)
DANGER = (0.91, 0.27, 0.27, 1)
WARNING = (0.95, 0.65, 0.06, 1)
INFO = (0.14, 0.38, 0.62, 1)
TEXT_PRIMARY = (1, 1, 1, 1)
TEXT_SECONDARY = (0.65, 0.65, 0.75, 1)
TEXT_MUTED = (0.45, 0.45, 0.55, 1)
BORDER_COLOR = (0.22, 0.22, 0.32, 1)


class ReportScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.date_key = ""

    def set_app(self, app):
        self.app = app

    def on_enter(self):
        from backend.database import today_key, session
        if not session.is_logged_in():
            self.manager.current = "login"
            return
        session.touch()
        self.app.current_user = session.get_user()
        if not self.date_key:
            self.date_key = today_key()
        self.build_ui()

    def build_ui(self):
        self.clear_widgets()
        main = BoxLayout(orientation="vertical", size_hint=(1, 1))

        with main.canvas.before:
            Color(*BG_DARK)
            self._main_bg = Rectangle(pos=main.pos, size=main.size)
        main.bind(pos=lambda s, _: self._main_bg.__setattr__("pos", s.pos))
        main.bind(size=lambda s, _: self._main_bg.__setattr__("size", s.size))

        header = BoxLayout(size_hint_y=None, height=52, padding=[14, 0, 14, 0], spacing=8)
        with header.canvas.before:
            Color(*BG_CARD)
            header._bg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda s, _: s._bg.__setattr__("pos", s.pos))
        header.bind(size=lambda s, _: s._bg.__setattr__("size", s.size))
        header.add_widget(Label(
            text="DAILY REPORT", font_size="16sp", color=TEXT_PRIMARY, bold=True,
        ))
        self.date_field = TextInput(
            text=self.date_key, size_hint_x=0.35, size_hint_y=None,
            height=36, multiline=False, font_size="13sp",
            background_color=BG_INPUT, background_normal="",
            foreground_color=TEXT_PRIMARY, cursor_color=ACCENT_BRIGHT,
            hint_text_color=TEXT_MUTED, padding=[8, 8],
        )
        header.add_widget(self.date_field)
        go_btn = Button(text="Go", size_hint_x=0.15, font_size="12sp",
                        background_color=ACCENT, color=TEXT_PRIMARY,
                        background_normal="")
        go_btn.bind(on_release=self.go_to_date)
        header.add_widget(go_btn)
        main.add_widget(header)

        from backend.sales import load_sales, get_payment_summary
        sales = load_sales(self.date_key)
        ps = get_payment_summary(sales)
        total_rev = sales.get("total_revenue", 0)

        stats = BoxLayout(size_hint_y=None, height=70, spacing=8, padding=8)
        for label, value, color in [
            ("Revenue", f"KES {total_rev:,.0f}", ACCENT),
            ("Cash", f"KES {ps['cash']:,.0f}", SUCCESS),
            ("M-Pesa", f"KES {ps['mpesa']:,.0f}", INFO),
        ]:
            card = BoxLayout(orientation="vertical", padding=8)
            with card.canvas.before:
                Color(*BG_CARD)
                card._bg = Rectangle(pos=card.pos, size=card.size)
            card.bind(pos=lambda s, _: s._bg.__setattr__("pos", s.pos))
            card.bind(size=lambda s, _: s._bg.__setattr__("size", s.size))
            card.add_widget(Label(text=label, font_size="10sp", color=TEXT_MUTED,
                                  size_hint_y=None, height=20))
            card.add_widget(Label(text=value, font_size="14sp", color=color,
                                  size_hint_y=None, height=26, bold=True))
            stats.add_widget(card)
        main.add_widget(stats)

        tabs = BoxLayout(size_hint_y=None, height=40, spacing=6, padding=[8, 4])
        self._tab_btns = []
        for tab_name in ["Sales", "Transactions", "Stock"]:
            btn = Button(
                text=tab_name, font_size="12sp",
                background_color=BG_INPUT, color=TEXT_SECONDARY,
                background_normal="",
            )
            btn.tab_name = tab_name
            btn.bind(on_release=lambda x: self.show_tab(x.tab_name))
            tabs.add_widget(btn)
            self._tab_btns.append(btn)
        main.add_widget(tabs)

        self._tab_scroll = ScrollView()
        self._tab_content = BoxLayout(orientation="vertical", size_hint_y=None, padding=[8, 4])
        self._tab_content.bind(minimum_height=self._tab_content.setter("height"))
        self._tab_scroll.add_widget(self._tab_content)
        main.add_widget(self._tab_scroll)

        bottom = BoxLayout(size_hint_y=None, height=48, spacing=8, padding=8)
        back_btn = Button(text="Back to POS", font_size="13sp",
                          background_color=BG_INPUT, color=TEXT_SECONDARY,
                          background_normal="")
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'pos'))
        bottom.add_widget(back_btn)
        undo_btn = Button(text="Undo Last", font_size="13sp",
                          background_color=DANGER, color=TEXT_PRIMARY,
                          background_normal="")
        undo_btn.bind(on_release=lambda x: self.undo_sale())
        bottom.add_widget(undo_btn)
        main.add_widget(bottom)

        self.add_widget(main)
        self.show_tab("Sales")

    def show_tab(self, tab_name):
        from backend.database import session
        session.touch()
        self._tab_content.clear_widgets()

        for btn in self._tab_btns:
            if btn.tab_name == tab_name:
                btn.background_color = ACCENT
                btn.color = TEXT_PRIMARY
            else:
                btn.background_color = BG_INPUT
                btn.color = TEXT_SECONDARY

        from backend.sales import load_sales
        from backend.stock import get_effective_price, calc_remaining_stock, get_stock_list

        sales = load_sales(self.date_key)

        if tab_name == "Sales":
            for name, qty in sorted(sales.get("items", {}).items()):
                price = get_effective_price(name, self.date_key)
                rev = qty * price
                row = BoxLayout(size_hint_y=None, height=38, padding=[8, 4])
                row.add_widget(Label(text=name, font_size="13sp", halign="left",
                                     size_hint_x=0.5, text_size=(None, None),
                                     color=TEXT_PRIMARY))
                row.add_widget(Label(text=f"Qty: {qty}", font_size="12sp",
                                     size_hint_x=0.25, color=TEXT_SECONDARY))
                row.add_widget(Label(text=f"KES {rev:,.0f}", font_size="12sp",
                                     size_hint_x=0.25, color=ACCENT_BRIGHT))
                self._tab_content.add_widget(row)
            if not sales.get("items"):
                self._tab_content.add_widget(Label(
                    text="No sales data", size_hint_y=None, height=50,
                    color=TEXT_MUTED))

        elif tab_name == "Transactions":
            for t in reversed(sales.get("transactions", [])):
                method = t.get("payment_method", "cash").upper()
                items_str = ", ".join(f"{n}x{q}" for n, q in t.get("items", {}).items())
                row = BoxLayout(orientation="vertical", size_hint_y=None, height=64,
                                padding=[10, 6])
                row.add_widget(Label(
                    text=f"{t.get('time', '')} | {t.get('cashier', '')} | {method} | KES {t.get('total', 0):,.0f}",
                    font_size="12sp", halign="left", size_hint_y=None, height=22,
                    text_size=(None, None), color=TEXT_PRIMARY))
                row.add_widget(Label(
                    text=items_str, font_size="11sp", halign="left",
                    size_hint_y=None, height=18, text_size=(None, None),
                    color=TEXT_MUTED))
                self._tab_content.add_widget(row)
            if not sales.get("transactions"):
                self._tab_content.add_widget(Label(
                    text="No transactions", size_hint_y=None, height=50,
                    color=TEXT_MUTED))

        elif tab_name == "Stock":
            remaining = calc_remaining_stock(self.date_key)
            for name in sorted(get_stock_list().keys()):
                rem = remaining.get(name, 0)
                tag = ""
                tag_color = TEXT_PRIMARY
                if rem <= 0:
                    tag = "  OUT OF STOCK"
                    tag_color = DANGER
                elif rem <= 3:
                    tag = "  LOW"
                    tag_color = WARNING
                self._tab_content.add_widget(Label(
                    text=f"{name}: {rem}{tag}",
                    font_size="13sp", halign="left", size_hint_y=None, height=34,
                    padding=[8, 4], text_size=(None, None),
                    color=tag_color))

    def go_to_date(self, *args):
        dk = self.date_field.text.strip()
        from datetime import datetime
        try:
            datetime.strptime(dk, "%Y-%m-%d")
        except ValueError:
            return
        self.date_key = dk
        self.build_ui()

    def undo_sale(self):
        from backend.database import today_key, session
        if not session.is_logged_in():
            return
        dk = today_key()
        from backend.sales import load_sales, undo_last_sale
        sales = load_sales(dk)
        txns = sales.get("transactions", [])
        if not txns:
            return
        last = txns[-1]
        user = session.get_user()
        if last.get("cashier") != user["display_name"] and user["role"] != "admin":
            return
        undo_last_sale(dk)
        session.touch()
        self.date_key = dk
        self.build_ui()
