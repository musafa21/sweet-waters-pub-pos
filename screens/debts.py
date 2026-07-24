from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, ThreeLineListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog


class DebtScreen(MDScreen):
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
            size_hint_y=None,
            height=50,
            md_bg_color=[0.17, 0.24, 0.31, 1],
            padding=[10, 0, 10, 0],
        )
        header.add_widget(MDLabel(
            text="DEBT MANAGEMENT",
            font_style="H6",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
        ))
        main.add_widget(header)

        from backend.debts import get_all_debts, calc_debt_outstanding
        all_debts = get_all_debts()
        outstanding = [d for d in all_debts if calc_debt_outstanding(d) > 0]
        total_out = sum(calc_debt_outstanding(d) for d in outstanding)

        summary = MDBoxLayout(size_hint_y=None, height=60, spacing=5, padding=5)
        for label, value, color in [
            ("Outstanding", str(len(outstanding)), [0.91, 0.3, 0.24, 1]),
            ("Total", f"KES {total_out:,.0f}", [0.91, 0.3, 0.24, 1]),
        ]:
            card = MDBoxLayout(orientation="vertical", md_bg_color=color, padding=5, size_hint_x=0.5)
            card.add_widget(MDLabel(
                text=label,
                font_style="Caption",
                halign="center",
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.8],
            ))
            card.add_widget(MDLabel(
                text=value,
                font_style="H6",
                halign="center",
                theme_text_color="Custom",
                text_color=[1, 1, 1, 1],
            ))
            summary.add_widget(card)
        main.add_widget(summary)

        self.debt_list = MDList()
        for d in all_debts:
            total = d.get("total", 0)
            paid = sum(s["amount"] for s in d.get("settlements", []))
            balance = total - paid
            status = "SETTLED" if balance <= 0 else "OUTSTANDING"
            item = ThreeLineListItem(
                text=f"{d.get('customer', '?')}  |  {status}",
                secondary_text=f"Total: KES {total:,.0f}  |  Balance: KES {balance:,.0f}",
                tertiary_text=f"Date: {d.get('date', '')}  |  Cashier: {d.get('cashier', '')}",
                on_release=lambda x, dd=d: self.settle_debt(dd),
            )
            self.debt_list.add_widget(item)

        if not all_debts:
            self.debt_list.add_widget(ThreeLineListItem(
                text="No debts found",
                secondary_text="",
                tertiary_text="",
            ))

        scroll = MDScrollView()
        scroll.add_widget(self.debt_list)
        main.add_widget(scroll)

        bottom = MDBoxLayout(size_hint_y=None, height=50, padding=5)
        bottom.add_widget(MDRaisedButton(
            text="Back",
            on_release=lambda x: setattr(self.manager, 'current', 'pos'),
            md_bg_color=[0.59, 0.65, 0.65, 1],
        ))
        main.add_widget(bottom)

        self.add_widget(main)

    def settle_debt(self, debt):
        from backend.debts import calc_debt_outstanding
        balance = calc_debt_outstanding(debt)
        if balance <= 0:
            dialog = MDDialog(
                title="Settled",
                text="Already fully settled.",
                buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())],
            )
            dialog.open()
            return

        content = MDBoxLayout(orientation="vertical", spacing=10, padding=20, size_hint_y=None, height=250)
        content.add_widget(MDLabel(
            text=f"Settle: {debt.get('customer', '?')}",
            font_style="H6",
            halign="center",
        ))
        content.add_widget(MDLabel(
            text=f"Outstanding: KES {balance:,.0f}",
            halign="center",
            theme_text_color="Error",
        ))

        method_box = MDBoxLayout(spacing=5, size_hint_y=None, height=40)
        self._settle_method = "cash"
        for m, lbl in [("cash", "Cash"), ("mpesa", "M-Pesa"), ("till", "Till")]:
            btn = MDFlatButton(
                text=lbl,
                on_release=lambda x, mm=m: self._set_method(mm, method_box),
                md_bg_color=[0.8, 0.8, 0.8, 1] if m != "cash" else [0.15, 0.68, 0.38, 1],
                theme_text_color="Custom",
                text_color=[1, 1, 1, 1] if m == "cash" else [0, 0, 0, 1],
            )
            method_box.add_widget(btn)
        content.add_widget(method_box)

        self._settle_amount = MDTextField(
            text=str(balance),
            hint_text="Amount",
            input_filter="float",
            size_hint_y=None,
            height=50,
        )
        content.add_widget(self._settle_amount)

        def confirm_settle(dt):
            try:
                amt = float(self._settle_amount.text)
            except ValueError:
                return
            if amt <= 0 or amt > balance:
                return
            from backend.debts import settle_debt as do_settle
            do_settle(debt.get("id"), debt["_date_key"], amt, self._settle_method)
            dialog.dismiss()
            self.build_ui()

        dialog = MDDialog(
            title="Settle Debt",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(
                    text="CONFIRM",
                    md_bg_color=[0.15, 0.68, 0.38, 1],
                    on_release=confirm_settle,
                ),
            ],
        )
        dialog.open()

    def _set_method(self, method, box):
        self._settle_method = method
        for child in box.children:
            if hasattr(child, 'text'):
                if child.text.lower() == method:
                    child.md_bg_color = [0.15, 0.68, 0.38, 1]
                    child.text_color = [1, 1, 1, 1]
                else:
                    child.md_bg_color = [0.8, 0.8, 0.8, 1]
                    child.text_color = [0, 0, 0, 1]
