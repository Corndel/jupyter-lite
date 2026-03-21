"""Generate urban housing market data for the Regression and Forecasting lab."""
import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

NEIGHBOURHOODS = [
    "Ashworth", "Beechwood", "Castlegate", "Drayton", "Eastmoor",
    "Ferndale", "Gladstone", "Hartley", "Ironbridge", "Jubilee",
    "Kingsway", "Langford", "Millbrook", "Northgate", "Oakfield",
    "Parkside", "Queensbury", "Riverside", "Stoneleigh", "Thornton",
    "Uppermill", "Victoria", "Westbury", "Yarrow", "Zelton",
    "Brindley", "Chapel End", "Dunmore", "Elmswood", "Foxhall",
]

# Neighbourhood premiums: some areas are more expensive than others
NEIGHBOURHOOD_PREMIUMS = {n: int(random.uniform(-50000, 50000)) for n in NEIGHBOURHOODS}

# Neighbourhood features (income, crime, green space, school quality)
NEIGHBOURHOOD_FEATURES = {}
for n in NEIGHBOURHOODS:
    premium = NEIGHBOURHOOD_PREMIUMS[n]
    # Higher-premium areas tend to have higher income, lower crime, better schools
    premium_factor = (premium + 50000) / 100000  # 0 to 1
    avg_income = int(25000 + premium_factor * 45000 + random.gauss(0, 5000))
    avg_income = max(25000, min(80000, avg_income))
    crime_rate = round(60 - premium_factor * 40 + random.gauss(0, 5), 1)
    crime_rate = max(5.0, min(60.0, crime_rate))
    green_space = round(5 + premium_factor * 25 + random.gauss(0, 4), 1)
    green_space = max(5.0, min(40.0, green_space))
    school_rating = round(1.5 + premium_factor * 3.0 + random.gauss(0, 0.3), 1)
    school_rating = max(1.0, min(5.0, school_rating))
    NEIGHBOURHOOD_FEATURES[n] = {
        "avg_household_income": avg_income,
        "crime_rate_per_1000": crime_rate,
        "green_space_pct": green_space,
        "school_rating_avg": school_rating,
    }

EPC_RATINGS = ["A", "B", "C", "C", "C", "D", "D", "D", "D", "E", "E", "F", "G"]

# Bedroom distribution weighted towards 2-3
BEDROOM_WEIGHTS = [0.05, 0.30, 0.35, 0.15, 0.10, 0.05]
BEDROOMS_CHOICES = [1, 2, 3, 4, 5, 6]


def _exponential(lam):
    """Sample from an exponential distribution with mean `lam`."""
    return -lam * math.log(1.0 - random.random())


def generate_property_sales(filepath, num_rows=3000):
    """Generate ~3000 rows of property sale data."""
    fieldnames = [
        "property_id", "sale_price", "bedrooms", "bathrooms", "floor_area_sqm",
        "garden_sqm", "age_years", "distance_to_station_km",
        "distance_to_school_km", "neighbourhood", "sale_date", "epc_rating",
    ]

    rows = []
    for i in range(1, num_rows + 1):
        prop_id = f"PROP-{i:05d}"

        bedrooms = random.choices(BEDROOMS_CHOICES, weights=BEDROOM_WEIGHTS, k=1)[0]
        bathrooms = min(bedrooms, random.choices([1, 2, 3], weights=[0.5, 0.35, 0.15], k=1)[0])

        # Floor area correlated with bedrooms
        base_area = 25 + bedrooms * 18
        floor_area = round(max(30, min(250, base_area + random.gauss(0, 15))), 1)

        # Garden: 20% have none
        if random.random() < 0.20:
            garden = 0.0
        else:
            garden = round(max(0, min(200, random.gauss(40 + bedrooms * 15, 25))), 1)

        age_years = int(max(0, min(150, _exponential(40))))
        distance_station = round(max(0.1, min(5.0, _exponential(1.5) + 0.1)), 1)
        distance_school = round(max(0.2, min(3.0, _exponential(0.8) + 0.2)), 1)

        neighbourhood = random.choice(NEIGHBOURHOODS)
        premium = NEIGHBOURHOOD_PREMIUMS[neighbourhood]

        # Sale date between 2022-01-01 and 2024-12-31
        days_offset = random.randint(0, 1095)
        sale_date = date(2022, 1, 1) + timedelta(days=days_offset)
        if sale_date > date(2024, 12, 31):
            sale_date = date(2024, 12, 31)
        sale_date_str = sale_date.strftime("%Y-%m-%d")

        epc_rating = random.choice(EPC_RATINGS)

        # Price formula
        price = (
            floor_area * 3500
            + bedrooms * 15000
            + premium
            - age_years * 200
            - distance_station * 8000
            + garden * 100
        )

        # U-shaped age: very old properties get a character premium
        if age_years > 100:
            price += 30000

        # Add noise
        price += random.gauss(0, 25000)

        # Clip
        price = int(max(80000, min(1500000, price)))

        row = {
            "property_id": prop_id,
            "sale_price": price,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "floor_area_sqm": floor_area,
            "garden_sqm": garden,
            "age_years": age_years,
            "distance_to_station_km": distance_station,
            "distance_to_school_km": distance_school,
            "neighbourhood": neighbourhood,
            "sale_date": sale_date_str,
            "epc_rating": epc_rating,
        }
        rows.append(row)

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    prices = [r["sale_price"] for r in rows]
    print(f"  Wrote {len(rows)} rows to {filepath}")
    print(f"  Price range: £{min(prices):,} – £{max(prices):,}")
    print(f"  Mean price: £{int(sum(prices) / len(prices)):,}")


def generate_neighbourhood_features(filepath):
    """Generate neighbourhood-level features for ~30 neighbourhoods."""
    fieldnames = [
        "neighbourhood", "avg_household_income", "crime_rate_per_1000",
        "green_space_pct", "school_rating_avg",
    ]

    rows = []
    for n in NEIGHBOURHOODS:
        row = {"neighbourhood": n, **NEIGHBOURHOOD_FEATURES[n]}
        rows.append(row)

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Wrote {len(rows)} rows to {filepath}")


if __name__ == "__main__":
    print("Generating Regression and Forecasting lab data...")
    generate_property_sales(DATA_DIR / "property_sales.csv")
    generate_neighbourhood_features(DATA_DIR / "neighbourhood_features.csv")
    print("Done!")
