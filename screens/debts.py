from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput


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
        main = BoxLayout(orientation="vertical", padding=8, spacing=8)

        header = BoxLayout(
            size_hint_y=None, height=48,
            padding=[10, 0, 10, 0],
        )
        with header.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0.1, 0.13, 0.24, 1)
            header._bg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda s, _: s._bg.__setattr__("pos", s.pos))
        header.bind(size=lambda s, _: s._bg.__setattr__("size", s.size))
        header.add_widget(Label(
            text="DEBT MANAGEMENT", font_size="16sp", color=(1, 1, 1, 1),
        ))
        main.add_widget(header)

        from backend.debts import get_all_debts, calc_debt_outstanding
        all_debts = get_all_debts()
        outstanding = [d for d in all_debts if calc_debt_outstanding(d) > 0]
        total_out = sum(calc_debt_outstanding(d) for d in outstanding)

        summary = BoxLayout(size_hint_y=None, height=50, spacing=5, padding=5)
        for label, value, color in [
            ("Outstanding", str(len(outstanding)), (0.91, 0.3, 0.24, 1)),
            ("Total", f"KES {total_out:,.0f}", (0.91, 0.3, 0.24, 1)),
        ]:
            card = BoxLayout(orientation="vertical", padding=5, size_hint_x=0.5)
            with card.canvas.before:
                from kivy.graphics import Color, Rectangle
                Color(*color)
                card._bg = Rectangle(pos=card.pos, size=card.size)
            card.bind(pos=lambda s, _: s._bg.__setattr__("pos", s.pos))
            card.bind(size=lambda s, _: s._bg.__setattr__("size", s.size))
            card.add_widget(Label(text=label, font_size="11sp", color=(1, 1, 1, 0.8)))
            card.add_widget(Label(text=value, font_size="16sp", color=(1, 1, 1, 1)))
            summary.add_widget(card)
        main.add_widget(summary)

        scroll = ScrollView()
        debt_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=4, padding=4)
        debt_box.bind(minimum_height=debt_box.setter("height"))

        for d in all_debts:
            total = d.get("total", 0)
            paid = sum(s["amount"] for s in d.get("settlements", []))
            balance = total - paid
            status = "SETTLED" if balance <= 0 else "OUTSTANDING"
            items_str = ", ".join(f"{n}x{q}" for n, q in d.get("items", {}).items())

            row = BoxLayout(orientation="vertical", size_hint_y=None, height=80,
                            padding=[8, 6], spacing=2)
            with row.canvas.before:
                from kivy.graphics import Color, Rectangle
                Color(0.1, 0.15, 0.26, 1)
                row._bg = Rectangle(pos=row.pos, size=row.size)
            row.bind(pos=lambda s, _: s._bg.__setattr__("pos", s.pos))
            row.bind(size=lambda s, _: s._bg.__setattr__("size", s.size))

            top = BoxLayout(size_hint_y=None, height=22)
            top.add_widget(Label(
                text=f"{d.get('customer', '?')}  |  {status}",
                font_size="14sp", halign="left", text_size=(None, None),
                color=(1, 1, 1, 1),
            ))
            row.add_widget(top)

            row.add_widget(Label(
                text=f"Total: KES {total:,.0f}  |  Balance: KES {balance:,.0f}",
                font_size="12sp", halign="left", size_hint_y=None, height=18,
                text_size=(None, None), color=(0.7, 0.7, 0.7, 1),
            ))
            row.add_widget(Label(
                text=f"{d.get('date', '')} | {items_str}",
                font_size="11sp", halign="left", size_hint_y=None, height=18,
                text_size=(None, None), color=(0.5, 0.5, 0.5, 1),
            ))

            if balance > 0:
                settle_btn = Button(
                    text="Settle", font_size="11sp", size_hint_x=0.25,
                    background_color=(0.15, 0.68, 0.38, 1), color=(1, 1, 1, 1),
                )
                settle_btn.bind(on_release=lambda x, dd=d: self.settle_debt(dd))
                row.add_widget(settle_btn)
            else:
                row.add_widget(Label(size_hint_x=0.25))

            debt_box.add_widget(row)

        if not all_debts:
            debt_box.add_widget(Label(
                text="No debts found", size_hint_y=None, height=40, color=(0.5, 0.5, 0.5, 1)))

        scroll.add_widget(debt_box)
        main.add_widget(scroll)

        bottom = BoxLayout(size_hint_y=None, height=44, padding=5)
        back_btn = Button(text="Back", font_size="13sp",
                          background_color=(0.59, 0.65, 0.65, 1), color=(1, 1, 1, 1))
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'pos'))
        bottom.add_widget(back_btn)
        main.add_widget(bottom)

        self.add_widget(main)

    def settle_debt(self, debt):
        from backend.database import session
        from backend.debts import calc_debt_outstanding
        balance = calc_debt_outstanding(debt)

        content = BoxLayout(orientation="vertical", spacing=10, padding=15)
        content.add_widget(Label(
            text=f"Settle: {debt.get('customer', '?')}\nOutstanding: KES {balance:,.0f}",
            font_size="16sp", halign="center",
        ))

        method_box = BoxLayout(spacing=4, size_hint_y=None, height=36)
        self._settle_method = "cash"
        self._settle_method_btns = {}
        for m, lbl in [("cash", "Cash"), ("mpesa", "M-Pesa")]:
            btn = Button(
                text=lbl, font_size="12sp",
                background_color=(0.15, 0.68, 0.38, 1) if m == "cash" else (0.5, 0.5, 0.5, 1),
                color=(1, 1, 1, 1),
            )
            btn.m = m
            btn.bind(on_release=lambda x: self._pick_method(x.m))
            self._settle_method_btns[m] = btn
            method_box.add_widget(btn)
        content.add_widget(method_box)

        self._settle_amount = TextInput(
            text=str(int(balance)), hint_text="Amount",
            input_filter="float", size_hint_y=None, height=40,
            font_size="16sp", multiline=False,
        )
        content.add_widget(self._settle_amount)

        btn_box = BoxLayout(spacing=8, size_hint_y=None, height=44)
        cancel_btn = Button(text="Cancel", background_color=(0.5, 0.5, 0.5, 1), color=(1, 1, 1, 1))
        confirm_btn = Button(text="CONFIRM", background_color=(0.15, 0.68, 0.38, 1), color=(1, 1, 1, 1))
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(confirm_btn)
        content.add_widget(btn_box)

        popup = Popup(title="Settle Debt", content=content, size_hint=(0.9, 0.6), auto_dismiss=False)
        cancel_btn.bind(on_release=popup.dismiss)
        confirm_btn.bind(on_release=lambda x: self._confirm_settle(popup, debt))
        popup.open()

    def _pick_method(self, method):
        self._settle_method = method
        for m, btn in self._settle_method_btns.items():
            btn.background_color = (0.15, 0.68, 0.38, 1) if m == method else (0.5, 0.5, 0.5, 1)

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
