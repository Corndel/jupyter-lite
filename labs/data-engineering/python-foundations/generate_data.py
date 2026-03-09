"""Generate Mars rover telemetry CSV data files for the Python Foundations module."""
import csv
import random
import math
from datetime import date, timedelta

random.seed(42)


def generate_mars_sol_sample(filepath, num_rows=200):
    """Generate ~200 rows of Mars sol data."""
    fieldnames = [
        "sol", "earth_date", "min_temp_c", "max_temp_c",
        "pressure_pa", "wind_speed_ms", "uv_index", "instrument_status"
    ]

    start_date = date(2024, 1, 1)
    statuses = ["nominal"] * 85 + ["warning"] * 10 + ["offline"] * 5

    rows = []
    for i in range(1, num_rows + 1):
        earth_date = start_date + timedelta(days=i - 1)

        row = {
            "sol": i,
            "earth_date": earth_date.isoformat(),
            "min_temp_c": round(random.uniform(-80, -50), 1),
            "max_temp_c": round(random.uniform(-20, 5), 1),
            "pressure_pa": round(random.uniform(600, 900), 1),
            "wind_speed_ms": round(random.uniform(0, 30), 1),
            "uv_index": random.randint(0, 11),
            "instrument_status": random.choice(statuses),
        }

        # Sprinkle nulls: ~7% chance per nullable field
        for field in ["min_temp_c", "max_temp_c", "pressure_pa", "wind_speed_ms", "uv_index"]:
            if random.random() < 0.07:
                row[field] = ""

        rows.append(row)

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {filepath}")


def generate_mars_weather_2024(filepath, num_rows=5000):
    """Generate ~5000 rows of Mars weather data with seasonal patterns."""
    fieldnames = [
        "sol", "earth_date", "min_temp_c", "max_temp_c",
        "pressure_pa", "wind_speed_ms", "uv_index", "instrument_status"
    ]

    start_date = date(2024, 1, 1)
    statuses = ["nominal"] * 85 + ["warning"] * 10 + ["offline"] * 5

    rows = []
    for i in range(1, num_rows + 1):
        earth_date = start_date + timedelta(days=i - 1)

        # Seasonal variation: Mars year is ~687 Earth days
        # Use a sine wave to model seasonal temperature shifts
        season_phase = (i / 687) * 2 * math.pi
        seasonal_offset = 15 * math.sin(season_phase)  # +/- 15 degrees

        min_temp = round(random.uniform(-80, -50) + seasonal_offset, 1)
        max_temp = round(random.uniform(-20, 5) + seasonal_offset, 1)
        pressure = round(random.uniform(600, 900) + 50 * math.sin(season_phase + 0.5), 1)
        wind = round(random.uniform(0, 30) + 5 * abs(math.sin(season_phase * 2)), 1)
        uv = random.randint(0, 11)
        status = random.choice(statuses)

        row = {
            "sol": i,
            "earth_date": earth_date.isoformat(),
            "min_temp_c": min_temp,
            "max_temp_c": max_temp,
            "pressure_pa": pressure,
            "wind_speed_ms": wind,
            "uv_index": uv,
            "instrument_status": status,
        }

        # Sprinkle nulls: ~5% chance per nullable field
        for field in ["min_temp_c", "max_temp_c", "pressure_pa", "wind_speed_ms", "uv_index"]:
            if random.random() < 0.05:
                row[field] = ""

        rows.append(row)

    # Add ~50 duplicate rows (for teaching dedup)
    duplicate_indices = random.sample(range(len(rows)), 50)
    duplicates = [rows[i].copy() for i in duplicate_indices]
    rows.extend(duplicates)

    # Add ~10 extreme outlier readings
    for _ in range(10):
        outlier_idx = random.randint(0, len(rows) - 1)
        outlier_type = random.choice(["temp", "wind", "pressure"])
        if outlier_type == "temp":
            rows[outlier_idx]["min_temp_c"] = round(random.uniform(-120, -100), 1)
            rows[outlier_idx]["max_temp_c"] = round(random.uniform(20, 40), 1)
        elif outlier_type == "wind":
            rows[outlier_idx]["wind_speed_ms"] = round(random.uniform(80, 150), 1)
        else:
            rows[outlier_idx]["pressure_pa"] = round(random.uniform(50, 200), 1)

    # Sort by sol to keep order (duplicates will appear near originals)
    rows.sort(key=lambda r: r["sol"])

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {filepath}")


if __name__ == "__main__":
    generate_mars_sol_sample("modules/python-foundations/data/mars_sol_sample.csv")
    generate_mars_weather_2024("modules/python-foundations/data/mars_weather_2024.csv")
    print("Done!")
