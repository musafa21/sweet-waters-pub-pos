import csv
import os
from .database import today_key
from .stock import get_effective_price, get_stock_list
from .sales import load_sales, get_payment_summary
from .debts import calc_debt_outstanding

def export_csv(date_key, path):
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

def export_pdf(date_key, path):
    try:
        from fpdf import FPDF
    except ImportError:
        raise ImportError("Install fpdf2: pip install fpdf2")
    sales = load_sales(date_key)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "SWEET WATERS PUB", ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"Daily Report - {date_key}", ln=True, align="C")
    pdf.ln(5)
    ps = get_payment_summary(sales)
    total_rev = sales.get("total_revenue", 0)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"Total Revenue: KES {total_rev:,.2f}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Cash: KES {ps['cash']:,.2f}  |  M-Pesa: KES {ps['mpesa']:,.2f}  |  Till: KES {ps['till']:,.2f}  |  Credit: KES {ps['credit']:,.2f}", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Items Sold", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(60, 6, "Item", border=1)
    pdf.cell(25, 6, "Qty", border=1, align="C")
    pdf.cell(35, 6, "Revenue", border=1, align="R")
    pdf.ln()
    for name, qty in sorted(sales.get("items", {}).items()):
        price = get_effective_price(name, date_key)
        pdf.cell(60, 5, name[:30], border=1)
        pdf.cell(25, 5, str(qty), border=1, align="C")
        pdf.cell(35, 5, f"{qty * price:,.2f}", border=1, align="R")
        pdf.ln()
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Transactions", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(20, 6, "Time", border=1)
    pdf.cell(25, 6, "Cashier", border=1)
    pdf.cell(25, 6, "Method", border=1)
    pdf.cell(60, 6, "Items", border=1)
    pdf.cell(25, 6, "Total", border=1, align="R")
    pdf.ln()
    for t in sales.get("transactions", []):
        items_str = "; ".join(f"{n}x{q}" for n, q in t.get("items", {}).items())[:35]
        pdf.cell(20, 5, t.get("time", ""), border=1)
        pdf.cell(25, 5, t.get("cashier", ""), border=1)
        pdf.cell(25, 5, t.get("payment_method", ""), border=1)
        pdf.cell(60, 5, items_str, border=1)
        pdf.cell(25, 5, f"{t.get('total', 0):,.2f}", border=1, align="R")
        pdf.ln()
    pdf.output(path)
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
