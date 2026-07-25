from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle, Line

BG_DARK = (0.06, 0.06, 0.12, 1)
BG_CARD = (0.10, 0.10, 0.18, 1)
BG_INPUT = (0.14, 0.14, 0.24, 1)
ACCENT = (0.36, 0.24, 0.73, 1)
ACCENT_BRIGHT = (0.48, 0.32, 0.92, 1)
SUCCESS = (0.2, 0.78, 0.55, 1)
DANGER = (0.91, 0.27, 0.27, 1)
TEXT_PRIMARY = (1, 1, 1, 1)
TEXT_SECONDARY = (0.65, 0.65, 0.75, 1)
TEXT_MUTED = (0.45, 0.45, 0.55, 1)
BORDER_COLOR = (0.22, 0.22, 0.32, 1)


class DebtScreen(Screen):
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
        session.touch()
        self.app.current_user = session.get_user()
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
            text="DEBT MANAGEMENT", font_size="16sp", color=TEXT_PRIMARY, bold=True,
        ))
        main.add_widget(header)

        from backend.debts import get_all_debts, calc_debt_outstanding
        all_debts = get_all_debts()
        outstanding = [d for d in all_debts if calc_debt_outstanding(d) > 0]
        total_out = sum(calc_debt_outstanding(d) for d in outstanding)

        summary = BoxLayout(size_hint_y=None, height=60, spacing=8, padding=8)
        for label, value, color in [
            ("Outstanding", str(len(outstanding)), DANGER),
            ("Total", f"KES {total_out:,.0f}", DANGER),
        ]:
            card = BoxLayout(orientation="vertical", padding=8, size_hint_x=0.5)
            with card.canvas.before:
                Color(*BG_CARD)
                card._bg = Rectangle(pos=card.pos, size=card.size)
                Color(*color)
                card._accent = Rectangle(pos=(card.x, card.y), size=(4, card.height))
            card.bind(pos=lambda s, _: (s._bg.__setattr__("pos", s.pos), s._accent.__setattr__("pos", (s.x, s.y))))
            card.bind(size=lambda s, _: (s._bg.__setattr__("size", s.size), s._accent.__setattr__("size", (4, s.height))))
            card.add_widget(Label(text=label, font_size="11sp", color=TEXT_MUTED))
            card.add_widget(Label(text=value, font_size="18sp", color=color, bold=True))
            summary.add_widget(card)
        main.add_widget(summary)

        scroll = ScrollView()
        debt_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=6, padding=8)
        debt_box.bind(minimum_height=debt_box.setter("height"))

        for d in all_debts:
            total = d.get("total", 0)
            paid = sum(s["amount"] for s in d.get("settlements", []))
            balance = total - paid
            status = "SETTLED" if balance <= 0 else "OUTSTANDING"
            status_color = SUCCESS if balance <= 0 else DANGER

            row = BoxLayout(orientation="vertical", size_hint_y=None, height=90,
                            padding=[12, 8], spacing=4)
            with row.canvas.before:
                Color(*BG_CARD)
                row._bg = Rectangle(pos=row.pos, size=row.size)
            row.bind(pos=lambda s, _: s._bg.__setattr__("pos", s.pos))
            row.bind(size=lambda s, _: s._bg.__setattr__("size", s.size))

            top = BoxLayout(size_hint_y=None, height=24)
            top.add_widget(Label(
                text=f"{d.get('customer', '?')}",
                font_size="14sp", halign="left", text_size=(None, None),
                color=TEXT_PRIMARY, bold=True,
            ))
            top.add_widget(Label(
                text=status, font_size="11sp", color=status_color,
                size_hint_x=0.3,
            ))
            row.add_widget(top)

            items_str = ", ".join(f"{n}x{q}" for n, q in d.get("items", {}).items())
            row.add_widget(Label(
                text=f"Total: KES {total:,.0f}  |  Balance: KES {balance:,.0f}",
                font_size="12sp", halign="left", size_hint_y=None, height=20,
                text_size=(None, None), color=TEXT_SECONDARY,
            ))
            row.add_widget(Label(
                text=f"{d.get('date', '')} | {items_str}",
                font_size="10sp", halign="left", size_hint_y=None, height=18,
                text_size=(None, None), color=TEXT_MUTED,
            ))

            if balance > 0:
                settle_btn = Button(
                    text="Settle", font_size="11sp", size_hint_x=0.25,
                    background_color=SUCCESS, color=TEXT_PRIMARY,
                    background_normal="",
                )
                settle_btn.bind(on_release=lambda x, dd=d: self.settle_debt(dd))
                row.add_widget(settle_btn)
            else:
                row.add_widget(Label(size_hint_x=0.25))

            debt_box.add_widget(row)

        if not all_debts:
            debt_box.add_widget(Label(
                text="No debts found", size_hint_y=None, height=50,
                color=TEXT_MUTED))

        scroll.add_widget(debt_box)
        main.add_widget(scroll)

        bottom = BoxLayout(size_hint_y=None, height=48, padding=8)
        back_btn = Button(text="Back to POS", font_size="13sp",
                          background_color=BG_INPUT, color=TEXT_SECONDARY,
                          background_normal="")
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'pos'))
        bottom.add_widget(back_btn)
        main.add_widget(bottom)

        self.add_widget(main)

    def settle_debt(self, debt):
        from backend.debts import calc_debt_outstanding
        balance = calc_debt_outstanding(debt)

        content = BoxLayout(orientation="vertical", spacing=12, padding=20)
        content.add_widget(Label(
            text=f"{debt.get('customer', '?')}",
            font_size="20sp", halign="center", color=TEXT_PRIMARY, bold=True,
        ))
        content.add_widget(Label(
            text=f"Outstanding: KES {balance:,.0f}",
            font_size="16sp", halign="center", color=DANGER,
        ))

        method_box = BoxLayout(spacing=6, size_hint_y=None, height=42)
        self._settle_method = "cash"
        self._settle_method_btns = {}
        for m, lbl in [("cash", "Cash"), ("mpesa", "M-Pesa")]:
            btn = Button(
                text=lbl, font_size="12sp",
                background_color=SUCCESS if m == "cash" else BG_INPUT,
                color=TEXT_PRIMARY, background_normal="",
            )
            btn.m = m
            btn.bind(on_release=lambda x: self._pick_method(x.m))
            self._settle_method_btns[m] = btn
            method_box.add_widget(btn)
        content.add_widget(method_box)

        self._settle_amount = TextInput(
            text=str(int(balance)), hint_text="Amount",
            input_filter="float", size_hint_y=None, height=44,
            font_size="16sp", multiline=False,
            background_color=BG_INPUT, background_normal="",
            foreground_color=TEXT_PRIMARY, cursor_color=ACCENT_BRIGHT,
            hint_text_color=TEXT_MUTED, padding=[12, 10],
        )
        content.add_widget(self._settle_amount)

        btn_box = BoxLayout(spacing=10, size_hint_y=None, height=48)
        cancel_btn = Button(text="Cancel", background_color=BG_INPUT,
                            color=TEXT_SECONDARY, background_normal="")
        confirm_btn = Button(text="CONFIRM", background_color=SUCCESS,
                             color=TEXT_PRIMARY, background_normal="")
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(confirm_btn)
        content.add_widget(btn_box)

        popup = Popup(title="Settle Debt", content=content, size_hint=(0.9, 0.65),
                      auto_dismiss=False, background_color=BG_CARD,
                      title_color=TEXT_PRIMARY, separator_color=BORDER_COLOR)
        cancel_btn.bind(on_release=popup.dismiss)
        confirm_btn.bind(on_release=lambda x: self._confirm_settle(popup, debt))
        popup.open()

    def _pick_method(self, method):
        self._settle_method = method
        for m, btn in self._settle_method_btns.items():
            btn.background_color = SUCCESS if m == method else BG_INPUT

    def _confirm_settle(self, popup, debt):
        try:
            amt = float(self._settle_amount.text)
        except ValueError:
            return
        if amt <= 0:
            return
        from backend.database import session
        from backend.debts import settle_debt as do_settle
        do_settle(debt.get("id"), debt["_date_key"], amt, self._settle_method)
        session.touch()
        popup.dismiss()
        self.build_ui()
