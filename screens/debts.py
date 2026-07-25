from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle, RoundedRectangle

BG = (0.07, 0.07, 0.14, 1)
CARD = (0.12, 0.12, 0.20, 1)
SURFACE = (0.14, 0.14, 0.24, 1)
INPUT_BG = (0.16, 0.16, 0.26, 1)
ACCENT = (0.42, 0.28, 0.82, 1)
SUCCESS = (0.2, 0.78, 0.55, 1)
DANGER = (0.95, 0.3, 0.3, 1)
WHITE = (1, 1, 1, 1)
MUTED = (0.5, 0.5, 0.6, 1)
HINT = (0.4, 0.4, 0.5, 1)
DIVIDER = (0.2, 0.2, 0.3, 1)


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
            text="\U0001f4b5  Debts",
            font_size="18sp", color=WHITE, bold=True,
        ))
        main.add_widget(header)

        from backend.debts import get_all_debts, calc_debt_outstanding
        all_debts = get_all_debts()
        outstanding = [d for d in all_debts if calc_debt_outstanding(d) > 0]
        total_out = sum(calc_debt_outstanding(d) for d in outstanding)

        summary = BoxLayout(size_hint_y=None, height=80, spacing=8, padding=[10, 8])
        for label, value, color in [
            ("Outstanding", f"{len(outstanding)}", DANGER),
            ("Total Owed", f"KES {total_out:,.0f}", DANGER),
        ]:
            card = BoxLayout(orientation="vertical", padding=[10, 6], spacing=2)
            with card.canvas.before:
                Color(*CARD)
                card._bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[10])
                Color(*color)
                card._accent = Rectangle(pos=(card.x, card.y), size=(3, card.height))
            card.bind(pos=lambda c, *_: (setattr(c._bg, 'pos', c.pos), setattr(c._accent, 'pos', (c.x, c.y))))
            card.bind(size=lambda c, *_: (setattr(c._bg, 'size', c.size), setattr(c._accent, 'size', (3, c.height))))
            card.add_widget(Label(text=label, font_size="11sp", color=MUTED,
                                  size_hint_y=0.45))
            card.add_widget(Label(text=value, font_size="18sp", color=color,
                                  size_hint_y=0.55, bold=True))
            summary.add_widget(card)
        main.add_widget(summary)

        scroll = ScrollView(bar_width=4, bar_color=(0.3, 0.3, 0.4, 0.3))
        debt_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=6, padding=[10, 6])
        debt_box.bind(minimum_height=debt_box.setter("height"))

        for d in all_debts:
            total = d.get("total", 0)
            paid = sum(s["amount"] for s in d.get("settlements", []))
            balance = total - paid
            status = "PAID" if balance <= 0 else "OWED"
            status_color = SUCCESS if balance <= 0 else DANGER

            card = BoxLayout(
                orientation="vertical", size_hint_y=None, height=100,
                padding=[14, 10], spacing=4,
            )
            with card.canvas.before:
                Color(*CARD)
                card._bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[12])
                Color(*status_color)
                card._accent = Rectangle(pos=(card.x, card.y), size=(4, card.height))
            card.bind(pos=lambda c, *_: (setattr(c._bg, 'pos', c.pos), setattr(c._accent, 'pos', (c.x, c.y))))
            card.bind(size=lambda c, *_: (setattr(c._bg, 'size', c.size), setattr(c._accent, 'size', (4, c.height))))

            top = BoxLayout(size_hint_y=None, height=26)
            top.add_widget(Label(
                text=d.get('customer', '?'),
                font_size="15sp", halign="left", text_size=(None, None),
                color=WHITE, bold=True, size_hint_x=0.6,
            ))
            top.add_widget(Label(
                text=status, font_size="12sp", color=status_color,
                size_hint_x=0.2,
            ))
            if balance > 0:
                settle_btn = Button(
                    text="Settle", font_size="11sp", size_hint_x=0.2,
                    background_color=SUCCESS, color=WHITE, background_normal="",
                )
                debt_ref = d
                settle_btn.bind(on_release=lambda x, dd=debt_ref: self.settle_debt(dd))
                top.add_widget(settle_btn)
            else:
                top.add_widget(Label(size_hint_x=0.2))
            card.add_widget(top)

            items_str = ", ".join(f"{n}x{q}" for n, q in d.get("items", {}).items())
            card.add_widget(Label(
                text=f"KES {total:,.0f} total  |  KES {balance:,.0f} balance",
                font_size="12sp", halign="left", size_hint_y=None, height=22,
                text_size=(None, None), color=MUTED,
            ))
            card.add_widget(Label(
                text=f"{d.get('date', '')}  |  {items_str}",
                font_size="10sp", halign="left", size_hint_y=None, height=18,
                text_size=(None, None), color=DIVIDER,
            ))

            debt_box.add_widget(card)

        if not all_debts:
            debt_box.add_widget(Label(
                text="No debts found",
                size_hint_y=None, height=80,
                color=MUTED, font_size="14sp",
            ))

        scroll.add_widget(debt_box)
        main.add_widget(scroll)

        bottom = BoxLayout(size_hint_y=None, height=56, padding=8)
        back_btn = Button(text="Back to POS", font_size="14sp",
                          background_color=SURFACE, color=MUTED, background_normal="")
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'pos'))
        bottom.add_widget(back_btn)
        main.add_widget(bottom)

        self.add_widget(main)

    def settle_debt(self, debt):
        from backend.debts import calc_debt_outstanding
        from backend.database import haptic_click
        haptic_click()
        balance = calc_debt_outstanding(debt)

        content = BoxLayout(orientation="vertical", spacing=12, padding=20)
        content.add_widget(Label(
            text=f"Settle debt for\n{debt.get('customer', '?')}",
            font_size="18sp", halign="center", color=WHITE, bold=True,
        ))
        content.add_widget(Label(
            text=f"Outstanding: KES {balance:,.0f}",
            font_size="16sp", halign="center", color=DANGER,
        ))

        method_box = BoxLayout(spacing=8, size_hint_y=None, height=48)
        self._settle_method = "cash"
        self._settle_method_btns = {}
        for m, lbl in [("cash", "\U0001f4b5 Cash"), ("mpesa", "\U0001f4f1 M-Pesa")]:
            btn = Button(
                text=lbl, font_size="13sp",
                background_color=SUCCESS if m == "cash" else SURFACE,
                color=WHITE, background_normal="",
            )
            btn.m = m
            btn.bind(on_release=lambda x: self._pick_method(x.m))
            self._settle_method_btns[m] = btn
            method_box.add_widget(btn)
        content.add_widget(method_box)

        self._settle_amount = TextInput(
            text=str(int(balance)), hint_text="Amount",
            input_filter="float", size_hint_y=None, height=48,
            font_size="17sp", multiline=False,
            background_color=INPUT_BG, background_normal="",
            foreground_color=WHITE, cursor_color=ACCENT,
            hint_text_color=HINT, padding=[14, 10],
        )
        content.add_widget(self._settle_amount)

        btn_box = BoxLayout(spacing=10, size_hint_y=None, height=50)
        cancel_btn = Button(text="Cancel", background_color=SURFACE,
                            color=MUTED, background_normal="")
        confirm_btn = Button(text="CONFIRM SETTLEMENT", background_color=SUCCESS,
                             color=WHITE, bold=True, background_normal="")
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(confirm_btn)
        content.add_widget(btn_box)

        popup = Popup(title="Settle Debt", content=content, size_hint=(0.9, 0.65),
                      auto_dismiss=False, background_color=CARD,
                      title_color=WHITE, separator_color=DIVIDER)
        cancel_btn.bind(on_release=popup.dismiss)
        confirm_btn.bind(on_release=lambda x: self._confirm_settle(popup, debt))
        popup.open()

    def _pick_method(self, method):
        self._settle_method = method
        for m, btn in self._settle_method_btns.items():
            btn.background_color = SUCCESS if m == method else SURFACE

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
