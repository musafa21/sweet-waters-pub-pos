import os
import glob as glob_mod
from .database import load_json, save_json, DATA_DIR, today_key
from .sales import load_sales
from datetime import datetime

def calc_debt_outstanding(debt):
    settled = sum(s["amount"] for s in debt.get("settlements", []))
    return debt.get("total", 0) - settled

def get_all_debts():
    all_d = []
    for path in glob_mod.glob(os.path.join(DATA_DIR, "sales_*.json")):
        fname = os.path.basename(path)
        dk = fname.replace("sales_", "").replace(".json", "")
        if len(dk) != 10:
            continue
        sales = load_sales(dk)
        for d in sales.get("debts", []):
            d["_date_key"] = dk
            all_d.append(d)
    all_d.sort(key=lambda d: (d.get("date", ""), d.get("time", "")), reverse=True)
    return all_d

def settle_debt(debt_id, date_key, amount, method):
    sales = load_sales(date_key)
    for dd in sales.get("debts", []):
        if dd.get("id") == debt_id:
            dd.setdefault("settlements", []).append({
                "date": today_key(),
                "time": datetime.now().strftime("%H:%M:%S"),
                "amount": amount,
                "method": method,
            })
            if calc_debt_outstanding(dd) <= 0:
                dd["status"] = "settled"
            break
    save_sales(date_key, sales)

def available_dates():
    dates = []
    for path in glob_mod.glob(os.path.join(DATA_DIR, "sales_*.json")):
        fname = os.path.basename(path)
        dk = fname.replace("sales_", "").replace(".json", "")
        if len(dk) == 10:
            dates.append(dk)
    from .stock import load_stock_movements
    mv = load_stock_movements()
    for dk in list(mv.get("opening", {}).keys()) + list(mv.get("purchases", {}).keys()):
        if dk not in dates and len(dk) == 10:
            dates.append(dk)
    dates.sort(reverse=True)
    return dates
