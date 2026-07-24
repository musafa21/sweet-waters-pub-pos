from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, ThreeLineListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard


class ReportScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.date_key = ""

    def set_app(self, app):
        self.app = app

    def on_enter(self):
        from backend.database import today_key
        if not self.date_key:
            self.date_key = today_key()
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
            text="DAILY REPORT",
            font_style="H6",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
        ))
        self.date_field = MDTextField(
            text=self.date_key,
            size_hint_x=0.4,
            size_hint_y=None,
            height=40,
            halign="center",
        )
        header.add_widget(self.date_field)
        header.add_widget(MDFlatButton(
            text="Go",
            on_release=self.go_to_date,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
        ))
        main.add_widget(header)

        from backend.sales import load_sales, get_payment_summary
        from backend.stock import calc_remaining_stock, get_stock_list, get_effective_price

        sales = load_sales(self.date_key)
        ps = get_payment_summary(sales)
        total_rev = sales.get("total_revenue", 0)

        stats = MDBoxLayout(
            size_hint_y=None,
            height=70,
            spacing=5,
            padding=5,
        )
        for label, value, color in [
            ("Revenue", f"KES {total_rev:,.0f}", [0.17, 0.24, 0.31, 1]),
            ("Cash", f"KES {ps['cash']:,.0f}", [0.15, 0.68, 0.38, 1]),
            ("M-Pesa", f"KES {ps['mpesa']:,.0f}", [0.1, 0.54, 0.29, 1]),
            ("Till", f"KES {ps['till']:,.0f}", [0.56, 0.27, 0.68, 1]),
        ]:
            card = MDCard(
                orientation="vertical",
                padding=8,
                md_bg_color=color,
                size_hint_x=0.25,
            )
            card.add_widget(MDLabel(
                text=label,
                font_style="Caption",
                halign="center",
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.8],
                size_hint_y=None,
                height=20,
            ))
            card.add_widget(MDLabel(
                text=value,
                font_style="Body1",
                halign="center",
                theme_text_color="Custom",
                text_color=[1, 1, 1, 1],
                size_hint_y=None,
                height=30,
            ))
            stats.add_widget(card)
        main.add_widget(stats)

        tabs = MDBoxLayout(
            size_hint_y=None,
            height=40,
            spacing=5,
        )
        self._tab_buttons = []
        for tab_name in ["Sales", "Transactions", "Stock"]:
            btn = MDFlatButton(
                text=tab_name,
                on_release=lambda x, t=tab_name: self.show_tab(t),
                theme_text_color="Custom",
                text_color=[0.17, 0.24, 0.31, 1],
            )
            tabs.add_widget(btn)
            self._tab_buttons.append(btn)
        main.add_widget(tabs)

        self._tab_content = MDBoxLayout()
        main.add_widget(self._tab_content)

        bottom = MDBoxLayout(size_hint_y=None, height=50, spacing=5, padding=5)
        bottom.add_widget(MDRaisedButton(
            text="Back",
            on_release=lambda x: setattr(self.manager, 'current', 'pos'),
            md_bg_color=[0.59, 0.65, 0.65, 1],
        ))
        bottom.add_widget(MDRaisedButton(
            text="Undo Last Sale",
            on_release=self.undo_sale,
            md_bg_color=[0.91, 0.3, 0.24, 1],
        ))
        main.add_widget(bottom)

        self.add_widget(main)
        self.show_tab("Sales")

    def show_tab(self, tab_name):
        self._tab_content.clear_widgets()
        from backend.sales import load_sales
        from backend.stock import get_effective_price, calc_remaining_stock, get_stock_list

        sales = load_sales(self.date_key)

        if tab_name == "Sales":
            items_list = MDList()
            for name, qty in sorted(sales.get("items", {}).items()):
                price = get_effective_price(name, self.date_key)
                rev = qty * price
                items_list.add_widget(ThreeLineListItem(
                    text=name,
                    secondary_text=f"Qty: {qty}",
                    tertiary_text=f"Revenue: KES {rev:,.0f}",
                ))
            if not sales.get("items"):
                items_list.add_widget(ThreeLineListItem(
                    text="No sales data",
                    secondary_text="",
                    tertiary_text="",
                ))
            scroll = MDScrollView()
            scroll.add_widget(items_list)
            self._tab_content.add_widget(scroll)

        elif tab_name == "Transactions":
            items_list = MDList()
            for t in reversed(sales.get("transactions", [])):
                method = t.get("payment_method", "cash").upper()
                items_str = ", ".join(f"{n}x{q}" for n, q in t.get("items", {}).items())
                items_list.add_widget(ThreeLineListItem(
                    text=f"{t.get('time', '')}  |  {t.get('cashier', '')}  |  {method}",
                    secondary_text=items_str,
                    tertiary_text=f"KES {t.get('total', 0):,.0f}",
                ))
            if not sales.get("transactions"):
                items_list.add_widget(ThreeLineListItem(
                    text="No transactions",
                    secondary_text="",
                    tertiary_text="",
                ))
            scroll = MDScrollView()
            scroll.add_widget(items_list)
            self._tab_content.add_widget(scroll)

        elif tab_name == "Stock":
            remaining = calc_remaining_stock(self.date_key)
            items_list = MDList()
            for name in sorted(get_stock_list().keys()):
                rem = remaining.get(name, 0)
                color_tag = ""
                if rem <= 0:
                    color_tag = " [color=#c0392b]OUT OF STOCK[/color]"
                elif rem <= 3:
                    color_tag = " [color=#e67e22]LOW[/color]"
                items_list.add_widget(ThreeLineListItem(
                    text=f"{name}{color_tag}",
                    secondary_text=f"Remaining: {rem}",
                    tertiary_text="",
                ))
            scroll = MDScrollView()
            scroll.add_widget(items_list)
            self._tab_content.add_widget(scroll)

    def go_to_date(self, *args):
        dk = self.date_field.text.strip()
        from datetime import datetime
        try:
            datetime.strptime(dk, "%Y-%m-%d")
        except ValueError:
            from kivymd.uix.dialog import MDDialog
            from kivymd.uix.button import MDFlatButton
            dialog = MDDialog(
                title="Invalid",
                text="Use YYYY-MM-DD format",
                buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())],
            )
            dialog.open()
            return
        self.date_key = dk
        self.build_ui()

    def undo_sale(self, *args):
        from backend.database import today_key
        from backend.sales import undo_last_sale, load_sales
        dk = today_key()
        sales = load_sales(dk)
        txns = sales.get("transactions", [])
        if not txns:
            from kivymd.uix.dialog import MDDialog
            from kivymd.uix.button import MDFlatButton
            dialog = MDDialog(
                title="Nothing",
                text="No sales to undo today.",
                buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())],
            )
            dialog.open()
            return
        last = txns[-1]
        items_str = ", ".join(f"{n}x{q}" for n, q in last.get("items", {}).items())

        def confirm_undo(dt):
            undone = undo_last_sale(dk)
            if undone:
                from kivymd.uix.dialog import MDDialog
                from kivymd.uix.button import MDFlatButton
                d = MDDialog(
                    title="Undone",
                    text=f"Sale of KES {undone.get('total', 0):,.2f} reversed.",
                    buttons=[MDFlatButton(text="OK", on_release=lambda x: d.dismiss())],
                )
                d.open()

        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton
        dialog = MDDialog(
            title="Undo Sale?",
            text=f"Time: {last.get('time', '')}\nCashier: {last.get('cashier', '')}\nItems: {items_str}\nTotal: KES {last.get('total', 0):,.0f}",
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(
                    text="Undo",
                    md_bg_color=[0.91, 0.3, 0.24, 1],
                    on_release=lambda x: (dialog.dismiss(), confirm_undo(None)),
                ),
            ],
        )
        dialog.open()
