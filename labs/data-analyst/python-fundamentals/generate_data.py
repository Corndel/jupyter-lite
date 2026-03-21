"""Generate satellite constellation telemetry data for the Python Fundamentals lab."""
import csv
import json
import random
import math
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

SATELLITE_NAMES = [
    "Sentinel-1", "Sentinel-2", "Sentinel-3", "Sentinel-4", "Sentinel-5",
    "Horizon-1", "Horizon-2", "Horizon-3", "Horizon-4", "Horizon-5",
    "Polar-1", "Polar-2", "Polar-3", "Polar-4", "Polar-5",
    "Equator-1", "Equator-2", "Equator-3", "Equator-4", "Equator-5",
]

ORBIT_TYPES = ["LEO", "MEO", "GEO", "SSO"]


def generate_telemetry_csv(filepath, num_rows=500):
    """Generate ~500 rows of satellite telemetry readings."""
    fieldnames = [
        "reading_id", "satellite_id", "timestamp",
        "orbit_altitude_km", "velocity_kms", "battery_pct",
        "signal_strength_dbm", "temperature_c", "status",
    ]

    statuses = ["active"] * 80 + ["degraded"] * 15 + ["offline"] * 5

    start_time = datetime(2025, 1, 1, 0, 0, 0)
    rows = []

    for i in range(1, num_rows + 1):
        sat_id = f"SAT-{random.randint(1, 20):03d}"
        ts = start_time + timedelta(hours=random.randint(0, 720))

        row = {
            "reading_id": i,
            "satellite_id": sat_id,
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "orbit_altitude_km": round(random.uniform(200, 36000), 1),
            "velocity_kms": round(random.uniform(3.0, 7.8), 2),
            "battery_pct": round(random.uniform(10, 100), 1),
            "signal_strength_dbm": round(random.uniform(-120, -40), 1),
            "temperature_c": round(random.uniform(-40, 80), 1),
            "status": random.choice(statuses),
        }

        # Sprinkle nulls: ~5% chance per nullable field
        for field in ["battery_pct", "signal_strength_dbm", "temperature_c"]:
            if random.random() < 0.05:
                row[field] = ""

        rows.append(row)

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    null_count = sum(1 for r in rows for f in ["battery_pct", "signal_strength_dbm", "temperature_c"] if r[f] == "")
    print(f"  Wrote {len(rows)} rows to {filepath} ({null_count} null values)")


def generate_constellation_json(filepath):
    """Generate nested JSON with 20 satellites and recent readings."""
    constellation = {
        "constellation_name": "Global Earth Observation Network",
        "operator": "International Space Monitoring Agency",
        "last_updated": "2025-01-31T12:00:00Z",
        "satellites": [],
    }

    launch_base = datetime(2020, 3, 15)
    reading_base = datetime(2025, 1, 28, 0, 0, 0)

    for idx, name in enumerate(SATELLITE_NAMES):
        sat_id = f"SAT-{idx + 1:03d}"
        orbit = random.choice(ORBIT_TYPES)
        launch_date = (launch_base + timedelta(days=random.randint(0, 1500))).strftime("%Y-%m-%d")

        # Generate 5 recent readings per satellite
        readings = []
        for r in range(5):
            ts = reading_base + timedelta(hours=r * 6)
            readings.append({
                "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "battery_pct": round(random.uniform(20, 100), 1),
                "signal_strength_dbm": round(random.uniform(-110, -50), 1),
                "temperature_c": round(random.uniform(-30, 70), 1),
                "status": random.choice(["active", "active", "active", "degraded"]),
            })

        satellite = {
            "satellite_id": sat_id,
            "name": name,
            "orbit_type": orbit,
            "launch_date": launch_date,
            "altitude_km": round(random.uniform(300, 35786), 0),
            "readings": readings,
        }
        constellation["satellites"].append(satellite)

    with open(filepath, "w") as f:
        json.dump(constellation, f, indent=2)

    print(f"  Wrote {len(constellation['satellites'])} satellites to {filepath}")


if __name__ == "__main__":
    print("Generating Python Fundamentals lab data...")
    generate_telemetry_csv(DATA_DIR / "satellite_telemetry.csv")
    generate_constellation_json(DATA_DIR / "constellation_status.json")
    print("Done!")
