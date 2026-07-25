import csv
import os
from .database import today_key
from .stock import get_effective_price, get_stock_list
from .sales import load_sales, get_payment_summary
from .debts import calc_debt_outstanding

ALLOWED_EXPORT_DIR = None


def _validate_export_path(path):
    abs_path = os.path.abspath(path)
    export_dir = ALLOWED_EXPORT_DIR or os.path.abspath(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"))
    if not abs_path.startswith(export_dir):
        raise ValueError("Export path outside allowed directory")
    return abs_path


def export_csv(date_key, path):
    path = _validate_export_path(path)
    sales = load_sales(date_key)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["SWEET WATERS PUB - DAILY REPORT", date_key])
        w.writerow([])
        w.writerow(["ITEMS SOLD"])
        w.writerow(["Item", "Qty Sold", "Revenue (KES)"])
        total = 0
        for name, qty in sorted(sales.get("items", {}).items()):
            price = get_effective_price(name, date_key)
            rev = qty * price
            total += rev
            w.writerow([name, qty, f"{rev:.2f}"])
        w.writerow(["TOTAL", "", f"{total:.2f}"])
        w.writerow([])
        w.writerow(["PAYMENTS"])
        ps = get_payment_summary(sales)
        w.writerow(["Cash", f"{ps['cash']:.2f}"])
        w.writerow(["M-Pesa", f"{ps['mpesa']:.2f}"])
        w.writerow(["Till", f"{ps['till']:.2f}"])
        w.writerow(["Credit", f"{ps['credit']:.2f}"])
        w.writerow([])
        w.writerow(["TRANSACTIONS"])
        w.writerow(["Time", "Cashier", "Method", "Items", "Total"])
        for t in sales.get("transactions", []):
            items_str = "; ".join(f"{n}x{q}" for n, q in t.get("items", {}).items())
            w.writerow([t.get("time", ""), t.get("cashier", ""),
                        t.get("payment_method", ""), items_str, t.get("total", 0)])
    return path

def get_analytics(date_key):
    from .stock import get_stock_list, get_effective_price
    sales = load_sales(date_key)
    items = sales.get("items", {})
    best_sellers = sorted(items.items(), key=lambda x: x[1], reverse=True)
    unsold = [n for n in get_stock_list() if n not in items]
    slow_movers = [(n, q) for n, q in sorted(items.items(), key=lambda x: x[1]) if q <= 2]
    hourly = {}
    for t in sales.get("transactions", []):
        try:
            h = int(t["time"].split(":")[0])
        except (KeyError, ValueError, IndexError):
            continue
        hourly.setdefault(h, {"count": 0, "revenue": 0})
        hourly[h]["count"] += 1
        hourly[h]["revenue"] += t.get("total", 0)
    return {
        "best_sellers": [(n, q, q * get_effective_price(n, date_key)) for n, q in best_sellers],
        "unsold": unsold,
        "slow_movers": [(n, q, q * get_effective_price(n, date_key)) for n, q in slow_movers],
        "peak_hours": hourly,
    }
