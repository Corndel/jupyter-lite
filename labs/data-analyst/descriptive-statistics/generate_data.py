"""Generate hospital emergency department data for the Descriptive Statistics lab."""
import csv
import math
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

NUM_PATIENTS = 5000

# --- Helpers ---

TRIAGE_WEIGHTS = [0.02, 0.15, 0.40, 0.30, 0.13]  # categories 1-5
AGE_GROUPS = ["0-17", "18-34", "35-54", "55-74", "75+"]
AGE_WEIGHTS = [0.12, 0.25, 0.25, 0.22, 0.16]

COMPLAINTS = [
    "chest_pain", "fracture", "abdominal_pain", "respiratory",
    "mental_health", "laceration", "head_injury", "allergic_reaction",
    "back_pain", "other",
]
COMPLAINT_WEIGHTS = [0.12, 0.08, 0.14, 0.11, 0.07, 0.09, 0.06, 0.04, 0.13, 0.16]

ARRIVAL_MODES = ["ambulance", "walk_in", "transfer"]
ARRIVAL_MODE_WEIGHTS = [0.30, 0.60, 0.10]

OUTCOMES = ["discharged", "admitted", "left_without_treatment", "transferred"]
OUTCOME_WEIGHTS = [0.65, 0.25, 0.08, 0.02]

# Monthly arrival multipliers (winter months = more arrivals)
MONTH_MULTIPLIERS = {
    1: 1.20, 2: 1.18, 3: 1.05, 4: 0.95, 5: 0.90, 6: 0.88,
    7: 0.85, 8: 0.87, 9: 0.92, 10: 0.98, 11: 1.08, 12: 1.15,
}

# Hourly weights: lower at night (22:00-06:00)
HOUR_WEIGHTS = [
    0.3, 0.2, 0.15, 0.12, 0.12, 0.15,   # 00-05
    0.3, 0.5, 0.8, 1.0, 1.1, 1.2,        # 06-11
    1.1, 1.0, 0.95, 0.9, 0.85, 0.9,      # 12-17
    1.0, 0.95, 0.8, 0.6, 0.45, 0.35,     # 18-23
]


def lognormal(mean, sigma):
    """Sample from a lognormal distribution using stdlib random."""
    return math.exp(random.gauss(mean, sigma))


def weighted_choice(options, weights):
    return random.choices(options, weights=weights, k=1)[0]


def generate_arrival_times(n):
    """Generate n arrival datetimes across 2024, respecting seasonal and hourly patterns."""
    start = datetime(2024, 1, 1)
    end = datetime(2024, 12, 31, 23, 59)

    arrivals = []
    attempts = 0
    max_attempts = n * 20

    while len(arrivals) < n and attempts < max_attempts:
        attempts += 1
        days_offset = random.randint(0, 365)
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        dt = start + timedelta(days=days_offset, hours=hour, minutes=minute)

        if dt > end:
            continue

        month_weight = MONTH_MULTIPLIERS[dt.month]
        hour_weight = HOUR_WEIGHTS[dt.hour]

        combined = month_weight * hour_weight
        max_possible = 1.20 * 1.2
        if random.random() < combined / max_possible:
            arrivals.append(dt)

    arrivals.sort()
    return arrivals


def generate_ed_arrivals():
    """Generate ed_arrivals.csv."""
    arrivals = generate_arrival_times(NUM_PATIENTS)

    rows = []
    for i, arrival_dt in enumerate(arrivals):
        patient_id = f"PAT-{i + 1:05d}"
        triage = weighted_choice([1, 2, 3, 4, 5], TRIAGE_WEIGHTS)
        age_group = weighted_choice(AGE_GROUPS, AGE_WEIGHTS)
        complaint = weighted_choice(COMPLAINTS, COMPLAINT_WEIGHTS)
        mode = weighted_choice(ARRIVAL_MODES, ARRIVAL_MODE_WEIGHTS)

        rows.append({
            "patient_id": patient_id,
            "arrival_time": arrival_dt.strftime("%Y-%m-%d %H:%M"),
            "triage_category": triage,
            "age_group": age_group,
            "presenting_complaint": complaint,
            "arrival_mode": mode,
        })

    filepath = DATA_DIR / "ed_arrivals.csv"
    fieldnames = ["patient_id", "arrival_time", "triage_category",
                  "age_group", "presenting_complaint", "arrival_mode"]
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Wrote {len(rows)} rows to {filepath}")
    return rows


def generate_ed_wait_times(arrival_rows):
    """Generate ed_wait_times.csv using patient_ids from arrivals."""
    rows = []
    null_count = 0

    for ar in arrival_rows:
        patient_id = ar["patient_id"]
        triage = ar["triage_category"]

        # Wait to triage: right-skewed, median ~15 min
        wait_triage = max(1, int(lognormal(mean=2.7, sigma=0.5)))
        if wait_triage > 90:
            wait_triage = random.randint(60, 90)

        # Wait to treatment: depends on triage category
        if triage in (1, 2):
            wait_treatment = max(1, int(lognormal(mean=2.3, sigma=0.5)))
            if wait_treatment > 60:
                wait_treatment = random.randint(20, 60)
        else:
            wait_treatment = max(5, int(lognormal(mean=3.8, sigma=0.6)))
            if wait_treatment > 300:
                wait_treatment = random.randint(180, 300)

        # Treatment time
        treatment_time = max(10, int(lognormal(mean=4.2, sigma=0.5)))
        if treatment_time > 480:
            treatment_time = random.randint(240, 480)

        total_time = wait_triage + wait_treatment + treatment_time
        if total_time > 720:
            total_time = random.randint(500, 720)

        outcome = weighted_choice(OUTCOMES, OUTCOME_WEIGHTS)

        row = {
            "patient_id": patient_id,
            "wait_to_triage_min": wait_triage,
            "wait_to_treatment_min": wait_treatment,
            "total_time_in_ed_min": total_time,
            "outcome": outcome,
        }

        # ~5% nulls in wait columns
        for field in ["wait_to_triage_min", "wait_to_treatment_min", "total_time_in_ed_min"]:
            if random.random() < 0.05:
                row[field] = ""
                null_count += 1

        rows.append(row)

    filepath = DATA_DIR / "ed_wait_times.csv"
    fieldnames = ["patient_id", "wait_to_triage_min", "wait_to_treatment_min",
                  "total_time_in_ed_min", "outcome"]
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Wrote {len(rows)} rows to {filepath} ({null_count} null values)")


def generate_ed_staff_shifts():
    """Generate ed_staff_shifts.csv: 2 shifts per day for 365 days."""
    rows = []
    start = datetime(2024, 1, 1)

    for day_offset in range(365):
        dt = start + timedelta(days=day_offset)
        date_str = dt.strftime("%Y-%m-%d")
        is_weekend = dt.weekday() >= 5

        for shift in ["day", "night"]:
            if is_weekend:
                doctors = random.randint(3, 5)
                nurses = random.randint(8, 14)
            else:
                doctors = random.randint(4, 8)
                nurses = random.randint(12, 20)

            if shift == "night":
                doctors = max(3, doctors - random.randint(0, 2))
                nurses = max(8, nurses - random.randint(0, 4))

            rows.append({
                "date": date_str,
                "shift": shift,
                "doctors_on_duty": doctors,
                "nurses_on_duty": nurses,
            })

    filepath = DATA_DIR / "ed_staff_shifts.csv"
    fieldnames = ["date", "shift", "doctors_on_duty", "nurses_on_duty"]
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Wrote {len(rows)} rows to {filepath}")


if __name__ == "__main__":
    print("Generating Descriptive Statistics lab data...")
    arrival_rows = generate_ed_arrivals()
    generate_ed_wait_times(arrival_rows)
    generate_ed_staff_shifts()
    print("Done!")
