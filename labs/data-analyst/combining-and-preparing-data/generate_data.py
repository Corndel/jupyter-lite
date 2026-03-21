"""
Generate synthetic supply chain logistics data for the
Combining and Preparing Data lab.

Produces:
    data/shipments_asia.csv      (~1000 rows)
    data/shipments_europe.csv    (~800 rows, different column names/date format)
    data/shipments_americas.json (~600 records, nested structure, unix timestamps)
    data/warehouse_inventory.csv (~500 rows, messy: duplicates, nulls, inconsistent names)
    data/suppliers.sqlite        (suppliers table, ~50 rows)
"""

import csv
import json
import os
import random
import sqlite3
from datetime import datetime, timedelta

random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def random_date_2024():
    """Return a random date in 2024 as a datetime object."""
    start = datetime(2024, 1, 1)
    offset = random.randint(0, 365)
    return start + timedelta(days=offset)


def fmt_yyyy_mm_dd(dt):
    return dt.strftime("%Y-%m-%d")


def fmt_dd_mm_yyyy(dt):
    return dt.strftime("%d/%m/%Y")


def unix_timestamp(dt):
    return int(dt.timestamp())


# ---------------------------------------------------------------------------
# City pools
# ---------------------------------------------------------------------------

ASIAN_CITIES = [
    "Shanghai", "Tokyo", "Seoul", "Mumbai", "Singapore", "Bangkok",
    "Hong Kong", "Taipei", "Jakarta", "Kuala Lumpur", "Manila", "Hanoi",
    "Shenzhen", "Osaka", "Busan",
]

EUROPEAN_CITIES = [
    "London", "Rotterdam", "Hamburg", "Antwerp", "Barcelona", "Marseille",
    "Genoa", "Piraeus", "Istanbul", "Gdansk", "Gothenburg", "Lisbon",
    "Dublin", "Le Havre", "Valencia",
]

AMERICAN_CITIES = [
    "New York", "Los Angeles", "Houston", "Miami", "Vancouver", "Santos",
    "Buenos Aires", "Cartagena", "Savannah", "Seattle", "Montreal",
    "Callao", "Manzanillo", "Kingston", "Balboa",
]

GLOBAL_DESTINATIONS = ASIAN_CITIES + EUROPEAN_CITIES + AMERICAN_CITIES

ASIAN_CARRIERS = ["Pacific Express", "Asia Cargo", "Global Freight", "Orient Lines"]
EUROPEAN_CARRIERS = ["Euro Logistics", "North Sea Shipping", "Continental Cargo", "Baltic Lines"]
AMERICAN_CARRIERS = ["Atlantic Express", "PanAm Freight", "Americas Cargo", "Gulf Shipping"]

STATUSES = ["delivered", "in_transit", "delayed", "customs_hold"]
STATUS_WEIGHTS = [0.55, 0.25, 0.12, 0.08]


def pick_status():
    return random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]


# ---------------------------------------------------------------------------
# Suppliers (SQLite) — created first so we can reference supplier_id
# ---------------------------------------------------------------------------

SUPPLIER_NAMES = [
    "Zhongshan Electronics", "Tata Components", "Samsung Parts Co",
    "Mitsubishi Materials", "Thai Precision", "SG MicroTech",
    "Hyundai Supplies", "Manila Metals", "Jakarta Plastics",
    "Shenzhen Circuits", "Osaka Bearings", "Busan Steel",
    "Taipei Semiconductors", "Hanoi Textiles", "KL Rubber Works",
    "Shanghai Fasteners", "Tokyo Instruments", "Seoul Chemicals",
    "Mumbai Castings", "Bangkok Polymers", "HK Optics Ltd",
    "Asia Paper Corp", "Orient Adhesives", "Pacific Resins",
    "Fuji Coatings", "Mekong Timber", "Bengal Fibres",
    "Luzon Ceramics", "Java Glass Works", "Borneo Composites",
    "Sumatra Foils", "Ganges Dyes", "Yangtze Alloys",
    "Indus Packaging", "Pearl River Mfg", "Chao Phraya Tools",
    "Saigon Wiring", "Colombo Textiles", "Dhaka Garments",
    "Karachi Leather", "Rangoon Lacquer", "Phnom Penh Silk",
    "Vientiane Wood", "Ulaanbaatar Felt", "Bishkek Wool",
    "Almaty Metals", "Tashkent Cotton", "Baku Petrochemicals",
    "Tbilisi Ceramics", "Yerevan Stone",
]

SUPPLIER_COUNTRIES = [
    "China", "India", "South Korea", "Japan", "Thailand", "Singapore",
    "South Korea", "Philippines", "Indonesia", "China", "Japan",
    "South Korea", "Taiwan", "Vietnam", "Malaysia",
    "China", "Japan", "South Korea", "India", "Thailand", "Hong Kong",
    "China", "China", "China", "Japan", "Vietnam", "India",
    "Philippines", "Indonesia", "Indonesia", "Indonesia", "India",
    "China", "India", "China", "Thailand", "Vietnam", "Sri Lanka",
    "Bangladesh", "Pakistan", "Myanmar", "Cambodia", "Laos",
    "Mongolia", "Kyrgyzstan", "Kazakhstan", "Uzbekistan",
    "Azerbaijan", "Georgia", "Armenia",
]


def create_suppliers_db():
    db_path = os.path.join(DATA_DIR, "suppliers.sqlite")
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE suppliers (
            supplier_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            country TEXT NOT NULL,
            reliability_rating REAL NOT NULL,
            active_since TEXT NOT NULL
        )
    """)

    for i, (name, country) in enumerate(zip(SUPPLIER_NAMES, SUPPLIER_COUNTRIES), start=1):
        rating = round(random.uniform(1.0, 5.0), 1)
        year = random.randint(2005, 2023)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        active_since = f"{year:04d}-{month:02d}-{day:02d}"
        cur.execute(
            "INSERT INTO suppliers VALUES (?, ?, ?, ?, ?)",
            (i, name, country, rating, active_since),
        )

    conn.commit()
    conn.close()
    return len(SUPPLIER_NAMES)


# ---------------------------------------------------------------------------
# Shipments — Asia (CSV, clean, YYYY-MM-DD)
# ---------------------------------------------------------------------------

def create_shipments_asia(n=1000):
    num_suppliers = len(SUPPLIER_NAMES)
    path = os.path.join(DATA_DIR, "shipments_asia.csv")
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "shipment_id", "origin", "destination", "weight_kg", "cost_usd",
            "ship_date", "carrier", "status", "supplier_id",
        ])
        for i in range(1, n + 1):
            sid = f"SHP-{i:05d}"
            origin = random.choice(ASIAN_CITIES)
            dest = random.choice([c for c in GLOBAL_DESTINATIONS if c != origin])
            weight = round(random.uniform(0.5, 5000.0), 2)
            cost = round(random.uniform(50.0, 50000.0), 2)
            ship_date = fmt_yyyy_mm_dd(random_date_2024())
            carrier = random.choice(ASIAN_CARRIERS)
            status = pick_status()
            supplier_id = random.randint(1, num_suppliers)
            writer.writerow([
                sid, origin, dest, weight, cost,
                ship_date, carrier, status, supplier_id,
            ])
    return n


# ---------------------------------------------------------------------------
# Shipments — Europe (CSV, different column names, DD/MM/YYYY dates)
# ---------------------------------------------------------------------------

def create_shipments_europe(n=800):
    path = os.path.join(DATA_DIR, "shipments_europe.csv")
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        # Deliberately different column names: "id" not "shipment_id",
        # "cost_eur" not "cost_usd"
        writer.writerow([
            "id", "origin", "destination", "weight_kg", "cost_eur",
            "ship_date", "carrier", "status",
        ])
        for i in range(1, n + 1):
            sid = f"SHP-{10000 + i:05d}"
            origin = random.choice(EUROPEAN_CITIES)
            dest = random.choice([c for c in GLOBAL_DESTINATIONS if c != origin])
            weight = round(random.uniform(0.5, 5000.0), 2)
            cost = round(random.uniform(50.0, 50000.0), 2)
            ship_date = fmt_dd_mm_yyyy(random_date_2024())  # DD/MM/YYYY!
            carrier = random.choice(EUROPEAN_CARRIERS)
            status = pick_status()
            writer.writerow([
                sid, origin, dest, weight, cost,
                ship_date, carrier, status,
            ])
    return n


# ---------------------------------------------------------------------------
# Shipments — Americas (nested JSON, unix timestamps)
# ---------------------------------------------------------------------------

def create_shipments_americas(n=600):
    path = os.path.join(DATA_DIR, "shipments_americas.json")
    records = []
    for i in range(1, n + 1):
        sid = f"SHP-{20000 + i:05d}"
        origin = random.choice(AMERICAN_CITIES)
        dest = random.choice([c for c in GLOBAL_DESTINATIONS if c != origin])
        weight = round(random.uniform(0.5, 5000.0), 2)
        dt = random_date_2024()
        cost = round(random.uniform(50.0, 50000.0), 2)
        insurance = round(cost * random.uniform(0.01, 0.05), 2)
        carrier = random.choice(AMERICAN_CARRIERS)
        status = pick_status()
        records.append({
            "shipment_id": sid,
            "route": {
                "origin": origin,
                "destination": dest,
            },
            "details": {
                "weight_kg": weight,
                "ship_date_unix": unix_timestamp(dt),
            },
            "financials": {
                "cost_usd": cost,
                "insurance_usd": insurance,
            },
            "carrier": carrier,
            "status": status,
        })

    with open(path, "w") as f:
        json.dump(records, f, indent=2)
    return n


# ---------------------------------------------------------------------------
# Warehouse inventory (messy: duplicates, nulls, inconsistent product names)
# ---------------------------------------------------------------------------

PRODUCTS_CLEAN = [
    "Widget A", "Widget B", "Gadget X", "Gadget Y", "Connector M",
    "Connector N", "Sensor Alpha", "Sensor Beta", "Module P", "Module Q",
    "Bracket R", "Bracket S", "Valve T", "Valve U", "Relay V",
    "Relay W", "Harness C", "Harness D", "Filter E", "Filter F",
]

# Messy variants for each clean name
PRODUCT_VARIANTS = {}
for name in PRODUCTS_CLEAN:
    lower_hyphen = name.lower().replace(" ", "-")
    upper = name.upper()
    double_space = name.replace(" ", "  ")
    PRODUCT_VARIANTS[name] = [name, lower_hyphen, upper, double_space]


def create_warehouse_inventory(n=500, n_duplicates=30, n_missing=40):
    path = os.path.join(DATA_DIR, "warehouse_inventory.csv")
    warehouses = [f"WH-{i:02d}" for i in range(1, 6)]

    rows = []
    for _ in range(n - n_duplicates - n_missing):
        wh = random.choice(warehouses)
        prod_clean = random.choice(PRODUCTS_CLEAN)
        prod_name = random.choice(PRODUCT_VARIANTS[prod_clean])
        prod_id = f"PROD-{random.randint(100, 999):03d}"
        qty = random.randint(1, 5000)
        restock = fmt_yyyy_mm_dd(random_date_2024())
        rows.append([wh, prod_id, prod_name, qty, restock])

    # Add rows with missing product_name or quantity (~40)
    for _ in range(n_missing):
        wh = random.choice(warehouses)
        prod_id = f"PROD-{random.randint(100, 999):03d}"
        restock = fmt_yyyy_mm_dd(random_date_2024())
        if random.random() < 0.5:
            # Missing product_name
            rows.append([wh, prod_id, "", random.randint(1, 5000), restock])
        else:
            # Missing quantity
            prod_clean = random.choice(PRODUCTS_CLEAN)
            prod_name = random.choice(PRODUCT_VARIANTS[prod_clean])
            rows.append([wh, prod_id, prod_name, "", restock])

    random.shuffle(rows)

    # Pick 30 rows to duplicate (genuine duplicates)
    duplicates = [list(row) for row in random.choices(rows, k=n_duplicates)]
    rows.extend(duplicates)
    random.shuffle(rows)

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "warehouse_id", "product_id", "product_name", "quantity",
            "last_restock_date",
        ])
        writer.writerows(rows)
    return len(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    n_suppliers = create_suppliers_db()
    print(f"Created suppliers.sqlite          ({n_suppliers} rows)")

    n_asia = create_shipments_asia()
    print(f"Created shipments_asia.csv        ({n_asia} rows)")

    n_europe = create_shipments_europe()
    print(f"Created shipments_europe.csv      ({n_europe} rows)")

    n_americas = create_shipments_americas()
    print(f"Created shipments_americas.json   ({n_americas} records)")

    n_inventory = create_warehouse_inventory()
    print(f"Created warehouse_inventory.csv   ({n_inventory} rows)")

    print("\nDone. All files written to:", DATA_DIR)
