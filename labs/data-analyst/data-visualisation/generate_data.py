"""Generate plausible climate and energy data for the data-visualisation lab."""

import csv
import math
import os
import random

random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

COUNTRIES = [
    "UK", "Germany", "France", "USA", "China",
    "India", "Brazil", "Australia", "Japan", "South Africa",
]

SOURCES = ["coal", "gas", "nuclear", "solar", "wind", "hydro"]

# ---------------------------------------------------------------------------
# 1. Global temperature anomaly (1850-2025)
# ---------------------------------------------------------------------------

def generate_temperature():
    rows = []
    for year in range(1850, 2026):
        t = year - 1850
        # Flat baseline with slight rise until ~1970, then accelerating
        if year <= 1970:
            trend = 0.0 + 0.001 * t
        else:
            years_since_1970 = year - 1970
            base = 0.001 * (1970 - 1850)  # ~0.12
            # Calibrated so 2025 reaches ~1.2 C
            trend = base + 0.016 * years_since_1970 + 0.00045 * years_since_1970 ** 1.5
        noise = random.gauss(0, 0.08)
        anomaly = round(trend + noise, 3)
        rows.append({"year": year, "anomaly_c": anomaly})

    path = os.path.join(DATA_DIR, "global_temperature.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["year", "anomaly_c"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"  global_temperature.csv: {len(rows)} rows")


# ---------------------------------------------------------------------------
# 2. Energy mix by country (2000-2024)
# ---------------------------------------------------------------------------

# Base generation in TWh for year 2000, per country per source
ENERGY_BASE = {
    "UK":           {"coal": 110, "gas": 140, "nuclear": 80, "solar": 0.1, "wind": 1,   "hydro": 5},
    "Germany":      {"coal": 150, "gas": 80,  "nuclear": 170,"solar": 0.1, "wind": 9,   "hydro": 20},
    "France":       {"coal": 30,  "gas": 20,  "nuclear": 400,"solar": 0.1, "wind": 0.5, "hydro": 70},
    "USA":          {"coal": 1970,"gas": 600, "nuclear": 750,"solar": 0.5, "wind": 6,   "hydro": 270},
    "China":        {"coal": 1100,"gas": 30,  "nuclear": 17, "solar": 0.1, "wind": 1,   "hydro": 220},
    "India":        {"coal": 480, "gas": 60,  "nuclear": 15, "solar": 0.1, "wind": 2,   "hydro": 75},
    "Brazil":       {"coal": 10,  "gas": 15,  "nuclear": 6,  "solar": 0.1, "wind": 0.2, "hydro": 300},
    "Australia":    {"coal": 150, "gas": 30,  "nuclear": 0,  "solar": 0.1, "wind": 1,   "hydro": 16},
    "Japan":        {"coal": 250, "gas": 250, "nuclear": 300,"solar": 0.2, "wind": 0.5, "hydro": 85},
    "South Africa": {"coal": 200, "gas": 2,   "nuclear": 12, "solar": 0.1, "wind": 0.1, "hydro": 3},
}

# Annual growth rates (compounding) — negative means decline
ENERGY_GROWTH = {
    "UK":           {"coal": -0.12, "gas": 0.01, "nuclear": -0.01, "solar": 0.35, "wind": 0.18, "hydro": 0.005},
    "Germany":      {"coal": -0.06, "gas": 0.02, "nuclear": -0.08, "solar": 0.30, "wind": 0.12, "hydro": 0.005},
    "France":       {"coal": -0.08, "gas": 0.02, "nuclear": -0.005,"solar": 0.32, "wind": 0.20, "hydro": 0.003},
    "USA":          {"coal": -0.05, "gas": 0.04, "nuclear": -0.003,"solar": 0.35, "wind": 0.15, "hydro": 0.002},
    "China":        {"coal": 0.06,  "gas": 0.12, "nuclear": 0.15,  "solar": 0.45, "wind": 0.25, "hydro": 0.04},
    "India":        {"coal": 0.05,  "gas": 0.04, "nuclear": 0.06,  "solar": 0.40, "wind": 0.15, "hydro": 0.02},
    "Brazil":       {"coal": 0.01,  "gas": 0.06, "nuclear": 0.02,  "solar": 0.45, "wind": 0.30, "hydro": 0.015},
    "Australia":    {"coal": -0.04, "gas": 0.03, "nuclear": 0.0,   "solar": 0.38, "wind": 0.15, "hydro": 0.005},
    "Japan":        {"coal": -0.02, "gas": 0.01, "nuclear": -0.03, "solar": 0.30, "wind": 0.18, "hydro": 0.003},
    "South Africa": {"coal": -0.01, "gas": 0.05, "nuclear": 0.01,  "solar": 0.40, "wind": 0.25, "hydro": 0.01},
}


def generate_energy_mix():
    rows = []
    for country in COUNTRIES:
        for year in range(2000, 2025):
            t = year - 2000
            values = {}
            for source in SOURCES:
                base = ENERGY_BASE[country][source]
                rate = ENERGY_GROWTH[country][source]
                # Accelerate solar/wind growth after 2015
                if source in ("solar", "wind") and year > 2015:
                    rate *= 1.3
                val = base * ((1 + rate) ** t)
                noise = random.gauss(1.0, 0.03)
                val = max(0, val * noise)
                values[source] = round(val, 2)

            total = sum(values.values())
            for source in SOURCES:
                pct = round(100 * values[source] / total, 2) if total > 0 else 0
                rows.append({
                    "country": country,
                    "year": year,
                    "source": source,
                    "generation_twh": values[source],
                    "pct_of_total": pct,
                })

    path = os.path.join(DATA_DIR, "energy_mix_by_country.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "country", "year", "source", "generation_twh", "pct_of_total",
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"  energy_mix_by_country.csv: {len(rows)} rows")


# ---------------------------------------------------------------------------
# 3. CO2 emissions (2000-2024)
# ---------------------------------------------------------------------------

# Base emissions in Mt for 2000, and per-capita in tonnes
CO2_BASE = {
    "UK":           {"emissions_mt": 550,  "per_capita_t": 9.2},
    "Germany":      {"emissions_mt": 850,  "per_capita_t": 10.3},
    "France":       {"emissions_mt": 400,  "per_capita_t": 6.6},
    "USA":          {"emissions_mt": 5900, "per_capita_t": 20.5},
    "China":        {"emissions_mt": 3400, "per_capita_t": 2.7},
    "India":        {"emissions_mt": 1000, "per_capita_t": 1.0},
    "Brazil":       {"emissions_mt": 340,  "per_capita_t": 1.9},
    "Australia":    {"emissions_mt": 350,  "per_capita_t": 18.0},
    "Japan":        {"emissions_mt": 1200, "per_capita_t": 9.5},
    "South Africa": {"emissions_mt": 390,  "per_capita_t": 8.5},
}

CO2_GROWTH = {
    "UK":           -0.025,
    "Germany":      -0.02,
    "France":       -0.015,
    "USA":          -0.012,
    "China":        0.05,
    "India":        0.04,
    "Brazil":       0.02,
    "Australia":    -0.01,
    "Japan":        -0.01,
    "South Africa": 0.015,
}

# Approximate population growth rates for per-capita calculation
POP_GROWTH = {
    "UK": 0.005, "Germany": 0.001, "France": 0.004, "USA": 0.007,
    "China": 0.005, "India": 0.013, "Brazil": 0.009, "Australia": 0.012,
    "Japan": -0.002, "South Africa": 0.012,
}


def generate_co2():
    rows = []
    for country in COUNTRIES:
        base_mt = CO2_BASE[country]["emissions_mt"]
        base_pc = CO2_BASE[country]["per_capita_t"]
        rate = CO2_GROWTH[country]
        pop_rate = POP_GROWTH[country]

        for year in range(2000, 2025):
            t = year - 2000
            # Slow down China's growth after 2015
            effective_rate = rate
            if country == "China" and year > 2015:
                effective_rate = 0.015
            emissions = base_mt * ((1 + effective_rate) ** t)
            noise = random.gauss(1.0, 0.02)
            emissions = round(emissions * noise, 1)

            pop_factor = (1 + pop_rate) ** t
            per_capita = round(emissions / (base_mt / base_pc * pop_factor), 2)

            rows.append({
                "country": country,
                "year": year,
                "emissions_mt": emissions,
                "per_capita_t": per_capita,
            })

    path = os.path.join(DATA_DIR, "co2_emissions.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "country", "year", "emissions_mt", "per_capita_t",
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"  co2_emissions.csv: {len(rows)} rows")


# ---------------------------------------------------------------------------
# 4. Renewable capacity (2010-2024)
# ---------------------------------------------------------------------------

RENEWABLE_BASE = {
    "UK":           {"solar_gw": 0.1,  "wind_gw": 5.0,  "hydro_gw": 1.7},
    "Germany":      {"solar_gw": 17.0, "wind_gw": 27.0, "hydro_gw": 5.6},
    "France":       {"solar_gw": 1.0,  "wind_gw": 5.6,  "hydro_gw": 25.4},
    "USA":          {"solar_gw": 2.5,  "wind_gw": 40.0, "hydro_gw": 78.0},
    "China":        {"solar_gw": 0.8,  "wind_gw": 31.0, "hydro_gw": 210.0},
    "India":        {"solar_gw": 0.1,  "wind_gw": 13.0, "hydro_gw": 37.0},
    "Brazil":       {"solar_gw": 0.01, "wind_gw": 1.0,  "hydro_gw": 80.0},
    "Australia":    {"solar_gw": 1.5,  "wind_gw": 2.0,  "hydro_gw": 8.0},
    "Japan":        {"solar_gw": 3.6,  "wind_gw": 2.3,  "hydro_gw": 22.0},
    "South Africa": {"solar_gw": 0.01, "wind_gw": 0.01, "hydro_gw": 0.6},
}

RENEWABLE_GROWTH = {
    "UK":           {"solar_gw": 0.30, "wind_gw": 0.10, "hydro_gw": 0.005},
    "Germany":      {"solar_gw": 0.08, "wind_gw": 0.06, "hydro_gw": 0.003},
    "France":       {"solar_gw": 0.22, "wind_gw": 0.12, "hydro_gw": 0.002},
    "USA":          {"solar_gw": 0.25, "wind_gw": 0.10, "hydro_gw": 0.002},
    "China":        {"solar_gw": 0.35, "wind_gw": 0.15, "hydro_gw": 0.03},
    "India":        {"solar_gw": 0.45, "wind_gw": 0.10, "hydro_gw": 0.02},
    "Brazil":       {"solar_gw": 0.55, "wind_gw": 0.25, "hydro_gw": 0.01},
    "Australia":    {"solar_gw": 0.28, "wind_gw": 0.12, "hydro_gw": 0.005},
    "Japan":        {"solar_gw": 0.15, "wind_gw": 0.10, "hydro_gw": 0.002},
    "South Africa": {"solar_gw": 0.50, "wind_gw": 0.35, "hydro_gw": 0.01},
}


def generate_renewable_capacity():
    rows = []
    for country in COUNTRIES:
        for year in range(2010, 2025):
            t = year - 2010
            row = {"country": country, "year": year}
            for tech in ("solar_gw", "wind_gw", "hydro_gw"):
                base = RENEWABLE_BASE[country][tech]
                rate = RENEWABLE_GROWTH[country][tech]
                val = base * ((1 + rate) ** t)
                noise = random.gauss(1.0, 0.02)
                val = max(0, round(val * noise, 2))
                row[tech] = val
            rows.append(row)

    path = os.path.join(DATA_DIR, "renewable_capacity.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "country", "year", "solar_gw", "wind_gw", "hydro_gw",
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"  renewable_capacity.csv: {len(rows)} rows")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Generating data files...")
    generate_temperature()
    generate_energy_mix()
    generate_co2()
    generate_renewable_capacity()
    print("Done.")
