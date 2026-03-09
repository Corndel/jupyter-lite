"""
Generate all data files for the ETL Pipelines module.
An e-commerce marketplace (Bazaar) with orders, seller CSVs, API JSON, and messy product data.
"""

import sqlite3
import csv
import json
import random
import os
from datetime import datetime, timedelta

random.seed(42)

BASE_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(BASE_DIR, "bazaar_orders.sqlite")
SELLER_DIR = os.path.join(BASE_DIR, "daily_seller_files")
API_PATH = os.path.join(BASE_DIR, "marketplace_api.json")
MESSY_PATH = os.path.join(BASE_DIR, "raw_products_messy.csv")

os.makedirs(SELLER_DIR, exist_ok=True)

# Remove existing database if present
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

# ============================================================
# 1. SQLite database: bazaar_orders.sqlite
# ============================================================

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.executescript("""
CREATE TABLE sellers (
    seller_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    category TEXT NOT NULL
);

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    country TEXT NOT NULL,
    signup_date TEXT NOT NULL
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id TEXT REFERENCES customers(customer_id),
    seller_id TEXT REFERENCES sellers(seller_id),
    order_date TEXT NOT NULL,
    total_amount REAL NOT NULL,
    currency TEXT NOT NULL,
    status TEXT NOT NULL
);
""")

# --- Sellers (20) ---
seller_categories = ["handmade", "vintage", "electronics", "clothing", "home_decor",
                      "jewellery", "art", "toys", "books", "food"]
seller_countries = ["UK", "US", "Germany", "France", "Japan", "Australia",
                    "Canada", "Netherlands", "Italy", "Spain"]
seller_names = [
    "Artisan Alcove", "Vintage Vault", "TechTrove", "Thread & Needle",
    "Homestead Goods", "Gemstone Gallery", "Canvas & Clay", "Toybox Treasures",
    "Bookworm Bazaar", "Gourmet Grove", "The Craft Corner", "Retro Revival",
    "Gadget Garden", "Silk & Stitch", "Hearthstone Home", "Silver & Stone",
    "Palette Studio", "Playtime Palace", "Page Turner Press", "Spice Route"
]

sellers_data = []
for i, name in enumerate(seller_names):
    sid = f"S{i+1:03d}"
    country = seller_countries[i % len(seller_countries)]
    category = seller_categories[i % len(seller_categories)]
    cur.execute("INSERT INTO sellers VALUES (?, ?, ?, ?)",
                (sid, name, country, category))
    sellers_data.append((sid, name, country, category))

# --- Customers (500) ---
first_names = [
    "Alice", "Bob", "Charlie", "Diana", "Edward", "Fiona", "George", "Hannah",
    "Isaac", "Julia", "Kevin", "Laura", "Michael", "Nadia", "Oliver", "Patricia",
    "Quentin", "Rachel", "Simon", "Tara", "Umar", "Victoria", "William", "Xena",
    "Yasmin", "Zachary", "Amelia", "Benjamin", "Catherine", "Daniel", "Eleanor",
    "Francis", "Grace", "Henry", "Imogen", "James", "Katherine", "Liam", "Megan",
    "Nathan", "Ophelia", "Peter", "Rosa", "Sebastian", "Thea", "Ursula", "Vincent",
    "Wendy", "Xavier", "Yvonne"
]

last_names = [
    "Smith", "Jones", "Williams", "Brown", "Taylor", "Davies", "Wilson",
    "Evans", "Thomas", "Johnson", "Roberts", "Walker", "Wright", "Robinson",
    "Thompson", "White", "Hughes", "Edwards", "Green", "Hall", "Lewis",
    "Harris", "Clark", "Patel", "Jackson", "Wood", "Turner", "Martin",
    "Cooper", "Hill", "Ward", "Morris", "Moore", "King", "Watson",
    "Harrison", "Morgan", "Allen", "James", "Scott", "Baker", "Price"
]

customer_countries = ["UK", "US", "Canada", "Australia", "Germany", "France",
                      "Japan", "Netherlands", "Ireland", "Sweden", "Italy",
                      "Spain", "Brazil", "India", "South Korea"]

customers_data = []
for i in range(500):
    cid = f"C{i+1:04d}"
    fname = random.choice(first_names)
    lname = random.choice(last_names)
    name = f"{fname} {lname}"
    email = f"{fname.lower()}.{lname.lower()}{random.randint(1, 99)}@{'gmail.com' if random.random() < 0.4 else 'outlook.com' if random.random() < 0.5 else 'yahoo.co.uk'}"
    country = random.choice(customer_countries)
    signup = datetime(2023, 6, 1) + timedelta(days=random.randint(0, 365))
    cur.execute("INSERT INTO customers VALUES (?, ?, ?, ?, ?)",
                (cid, name, email, country, signup.strftime("%Y-%m-%d")))
    customers_data.append(cid)

# --- Orders (~2000) ---
statuses = ["completed", "completed", "completed", "completed",
            "pending", "pending", "cancelled", "refunded"]
currencies = ["GBP", "EUR", "USD"]

# Orders span 2024-02-01 to 2024-03-31
order_start = datetime(2024, 2, 1)
order_end = datetime(2024, 3, 31)
order_span_days = (order_end - order_start).days

for oid in range(1, 2001):
    cid = random.choice(customers_data)
    sid = random.choice(sellers_data)[0]
    order_date = order_start + timedelta(
        days=random.randint(0, order_span_days),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )
    amount = round(random.uniform(5.0, 500.0), 2)
    currency = random.choice(currencies)
    status = random.choice(statuses)
    cur.execute("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)",
                (oid, cid, sid, order_date.strftime("%Y-%m-%d %H:%M:%S"),
                 amount, currency, status))

conn.commit()

# Verify
for table in ["sellers", "customers", "orders"]:
    count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  {table}: {count} rows")

conn.close()
print(f"Database written to {DB_PATH}")

# ============================================================
# 2. Daily seller CSV files (10 files)
# ============================================================

product_adjectives = [
    "Handmade", "Vintage", "Organic", "Artisan", "Premium", "Classic",
    "Rustic", "Modern", "Elegant", "Natural", "Bespoke", "Luxury"
]

product_nouns = [
    "Ceramic Mug", "Leather Wallet", "Wooden Bowl", "Cotton Scarf",
    "Glass Vase", "Silver Ring", "Linen Tablecloth", "Brass Candleholder",
    "Wool Blanket", "Silk Cushion", "Oak Cutting Board", "Copper Kettle",
    "Porcelain Plate", "Bamboo Tray", "Marble Coaster", "Iron Bookend",
    "Canvas Tote", "Clay Planter", "Stone Mortar", "Wicker Basket",
    "Enamel Pin", "Velvet Pouch", "Denim Apron", "Cork Notebook",
    "Tin Candle", "Paper Lampshade", "Resin Earrings", "Jute Rug"
]

categories = ["home", "accessories", "kitchen", "decor", "fashion",
              "jewellery", "stationery", "garden"]


def gen_products(seller_prefix, n_products, currency, date_format, date_val):
    """Generate a list of product dicts for a seller."""
    products = []
    for i in range(n_products):
        pid = f"{seller_prefix}-P{i+1:03d}"
        name = f"{random.choice(product_adjectives)} {random.choice(product_nouns)}"
        price = round(random.uniform(5.0, 150.0), 2)
        cat = random.choice(categories)
        stock = random.randint(0, 200)

        if date_format == "dd/mm/yyyy":
            date_str = date_val.strftime("%d/%m/%Y")
        elif date_format == "yyyy-mm-dd":
            date_str = date_val.strftime("%Y-%m-%d")
        elif date_format == "mm/dd/yyyy":
            date_str = date_val.strftime("%m/%d/%Y")

        products.append({
            "product_id": pid,
            "product_name": name,
            "price": price,
            "currency": currency,
            "category": cat,
            "stock_quantity": stock,
            "last_updated": date_str
        })
    return products


seller_configs = {
    "alpha": {"currency": "GBP", "date_format": "dd/mm/yyyy", "prefix": "ALP",
              "dates": [datetime(2024, 3, 1), datetime(2024, 3, 2),
                        datetime(2024, 3, 3), datetime(2024, 3, 4)]},
    "beta":  {"currency": "EUR", "date_format": "yyyy-mm-dd", "prefix": "BET",
              "dates": [datetime(2024, 3, 1), datetime(2024, 3, 2),
                        datetime(2024, 3, 3)]},
    "gamma": {"currency": "USD", "date_format": "mm/dd/yyyy", "prefix": "GAM",
              "dates": [datetime(2024, 3, 1), datetime(2024, 3, 2),
                        datetime(2024, 3, 3)]},
}

csv_count = 0
for seller_name, config in seller_configs.items():
    for date_val in config["dates"]:
        date_str = date_val.strftime("%Y%m%d")
        filename = f"seller_{seller_name}_{date_str}.csv"
        filepath = os.path.join(SELLER_DIR, filename)

        # 15-30 products per file, with overlap between days
        n_products = random.randint(15, 30)
        products = gen_products(
            config["prefix"], n_products, config["currency"],
            config["date_format"], date_val
        )

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "product_id", "product_name", "price", "currency",
                "category", "stock_quantity", "last_updated"
            ])
            writer.writeheader()
            writer.writerows(products)

        csv_count += 1

print(f"\nGenerated {csv_count} seller CSV files in {SELLER_DIR}")

# ============================================================
# 3. marketplace_api.json (simulated API response, ~200 products)
# ============================================================

api_products = []
for i in range(200):
    sid = f"S{random.randint(1, 20):03d}"
    name = f"{random.choice(product_adjectives)} {random.choice(product_nouns)}"
    price = round(random.uniform(8.0, 300.0), 2)
    currency = random.choice(currencies)
    cat = random.choice(categories)
    stock = random.randint(0, 500)
    updated = (datetime(2024, 3, 15) - timedelta(days=random.randint(0, 30))).isoformat() + "Z"

    api_products.append({
        "id": f"P{i+1:04d}",
        "name": name,
        "seller_id": sid,
        "price": price,
        "currency": currency,
        "category": cat,
        "stock_quantity": stock,
        "last_updated": updated,
        "active": random.random() > 0.1
    })

api_response = {
    "api_version": "2.1",
    "timestamp": "2024-03-15T10:30:00Z",
    "total_results": len(api_products),
    "page": 1,
    "per_page": 200,
    "products": api_products
}

with open(API_PATH, "w") as f:
    json.dump(api_response, f, indent=2)

print(f"Generated {len(api_products)} products in {API_PATH}")

# ============================================================
# 4. raw_products_messy.csv (~500 rows, deliberately messy)
# ============================================================

messy_rows = []

# We'll create ~500 products with various issues
for i in range(500):
    pid = f"MP{i+1:04d}"
    adj = random.choice(product_adjectives)
    noun = random.choice(product_nouns)

    # Generate the base product name
    name = f"{adj} {noun}"

    # Introduce messiness
    r = random.random()
    if r < 0.08:
        # ALL CAPS
        name = name.upper()
    elif r < 0.16:
        # all lower
        name = name.lower()
    elif r < 0.24:
        # rAnDom cAsE
        name = "".join(c.upper() if random.random() > 0.5 else c.lower() for c in name)
    elif r < 0.30:
        # Trailing whitespace
        name = name + "   "
    elif r < 0.36:
        # Leading whitespace
        name = "  " + name
    elif r < 0.42:
        # Non-breaking space (the invisible character trap)
        # Insert \xa0 instead of regular space
        parts = name.split(" ", 1)
        if len(parts) == 2:
            name = parts[0] + "\xa0" + parts[1]
    elif r < 0.46:
        # Double space
        name = name.replace(" ", "  ", 1)

    # Price
    price = round(random.uniform(3.0, 250.0), 2)

    # Currency - mix them up
    currency = random.choice(["GBP", "EUR", "USD", "gbp", "eur", "usd",
                               "GBP", "EUR", "USD"])

    # Category
    cat = random.choice(categories)
    if random.random() < 0.1:
        cat = cat.upper()
    if random.random() < 0.05:
        cat = "  " + cat

    # Seller
    seller = random.choice(["alpha", "beta", "gamma"])

    # Date - various formats
    base_date = datetime(2024, 3, 1) + timedelta(days=random.randint(0, 14))
    dr = random.random()
    if seller == "alpha" or dr < 0.33:
        date_str = base_date.strftime("%d/%m/%Y")
    elif seller == "beta" or dr < 0.66:
        date_str = base_date.strftime("%Y-%m-%d")
    else:
        date_str = base_date.strftime("%m/%d/%Y")

    # Some missing values
    if random.random() < 0.05:
        price = ""
    if random.random() < 0.03:
        cat = ""
    if random.random() < 0.02:
        date_str = ""

    messy_rows.append({
        "product_id": pid,
        "product_name": name,
        "price": price,
        "currency": currency,
        "category": cat,
        "seller": seller,
        "last_updated": date_str
    })

# Now inject some deliberate near-duplicates:
# Same product name but one has \xa0 and the other has normal space
duplicate_pairs = [
    ("Handmade Ceramic Mug", "Handmade\xa0Ceramic Mug"),
    ("Vintage Leather Wallet", "Vintage\xa0Leather Wallet"),
    ("Premium Glass Vase", "Premium\xa0Glass Vase"),
    ("Artisan Wooden Bowl", "Artisan\xa0Wooden Bowl"),
    ("Elegant Silver Ring", "Elegant\xa0Silver Ring"),
    ("Rustic Oak Cutting Board", "Rustic\xa0Oak Cutting Board"),
    ("Modern Brass Candleholder", "Modern\xa0Brass Candleholder"),
    ("Natural Wool Blanket", "Natural\xa0Wool Blanket"),
]

for normal_name, nbsp_name in duplicate_pairs:
    base_date = datetime(2024, 3, 5)
    date_str = base_date.strftime("%Y-%m-%d")
    price = round(random.uniform(15.0, 80.0), 2)

    # Normal version
    messy_rows.append({
        "product_id": f"MP{len(messy_rows)+1:04d}",
        "product_name": normal_name,
        "price": price,
        "currency": "GBP",
        "category": "home",
        "seller": "alpha",
        "last_updated": date_str
    })
    # \xa0 version (same price, same everything else)
    messy_rows.append({
        "product_id": f"MP{len(messy_rows)+1:04d}",
        "product_name": nbsp_name,
        "price": price,
        "currency": "GBP",
        "category": "home",
        "seller": "alpha",
        "last_updated": date_str
    })

with open(MESSY_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "product_id", "product_name", "price", "currency",
        "category", "seller", "last_updated"
    ])
    writer.writeheader()
    writer.writerows(messy_rows)

print(f"Generated {len(messy_rows)} rows in {MESSY_PATH}")
print("\nDone! All data files generated.")
