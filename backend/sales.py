from .database import load_json, save_json, today_key
from datetime import datetime

def load_sales(date_key):
    return load_json(f"sales_{date_key}",
                     {"items": {}, "transactions": [], "total_revenue": 0,
                      "price_overrides": {}, "debts": []})

def save_sales(date_key, data):
    save_json(f"sales_{date_key}", data)

def record_sale(date_key, txn):
    sales = load_sales(date_key)
    sales["transactions"].append(txn)
    for name, qty in txn.get("items", {}).items():
        sales["items"][name] = sales["items"].get(name, 0) + qty
    sales["total_revenue"] = sales.get("total_revenue", 0) + txn.get("total", 0)
    if txn.get("payment_method") == "credit":
        debt = {
            "id": f"{date_key}_{txn['time'].replace(':', '')}",
            "customer": txn.get("customer", "Unknown"),
            "items": txn.get("items", {}),
            "total": txn.get("total", 0),
            "date": date_key,
            "time": txn.get("time", ""),
            "status": "outstanding",
            "settlements": [],
            "cashier": txn.get("cashier", ""),
        }
        sales.setdefault("debts", []).append(debt)
    save_sales(date_key, sales)

def undo_last_sale(date_key):
    sales = load_sales(date_key)
    txns = sales.get("transactions", [])
    if not txns:
        return None
    last = txns.pop()
    for name, qty in last.get("items", {}).items():
        current = sales.get("items", {}).get(name, 0)
        sales["items"][name] = max(0, current - qty)
    sales["total_revenue"] = max(0, sales.get("total_revenue", 0) - last.get("total", 0))
    if last.get("payment_method") == "credit":
        debt_id = f"{date_key}_{last['time'].replace(':', '')}"
        sales["debts"] = [d for d in sales.get("debts", []) if d.get("id") != debt_id]
    save_sales(date_key, sales)
    return last

def get_payment_summary(sales_data):
    cash = mpesa = till = credit = 0
    for t in sales_data.get("transactions", []):
        m = t.get("payment_method", "cash")
        if m == "cash":
            cash += t.get("cash_received", t.get("total", 0))
        elif m == "mpesa":
            mpesa += t.get("mpesa_amount", t.get("total", 0))
        elif m == "till":
            till += t.get("till_amount", t.get("total", 0))
        elif m == "credit":
            credit += t.get("total", 0)
        elif m == "split":
            cash += t.get("split_cash", 0)
            mpesa += t.get("split_mpesa", 0)
            till += t.get("split_till", 0)
            if t.get("split_credit", 0) > 0:
                credit += t["split_credit"]
    return {"cash": cash, "mpesa": mpesa, "till": till, "credit": credit}
