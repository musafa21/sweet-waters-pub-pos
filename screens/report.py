from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, RoundedRectangle

BG = (0.07, 0.07, 0.14, 1)
CARD = (0.12, 0.12, 0.20, 1)
SURFACE = (0.14, 0.14, 0.24, 1)
INPUT_BG = (0.16, 0.16, 0.26, 1)
ACCENT = (0.42, 0.28, 0.82, 1)
SUCCESS = (0.2, 0.78, 0.55, 1)
DANGER = (0.95, 0.3, 0.3, 1)
WARNING = (1.0, 0.65, 0.1, 1)
INFO = (0.18, 0.4, 0.7, 1)
GOLD = (1.0, 0.78, 0.2, 1)
WHITE = (1, 1, 1, 1)
MUTED = (0.5, 0.5, 0.6, 1)
HINT = (0.4, 0.4, 0.5, 1)
DIVIDER = (0.2, 0.2, 0.3, 1)


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
        main = BoxLayout(orientation="vertical")

        with main.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=main.pos, size=main.size)
        main.bind(pos=lambda s, _: self._bg.__setattr__("pos", s.pos))
        main.bind(size=lambda s, _: self._bg.__setattr__("size", s.size))

        header = BoxLayout(size_hint_y=None, height=56, padding=[14, 0, 14, 0], spacing=8)
        with header.canvas.before:
            Color(*CARD)
            header._bg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda s, _: s._bg.__setattr__("pos", s.pos))
        header.bind(size=lambda s, _: s._bg.__setattr__("size", s.size))
        header.add_widget(Label(
            text="\U0001f4ca  Daily Report",
            font_size="17sp", color=WHITE, bold=True, size_hint_x=0.40,
        ))
        date_row = BoxLayout(orientation="horizontal", size_hint_x=0.38, spacing=4)
        prev_btn = Button(text="<", font_size="15sp", size_hint_x=0.22,
                          background_color=SURFACE, color=WHITE, background_normal="")
        self.date_label = Label(
            text=self.date_key, font_size="13sp", color=WHITE,
            size_hint_x=0.56,
        )
        next_btn = Button(text=">", font_size="15sp", size_hint_x=0.22,
                          background_color=SURFACE, color=WHITE, background_normal="")
        prev_btn.bind(on_release=lambda x: self._shift_date(-1))
        next_btn.bind(on_release=lambda x: self._shift_date(1))
        date_row.add_widget(prev_btn)
        date_row.add_widget(self.date_label)
        date_row.add_widget(next_btn)
        header.add_widget(date_row)
        go_btn = Button(text="Today", size_hint_x=0.18, font_size="13sp",
                        background_color=ACCENT, color=WHITE, background_normal="")
        go_btn.bind(on_release=self.go_today)
        header.add_widget(go_btn)
        main.add_widget(header)

        from backend.sales import load_sales, get_payment_summary
        sales = load_sales(self.date_key)
        ps = get_payment_summary(sales)
        total_rev = sales.get("total_revenue", 0)

        stats = BoxLayout(size_hint_y=None, height=80, spacing=8, padding=[10, 8])
        for label, value, color in [
            ("Revenue", f"KES {total_rev:,.0f}", ACCENT),
            ("Cash", f"KES {ps['cash']:,.0f}", SUCCESS),
            ("M-Pesa", f"KES {ps['mpesa']:,.0f}", INFO),
        ]:
            card = BoxLayout(orientation="vertical", padding=[8, 6], spacing=2)
            with card.canvas.before:
                Color(*CARD)
                card._bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[10])
                Color(*color)
                card._accent = Rectangle(pos=(card.x, card.y), size=(3, card.height))
            card.bind(pos=lambda c, *_: (setattr(c._bg, 'pos', c.pos), setattr(c._accent, 'pos', (c.x, c.y))))
            card.bind(size=lambda c, *_: (setattr(c._bg, 'size', c.size), setattr(c._accent, 'size', (3, c.height))))
            card.add_widget(Label(text=label, font_size="10sp", color=MUTED,
                                  size_hint_y=0.45))
            card.add_widget(Label(text=value, font_size="13sp", color=color,
                                  size_hint_y=0.55, bold=True))
            stats.add_widget(card)
        main.add_widget(stats)

        tabs = BoxLayout(size_hint_y=None, height=44, spacing=6, padding=[10, 4])
        self._tab_btns = []
        for tab_name in ["Sales", "Transactions", "Stock"]:
            btn = Button(
                text=tab_name, font_size="12sp",
                background_color=SURFACE, color=MUTED,
                background_normal="",
            )
            btn.tab_name = tab_name
            btn.bind(on_release=lambda x: self.show_tab(x.tab_name))
            tabs.add_widget(btn)
            self._tab_btns.append(btn)
        main.add_widget(tabs)

        self._tab_scroll = ScrollView(bar_width=4, bar_color=(0.3, 0.3, 0.4, 0.3))
        self._tab_content = BoxLayout(orientation="vertical", size_hint_y=None, padding=[8, 4])
        self._tab_content.bind(minimum_height=self._tab_content.setter("height"))
        self._tab_scroll.add_widget(self._tab_content)
        main.add_widget(self._tab_scroll)

        bottom = BoxLayout(size_hint_y=None, height=56, spacing=8, padding=8)
        back_btn = Button(text="Back to POS", font_size="13sp",
                          background_color=SURFACE, color=MUTED, background_normal="")
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'pos'))
        bottom.add_widget(back_btn)
        undo_btn = Button(text="Undo Last Sale", font_size="13sp",
                          background_color=DANGER, color=WHITE, background_normal="")
        undo_btn.bind(on_release=lambda x: self.undo_sale())
        bottom.add_widget(undo_btn)
        main.add_widget(bottom)

        self.add_widget(main)
        self.show_tab("Sales")

    def go_today(self, *args):
        from backend.database import today_key
        self.date_key = today_key()
        self.build_ui()

    def _shift_date(self, direction):
        from datetime import datetime, timedelta
        try:
            dt = datetime.strptime(self.date_key, "%Y-%m-%d")
        except ValueError:
            return
        dt += timedelta(days=direction)
        self.date_key = dt.strftime("%Y-%m-%d")
        self.build_ui()

    def show_tab(self, tab_name):
        from backend.database import session, haptic_click
        haptic_click()
        session.touch()
        self._tab_content.clear_widgets()
        self._tab_content.height = 0

        for btn in self._tab_btns:
            if btn.tab_name == tab_name:
                btn.background_color = ACCENT
                btn.color = WHITE
            else:
                btn.background_color = SURFACE
                btn.color = MUTED

        from backend.sales import load_sales
        from backend.stock import get_effective_price, calc_remaining_stock, get_stock_list

        sales = load_sales(self.date_key)

        if tab_name == "Sales":
            items = sorted(sales.get("items", {}).items())
            for name, qty in items:
                price = get_effective_price(name, self.date_key)
                rev = qty * price
                row = BoxLayout(
                    size_hint_y=None, height=42, padding=[8, 4],
                    spacing=4,
                )
                with row.canvas.before:
                    Color(*(0.12, 0.12, 0.20, 1))
                    row._bg = RoundedRectangle(pos=row.pos, size=row.size, radius=[8])
                row.bind(pos=lambda r, _: r._bg.__setattr__("pos", r.pos))
                row.bind(size=lambda r, _: r._bg.__setattr__("size", r.size))
                row.add_widget(Label(text=name, font_size="13sp", halign="left",
                                     size_hint_x=0.50, text_size=(None, None),
                                     color=WHITE))
                row.add_widget(Label(text=f"x{qty}", font_size="12sp",
                                     size_hint_x=0.20, color=MUTED))
                row.add_widget(Label(text=f"KES {rev:,.0f}", font_size="12sp",
                                     size_hint_x=0.30, color=GOLD, halign="right"))
                self._tab_content.add_widget(row)
            if not items:
                self._tab_content.add_widget(Label(
                    text="No sales data today", size_hint_y=None, height=60,
                    color=MUTED, font_size="14sp"))
            self._tab_content.height = len(items) * 46

        elif tab_name == "Transactions":
            txns = list(reversed(sales.get("transactions", [])))
            for t in txns:
                method = t.get("payment_method", "cash").upper()
                items_str = ", ".join(f"{n}x{q}" for n, q in t.get("items", {}).items())
                row = BoxLayout(orientation="vertical", size_hint_y=None, height=68,
                                padding=[10, 6], spacing=2)
                with row.canvas.before:
                    Color(*(0.12, 0.12, 0.20, 1))
                    row._bg = RoundedRectangle(pos=row.pos, size=row.size, radius=[8])
                row.bind(pos=lambda r, _: r._bg.__setattr__("pos", r.pos))
                row.bind(size=lambda r, _: r._bg.__setattr__("size", r.size))
                row.add_widget(Label(
                    text=f"{t.get('time', '')}  |  {t.get('cashier', '')}  |  {method}  |  KES {t.get('total', 0):,.0f}",
                    font_size="12sp", halign="left", size_hint_y=0.5,
                    text_size=(None, None), color=WHITE))
                row.add_widget(Label(
                    text=items_str, font_size="10sp", halign="left",
                    size_hint_y=0.5, text_size=(None, None),
                    color=MUTED))
                self._tab_content.add_widget(row)
            if not txns:
                self._tab_content.add_widget(Label(
                    text="No transactions today", size_hint_y=None, height=60,
                    color=MUTED, font_size="14sp"))
            self._tab_content.height = len(txns) * 72

        elif tab_name == "Stock":
            remaining = calc_remaining_stock(self.date_key)
            items_list = sorted(get_stock_list().keys())
            for name in items_list:
                rem = max(0, remaining.get(name, 0))
                if rem <= 0:
                    tag = "  OUT"
                    tag_color = DANGER
                elif rem <= 3:
                    tag = "  LOW"
                    tag_color = WARNING
                else:
                    tag = ""
                    tag_color = WHITE
                row = BoxLayout(size_hint_y=None, height=38, padding=[8, 4])
                with row.canvas.before:
                    Color(*(0.12, 0.12, 0.20, 1))
                    row._bg = RoundedRectangle(pos=row.pos, size=row.size, radius=[8])
                row.bind(pos=lambda r, _: r._bg.__setattr__("pos", r.pos))
                row.bind(size=lambda r, _: r._bg.__setattr__("size", r.size))
                row.add_widget(Label(
                    text=f"{name}: {rem}{tag}",
                    font_size="13sp", halign="left", text_size=(None, None),
                    color=tag_color))
                self._tab_content.add_widget(row)
            self._tab_content.height = len(items_list) * 42

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
        items_str = ", ".join(f"{n}x{q}" for n, q in last.get("items", {}).items())
        content = BoxLayout(orientation="vertical", spacing=12, padding=16)
        content.add_widget(Label(
            text=f"Undo this sale?\n{last.get('time', '')}  |  KES {last.get('total', 0):,.0f}\n{items_str}",
            font_size="14sp", color=WHITE, halign="center",
        ))
        btns = BoxLayout(spacing=8, size_hint_y=None, height=44)
        cancel_btn = Button(text="Cancel", background_color=SURFACE, color=MUTED, background_normal="")
        confirm_btn = Button(text="UNDO", background_color=DANGER, color=WHITE, bold=True, background_normal="")
        btns.add_widget(cancel_btn)
        btns.add_widget(confirm_btn)
        content.add_widget(btns)
        popup = Popup(
            title="Confirm Undo", content=content,
            size_hint=(0.85, 0.50), auto_dismiss=False,
            background_color=CARD, title_color=WHITE,
            separator_color=DIVIDER,
        )
        cancel_btn.bind(on_release=popup.dismiss)
        confirm_btn.bind(on_release=lambda x: self._do_undo(popup, dk))
        popup.open()

    def _do_undo(self, popup, dk):
        popup.dismiss()
        from backend.sales import undo_last_sale
        from backend.database import session
        undo_last_sale(dk)
        session.touch()
        self.date_key = dk
        self.build_ui()
