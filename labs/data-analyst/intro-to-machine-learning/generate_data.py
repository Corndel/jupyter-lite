"""Generate financial fraud and customer profile data for the Intro to Machine Learning lab."""
import csv
import random
from pathlib import Path

import numpy as np

random.seed(42)
np.random.seed(42)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

NUM_CUSTOMERS = 500
NUM_TRANSACTIONS = 5000
FRAUD_RATE = 0.03

MERCHANT_CATEGORIES = [
    "groceries", "electronics", "restaurants", "travel",
    "online_retail", "cash_withdrawal", "fuel",
]
DAYS_OF_WEEK = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]
REGIONS = ["North", "South", "East", "West", "Central"]


def generate_customer_profiles(filepath):
    """Generate ~500 customer profiles with natural demographic clusters."""
    fieldnames = [
        "customer_id", "age", "income_bracket", "account_age_months",
        "num_products", "avg_monthly_spend", "region",
    ]

    rows = []
    for i in range(1, NUM_CUSTOMERS + 1):
        # Pick a cluster
        cluster = random.choices(
            ["young_professional", "family", "retiree", "high_net_worth"],
            weights=[30, 35, 20, 15],
        )[0]

        if cluster == "young_professional":
            age = int(np.clip(np.random.normal(28, 3), 22, 35))
            income = random.choice(["medium"] * 70 + ["low"] * 20 + ["high"] * 10)
            num_products = random.choices([1, 2, 3], weights=[40, 45, 15])[0]
            account_months = int(np.clip(np.random.normal(24, 12), 1, 60))
            avg_spend = round(float(np.clip(np.random.normal(800, 300), 200, 2000)), 2)

        elif cluster == "family":
            age = int(np.clip(np.random.normal(40, 5), 30, 50))
            income = random.choice(["medium"] * 40 + ["high"] * 50 + ["very_high"] * 10)
            num_products = random.choices([3, 4, 5], weights=[35, 40, 25])[0]
            account_months = int(np.clip(np.random.normal(96, 36), 12, 180))
            avg_spend = round(float(np.clip(np.random.normal(1800, 600), 500, 4000)), 2)

        elif cluster == "retiree":
            age = int(np.clip(np.random.normal(70, 5), 60, 80))
            income = random.choice(["low"] * 30 + ["medium"] * 45 + ["high"] * 25)
            num_products = random.choices([2, 3, 4], weights=[40, 40, 20])[0]
            account_months = int(np.clip(np.random.normal(180, 40), 60, 240))
            avg_spend = round(float(np.clip(np.random.normal(1000, 400), 200, 2500)), 2)

        else:  # high_net_worth
            age = int(np.clip(np.random.normal(50, 8), 35, 65))
            income = "very_high"
            num_products = random.choices([4, 5, 6], weights=[30, 40, 30])[0]
            account_months = int(np.clip(np.random.normal(120, 48), 24, 240))
            avg_spend = round(float(np.clip(np.random.normal(3500, 800), 1500, 5000)), 2)

        rows.append({
            "customer_id": f"CUST-{i:03d}",
            "age": age,
            "income_bracket": income,
            "account_age_months": account_months,
            "num_products": num_products,
            "avg_monthly_spend": avg_spend,
            "region": random.choice(REGIONS),
        })

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


def generate_transactions(filepath, customers):
    """Generate ~5000 transactions with ~3% fraud rate."""
    fieldnames = [
        "transaction_id", "customer_id", "amount", "merchant_category",
        "hour_of_day", "day_of_week", "is_international",
        "distance_from_home_km", "is_fraud",
    ]

    num_fraud = int(NUM_TRANSACTIONS * FRAUD_RATE)
    num_legit = NUM_TRANSACTIONS - num_fraud

    customer_ids = [c["customer_id"] for c in customers]

    rows = []

    # Legitimate transactions
    for i in range(num_legit):
        # Amount: mostly 5-500, some up to 2000
        if random.random() < 0.85:
            amount = round(float(np.clip(np.random.lognormal(3.5, 0.8), 5, 500)), 2)
        else:
            amount = round(float(np.clip(np.random.lognormal(5.5, 0.6), 200, 2000)), 2)

        # Hour: spread across the day, peaking in business hours
        hour = int(np.clip(np.random.normal(14, 5), 0, 23))

        # Distance from home: mostly close
        distance = round(float(np.clip(np.random.exponential(5), 0, 20)), 1)

        rows.append({
            "transaction_id": f"TXN-{i + 1:07d}",
            "customer_id": random.choice(customer_ids),
            "amount": amount,
            "merchant_category": random.choice(MERCHANT_CATEGORIES),
            "hour_of_day": hour,
            "day_of_week": random.choice(DAYS_OF_WEEK),
            "is_international": random.random() < 0.05,
            "distance_from_home_km": distance,
            "is_fraud": False,
        })

    # Fraudulent transactions
    for i in range(num_fraud):
        # Amount: tends higher, 200-5000
        amount = round(float(np.clip(np.random.lognormal(5.8, 0.7), 50, 5000)), 2)

        # Hour: skewed towards late night (0-5) but not exclusively
        if random.random() < 0.55:
            hour = random.randint(0, 5)
        else:
            hour = random.randint(0, 23)

        # Distance: many far from home, but some overlap
        if random.random() < 0.6:
            distance = round(float(np.clip(np.random.exponential(80), 20, 500)), 1)
        else:
            distance = round(float(np.clip(np.random.exponential(10), 0, 50)), 1)

        # Merchant category: slightly skewed towards online/electronics/cash
        fraud_merchants = random.choices(
            MERCHANT_CATEGORIES,
            weights=[5, 20, 5, 15, 25, 20, 10],
        )[0]

        rows.append({
            "transaction_id": f"TXN-{num_legit + i + 1:07d}",
            "customer_id": random.choice(customer_ids),
            "amount": amount,
            "merchant_category": fraud_merchants,
            "hour_of_day": hour,
            "day_of_week": random.choice(DAYS_OF_WEEK),
            "is_international": random.random() < 0.30,
            "distance_from_home_km": distance,
            "is_fraud": True,
        })

    # Shuffle so fraud isn't all at the end
    random.shuffle(rows)

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


if __name__ == "__main__":
    customers = generate_customer_profiles(DATA_DIR / "customer_profiles.csv")
    print(f"Generated {len(customers)} customer profiles")

    transactions = generate_transactions(DATA_DIR / "transactions.csv", customers)
    fraud_count = sum(1 for t in transactions if t["is_fraud"])
    print(f"Generated {len(transactions)} transactions ({fraud_count} fraud, {fraud_count / len(transactions):.1%})")
