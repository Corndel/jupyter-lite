"""Generate all data files for the data-quality module.

Run:  pip install pyarrow && python generate_data.py
"""

import csv
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

random.seed(42)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MERCHANT_CATEGORIES = [
    "groceries", "dining", "transport", "entertainment", "utilities",
    "retail", "healthcare", "travel", "subscriptions", "fuel",
]

MERCHANT_NAMES = {
    "groceries": ["Tesco", "Sainsbury's", "Aldi", "Lidl", "Waitrose", "M&S Food"],
    "dining": ["Nando's", "Pizza Express", "Wagamama", "Greggs", "Pret A Manger"],
    "transport": ["TfL", "Uber", "Bolt", "National Rail", "Trainline"],
    "entertainment": ["Netflix", "Spotify", "Vue Cinema", "Amazon Prime", "Sky"],
    "utilities": ["British Gas", "EDF Energy", "Thames Water", "BT", "Virgin Media"],
    "retail": ["Amazon", "ASOS", "John Lewis", "Argos", "Currys"],
    "healthcare": ["Boots", "Superdrug", "Specsavers", "Bupa", "LloydsPharmacy"],
    "travel": ["Booking.com", "Ryanair", "EasyJet", "Airbnb", "Expedia"],
    "subscriptions": ["Apple", "Google", "Microsoft 365", "Adobe", "Dropbox"],
    "fuel": ["Shell", "BP", "Esso", "Texaco", "Jet"],
}

CURRENCIES = ["GBP"] * 80 + ["EUR"] * 12 + ["USD"] * 8
CARD_TYPES = ["debit", "credit"]
STATUSES = ["completed"] * 75 + ["pending"] * 12 + ["declined"] * 8 + ["refunded"] * 5

FIRST_NAMES = [
    "Oliver", "Amelia", "George", "Isla", "Harry", "Ava", "Noah", "Mia",
    "Jack", "Lily", "Leo", "Grace", "Oscar", "Freya", "Charlie", "Emily",
    "Arthur", "Rosie", "Henry", "Sophia",
]
LAST_NAMES = [
    "Smith", "Jones", "Williams", "Brown", "Taylor", "Davies", "Wilson",
    "Evans", "Thomas", "Roberts", "Johnson", "Walker", "Wright", "Robinson",
    "Thompson", "White", "Hughes", "Edwards", "Green", "Hall",
]

SORT_CODES = ["20-45-67", "30-12-89", "40-07-23", "11-22-33", "60-83-71"]


def random_timestamp(start: datetime, end: datetime) -> str:
    delta = end - start
    offset = random.random() * delta.total_seconds()
    dt = start + timedelta(seconds=offset)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def random_amount_normal() -> float:
    """Most transactions between 5 and 200."""
    amount = random.gauss(45, 35)
    return round(max(1.0, min(amount, 500.0)), 2)


def make_customer_ids(n: int = 800) -> list[str]:
    return [f"CUST{i:05d}" for i in range(1, n + 1)]


CUSTOMER_IDS = make_customer_ids()

# ---------------------------------------------------------------------------
# 1. transactions_batch.csv  (~5,000 rows)
# ---------------------------------------------------------------------------

def generate_transactions_batch():
    rows = []
    start = datetime(2024, 10, 1)
    end = datetime(2024, 12, 31)

    for i in range(5000):
        cat = random.choice(MERCHANT_CATEGORIES)
        merchant = random.choice(MERCHANT_NAMES[cat])
        currency = random.choice(CURRENCIES)
        status = random.choice(STATUSES)
        card = random.choice(CARD_TYPES)
        customer = random.choice(CUSTOMER_IDS)

        # Amount: mostly normal, with a handful of extreme outliers
        if i < 3:
            # The cognitive anchors: huge outliers
            amount = random.choice([500_000.00, 487_250.00, 312_999.99])
        elif i < 15:
            # Some moderately large outliers
            amount = round(random.uniform(5_000, 50_000), 2)
        else:
            amount = random_amount_normal()

        row = {
            "transaction_id": f"TXN{uuid.uuid4().hex[:12].upper()}",
            "timestamp": random_timestamp(start, end),
            "amount": amount,
            "currency": currency,
            "merchant_name": merchant,
            "merchant_category": cat,
            "card_type": card,
            "status": status,
            "customer_id": customer,
        }

        # Introduce some nulls (5-10% in selected columns)
        if random.random() < 0.07:
            row["merchant_category"] = ""
        if random.random() < 0.05:
            row["card_type"] = ""
        if random.random() < 0.08:
            row["customer_id"] = ""

        rows.append(row)

    # Shuffle so outliers aren't at the top
    random.shuffle(rows)

    path = DATA_DIR / "transactions_batch.csv"
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"  {path.name}: {len(rows)} rows")


# ---------------------------------------------------------------------------
# 2. incoming_payments.json  (~200 records, some with quality issues)
# ---------------------------------------------------------------------------

def generate_incoming_payments():
    records = []
    start = datetime(2024, 11, 1)
    end = datetime(2024, 12, 31)
    future = datetime(2026, 6, 15)

    merchant_info = [
        {"name": "Tesco", "category": "groceries"},
        {"name": "Nando's", "category": "dining"},
        {"name": "Amazon", "category": "retail"},
        {"name": "Shell", "category": "fuel"},
        {"name": "Netflix", "category": "subscriptions"},
        {"name": "TfL", "category": "transport"},
        {"name": "Boots", "category": "healthcare"},
        {"name": "Ryanair", "category": "travel"},
    ]

    for i in range(200):
        pay_id = f"PAY{i + 1:04d}"
        sort_code = random.choice(SORT_CODES)
        account = f"{random.randint(10000000, 99999999)}"
        merchant = random.choice(merchant_info)
        currency = random.choice(["GBP"] * 85 + ["EUR"] * 10 + ["USD"] * 5)

        rec = {
            "id": pay_id,
            "amount": round(random.uniform(5, 500), 2),
            "currency": currency,
            "sender_sort_code": sort_code,
            "sender_account": account,
            "timestamp": random_timestamp(start, end),
            "merchant": dict(merchant),
        }

        # --- Introduce data quality issues ---

        # Sort codes in the amount field (the cognitive anchor)
        if i in (3, 27, 58, 112, 167):
            rec["amount"] = random.choice(SORT_CODES)

        # Negative amounts
        elif i in (11, 44, 89, 150):
            rec["amount"] = round(-random.uniform(10, 200), 2)

        # Future dates
        elif i in (7, 62, 130):
            rec["timestamp"] = random_timestamp(
                datetime(2026, 4, 1), datetime(2026, 9, 30)
            )

        # Missing required fields
        elif i in (19, 77, 145):
            del rec["currency"]
        elif i in (33, 99):
            del rec["sender_account"]
        elif i in (55, 180):
            rec["merchant"] = {"name": None, "category": None}

        records.append(rec)

    path = DATA_DIR / "incoming_payments.json"
    with open(path, "w") as f:
        json.dump(records, f, indent=2)

    print(f"  {path.name}: {len(records)} records")


# ---------------------------------------------------------------------------
# 3. payments_v1.parquet  (~1,000 rows) — original schema
# ---------------------------------------------------------------------------

def generate_payments_v1():
    n = 1000
    start = datetime(2024, 6, 1)
    end = datetime(2024, 12, 31)

    data = {
        "payment_id": [f"PMT{i + 1:05d}" for i in range(n)],
        "date": [
            (start + timedelta(days=random.randint(0, (end - start).days))).strftime(
                "%Y-%m-%d"
            )
            for _ in range(n)
        ],
        "amount": [round(random.uniform(5, 2000), 2) for _ in range(n)],
        "currency": [random.choice(["GBP"] * 80 + ["EUR"] * 15 + ["USD"] * 5) for _ in range(n)],
        "sender_name": [
            f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            for _ in range(n)
        ],
        "recipient_name": [
            f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            for _ in range(n)
        ],
        "status": [random.choice(["completed", "pending", "failed"]) for _ in range(n)],
    }

    table = pa.table(data)
    path = DATA_DIR / "payments_v1.parquet"
    pq.write_table(table, path)
    print(f"  {path.name}: {n} rows, schema: {list(data.keys())}")


# ---------------------------------------------------------------------------
# 4. payments_v2.parquet  (~1,000 rows) — new schema with changes
# ---------------------------------------------------------------------------

def generate_payments_v2():
    n = 1000
    start = datetime(2025, 1, 1)
    end = datetime(2025, 3, 31)

    data = {
        "payment_id": [f"PMT{i + 1001:05d}" for i in range(n)],
        "date": [
            (start + timedelta(days=random.randint(0, (end - start).days))).strftime(
                "%Y-%m-%d"
            )
            for _ in range(n)
        ],
        # NEW: reference_number inserted between date and amount
        "reference_number": [f"REF-{uuid.uuid4().hex[:8].upper()}" for _ in range(n)],
        "amount": [round(random.uniform(5, 2000), 2) for _ in range(n)],
        "currency": [random.choice(["GBP"] * 80 + ["EUR"] * 15 + ["USD"] * 5) for _ in range(n)],
        # RENAMED: sender_name -> payer_name
        "payer_name": [
            f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            for _ in range(n)
        ],
        "recipient_name": [
            f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            for _ in range(n)
        ],
        "status": [random.choice(["completed", "pending", "failed"]) for _ in range(n)],
        # NEW: processing_fee
        "processing_fee": [round(random.uniform(0.10, 5.00), 2) for _ in range(n)],
    }

    table = pa.table(data)
    path = DATA_DIR / "payments_v2.parquet"
    pq.write_table(table, path)
    print(f"  {path.name}: {n} rows, schema: {list(data.keys())}")


# ---------------------------------------------------------------------------
# 5. transactions_historical.parquet  (~100,000 rows)
# ---------------------------------------------------------------------------

def generate_transactions_historical():
    n = 100_000
    start = datetime(2024, 1, 1)
    end = datetime(2024, 12, 31)

    # Generate timestamps with realistic patterns
    timestamps = []
    for _ in range(n):
        day_offset = random.randint(0, (end - start).days)
        dt = start + timedelta(days=day_offset)

        # More transactions on weekdays
        if dt.weekday() >= 5:  # weekend
            if random.random() < 0.3:
                day_offset = random.randint(0, (end - start).days)
                dt = start + timedelta(days=day_offset)
                while dt.weekday() >= 5:
                    day_offset = random.randint(0, (end - start).days)
                    dt = start + timedelta(days=day_offset)

        # More transactions in Nov-Dec (holiday season)
        if dt.month in (11, 12) and random.random() < 0.3:
            pass  # keep it — holiday boost
        elif dt.month in (11, 12):
            pass

        hour = random.choices(
            range(24),
            weights=[1, 1, 1, 1, 1, 2, 4, 7, 9, 10, 10, 9, 10, 10, 9, 8, 7, 8, 9, 8, 6, 4, 2, 1],
        )[0]
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        dt = dt.replace(hour=hour, minute=minute, second=second)
        timestamps.append(dt.strftime("%Y-%m-%dT%H:%M:%SZ"))

    categories = [random.choice(MERCHANT_CATEGORIES) for _ in range(n)]
    merchants = [random.choice(MERCHANT_NAMES[cat]) for cat in categories]

    amounts = []
    for _ in range(n):
        r = random.random()
        if r < 0.001:
            amounts.append(round(random.uniform(50_000, 500_000), 2))
        elif r < 0.01:
            amounts.append(round(random.uniform(1_000, 50_000), 2))
        else:
            amounts.append(round(max(0.50, random.gauss(45, 35)), 2))

    data = {
        "transaction_id": [f"TXN{uuid.uuid4().hex[:12].upper()}" for _ in range(n)],
        "timestamp": timestamps,
        "amount": amounts,
        "currency": [random.choice(CURRENCIES) for _ in range(n)],
        "merchant_name": merchants,
        "merchant_category": categories,
        "card_type": [random.choice(CARD_TYPES) for _ in range(n)],
        "status": [random.choice(STATUSES) for _ in range(n)],
        "customer_id": [random.choice(CUSTOMER_IDS) for _ in range(n)],
        "processing_time_ms": [
            random.randint(50, 3000) if random.random() < 0.95 else random.randint(3000, 15000)
            for _ in range(n)
        ],
    }

    table = pa.table(data)
    path = DATA_DIR / "transactions_historical.parquet"
    pq.write_table(table, path)
    print(f"  {path.name}: {n} rows")


# ---------------------------------------------------------------------------
# Run all generators
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Generating data files...")
    generate_transactions_batch()
    generate_incoming_payments()
    generate_payments_v1()
    generate_payments_v2()
    generate_transactions_historical()
    print("Done.")
