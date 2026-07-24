import re
from .database import load_json, save_json, today_key

_UNSAFE_RE = re.compile(r'[<>{}\[\]]')


def _sanitize_name(name):
    return _UNSAFE_RE.sub("", name).strip()


def load_stock():
    data = load_json("stock")
    if not data:
        data = init_stock()
    return data

def save_stock(data):
    save_json("stock", data)

def get_stock_list():
    return load_stock().get("items", {})

def get_stock_item(name):
    return get_stock_list().get(name, None)

def set_stock_item(name, price, category=None):
    name = _sanitize_name(name)
    if not name:
        return
    if category:
        category = _sanitize_name(category)
    data = load_stock()
    items = data.setdefault("items", {})
    if name in items:
        items[name]["price"] = price
        if category:
            items[name]["category"] = category
    else:
        items[name] = {"price": price, "category": category or "Uncategorized"}
    save_stock(data)

def delete_stock_item(name):
    data = load_stock()
    items = data.get("items", {})
    if name in items:
        del items[name]
        save_stock(data)
        return True
    return False

def get_categories():
    items = get_stock_list()
    cats = {}
    for name, info in items.items():
        cat = info.get("category", "Uncategorized")
        cats.setdefault(cat, []).append(name)
    return cats

def get_effective_price(item_name, date_key=None):
    if date_key is None:
        date_key = today_key()
    from .sales import load_sales
    sales = load_sales(date_key)
    overrides = sales.get("price_overrides", {})
    if item_name in overrides:
        return overrides[item_name]
    item = get_stock_item(item_name)
    return item["price"] if item else 0

def load_stock_movements():
    return load_json("stock_movements", {"opening": {}, "purchases": {}, "closing": {}})

def save_stock_movements(data):
    save_json("stock_movements", data)

def calc_remaining_stock(date_key):
    from .sales import load_sales
    movements = load_stock_movements()
    sales = load_sales(date_key)
    items_sold = sales.get("items", {})
    opening = movements.get("opening", {}).get(date_key, {})
    purchases = movements.get("purchases", {}).get(date_key, [])
    purch_qty = {}
    for p in purchases:
        name = p["item"]
        purch_qty[name] = purch_qty.get(name, 0) + p["qty"]
    remaining = {}
    for name in get_stock_list():
        op = opening.get(name, 0)
        pu = purch_qty.get(name, 0)
        so = items_sold.get(name, 0)
        remaining[name] = op + pu - so
    return remaining

def calc_today_stock():
    return calc_remaining_stock(today_key())

def init_stock():
    DEFAULT_STOCK = {
        "Tusker": {"price": 250.00, "category": "Beers & Lagers"},
        "Tusker Lite": {"price": 280.00, "category": "Beers & Lagers"},
        "Tusker Cider": {"price": 280.00, "category": "Beers & Lagers"},
        "Balozi": {"price": 250.00, "category": "Beers & Lagers"},
        "Pilsner": {"price": 250.00, "category": "Beers & Lagers"},
        "W/Cap lager": {"price": 280.00, "category": "Beers & Lagers"},
        "Guinness Kubwa": {"price": 280.00, "category": "Beers & Lagers"},
        "Heineken": {"price": 300.00, "category": "Beers & Lagers"},
        "Faxe": {"price": 300.00, "category": "Beers & Lagers"},
        "Savannah": {"price": 300.00, "category": "Beers & Lagers"},
        "Desperados": {"price": 300.00, "category": "Beers & Lagers"},
        "Predator": {"price": 80.00, "category": "Beers & Lagers"},
        "Azam": {"price": 60.00, "category": "Beers & Lagers"},
        "Chrome 250Ml": {"price": 300.00, "category": "Rum & Spirits"},
        "Chrome 750ml": {"price": 900.00, "category": "Rum & Spirits"},
        "Kibao 250ml": {"price": 300.00, "category": "Rum & Spirits"},
        "Kibao 750ml": {"price": 900.00, "category": "Rum & Spirits"},
        "Triple Ace 250Ml": {"price": 300.00, "category": "Rum & Spirits"},
        "Tipple Ace 750Ml": {"price": 900.00, "category": "Rum & Spirits"},
        "Kane Extra 250Ml": {"price": 300.00, "category": "Rum & Spirits"},
        "Kane Extra 750Ml": {"price": 900.00, "category": "Rum & Spirits"},
        "County 250Mls": {"price": 300.00, "category": "Rum & Spirits"},
        "County 750Ml": {"price": 900.00, "category": "Rum & Spirits"},
        "Kenya Cane 250Ml": {"price": 350.00, "category": "Rum & Spirits"},
        "Kenya Cane 350Ml": {"price": 450.00, "category": "Rum & Spirits"},
        "Kenya Cane 750Ml": {"price": 950.00, "category": "Rum & Spirits"},
        "Hunters 250Ml": {"price": 350.00, "category": "Rum & Spirits"},
        "Hunters 350Ml": {"price": 500.00, "category": "Rum & Spirits"},
        "Hunters 750Ml": {"price": 1200.00, "category": "Rum & Spirits"},
        "Captain Morgan 250Ml": {"price": 400.00, "category": "Rum & Spirits"},
        "Captain Morgan 750Ml": {"price": 1200.00, "category": "Rum & Spirits"},
        "Richot 250ML": {"price": 500.00, "category": "Rum & Spirits"},
        "Richot 350Ml": {"price": 750.00, "category": "Rum & Spirits"},
        "Richot 750Ml": {"price": 1500.00, "category": "Rum & Spirits"},
        "VBA 750Ml": {"price": 1000.00, "category": "Rum & Spirits"},
        "Best Whiskey 250Ml": {"price": 400.00, "category": "Whiskey"},
        "Best Whiskey 750Ml": {"price": 1200.00, "category": "Whiskey"},
        "VAT 69 350ML": {"price": 850.00, "category": "Whiskey"},
        "VAT 69 750ML": {"price": 1600.00, "category": "Whiskey"},
        "JW Black Label 250ML": {"price": 1100.00, "category": "Whiskey"},
        "JW Black Label 750ML": {"price": 3800.00, "category": "Whiskey"},
        "All Season 750ml": {"price": 750.00, "category": "Whiskey"},
        "Black N White": {"price": 750.00, "category": "Whiskey"},
        "Red Label": {"price": 800.00, "category": "Whiskey"},
        "Bond 7": {"price": 750.00, "category": "Whiskey"},
        "General Meakins 250Ml": {"price": 300.00, "category": "Whiskey"},
        "Best Gin 250ml": {"price": 350.00, "category": "Gin"},
        "Best Gin 750ml": {"price": 950.00, "category": "Gin"},
        "Gilbeys Gin 250Ml": {"price": 500.00, "category": "Gin"},
        "Gilbeys Gin 350ML": {"price": 750.00, "category": "Gin"},
        "Gilbeys Gin 750Ml": {"price": 1500.00, "category": "Gin"},
        "Gordon Gin 750Ml": {"price": 2300.00, "category": "Gin"},
        "Napoleon 250ML": {"price": 300.00, "category": "Gin"},
        "Viceroy 250Ml": {"price": 500.00, "category": "Vodka"},
        "Viceroy 350Ml": {"price": 750.00, "category": "Vodka"},
        "Smirnoff 350Ml": {"price": 750.00, "category": "Vodka"},
        "Smirnoff 750Ml": {"price": 1500.00, "category": "Vodka"},
        "Best Vodka 250Ml": {"price": 400.00, "category": "Vodka"},
        "Best Vodka 750Ml": {"price": 1200.00, "category": "Vodka"},
        "4th Street": {"price": 1200.00, "category": "Wines"},
        "Gato Negro": {"price": 1200.00, "category": "Wines"},
        "Drostdy Hoff": {"price": 1200.00, "category": "Wines"},
        "Caprice": {"price": 900.00, "category": "Wines"},
        "Reserve 7": {"price": 900.00, "category": "Wines"},
        "Safari Water 1000Ml": {"price": 70.00, "category": "Water & Soft Drinks"},
        "Safari Water 500Ml": {"price": 40.00, "category": "Water & Soft Drinks"},
        "Lemonade": {"price": 60.00, "category": "Water & Soft Drinks"},
        "Soda 500Ml": {"price": 100.00, "category": "Water & Soft Drinks"},
        "Soda 250Ml": {"price": 50.00, "category": "Water & Soft Drinks"},
        "Delmonte": {"price": 300.00, "category": "Water & Soft Drinks"},
        "Guarana Can": {"price": 250.00, "category": "Water & Soft Drinks"},
        "Sportsman": {"price": 15.00, "category": "Water & Soft Drinks"},
        "Safari Kings": {"price": 10.00, "category": "Water & Soft Drinks"},
    }
    data = {"items": DEFAULT_STOCK}
    save_stock(data)
    return data
