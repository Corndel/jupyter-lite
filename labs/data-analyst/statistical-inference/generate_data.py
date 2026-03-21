"""Generate pharmaceutical clinical trial data for the Statistical Inference lab."""
import csv
import random
from pathlib import Path

import numpy as np

random.seed(42)
np.random.seed(42)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

NUM_PATIENTS = 2000

SITES = list(range(1, 9))

ADVERSE_EVENT_TYPES = ["headache", "nausea", "fatigue", "dizziness", "rash", "insomnia"]


def generate_trial_patients(filepath):
    """Generate ~2000 patient records for a multi-site Phase III trial."""
    fieldnames = [
        "patient_id", "age", "sex", "weight_kg", "group", "site_id",
    ]

    rows = []
    for i in range(1, NUM_PATIENTS + 1):
        sex = random.choice(["M"] * 48 + ["F"] * 52)
        group = random.choice(["treatment", "control"])

        age_raw = np.random.normal(55, 12)
        age = int(np.clip(age_raw, 18, 85))

        weight_raw = np.random.normal(78, 15)
        weight_kg = round(float(np.clip(weight_raw, 45, 150)), 1)

        rows.append({
            "patient_id": f"PT-{i:04d}",
            "age": age,
            "sex": sex,
            "weight_kg": weight_kg,
            "group": group,
            "site_id": random.choice(SITES),
        })

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    treatment_count = sum(1 for r in rows if r["group"] == "treatment")
    control_count = sum(1 for r in rows if r["group"] == "control")
    print(f"  Wrote {len(rows)} rows to {filepath}")
    print(f"    Treatment: {treatment_count}, Control: {control_count}")
    return rows


def generate_treatment_outcomes(filepath, patients):
    """Generate outcome scores for each patient over 12 weeks."""
    fieldnames = [
        "patient_id", "baseline_score", "week_4_score", "week_8_score",
        "week_12_score", "final_outcome",
    ]

    rows = []
    for p in patients:
        baseline = float(np.clip(np.random.normal(50, 10), 15, 85))

        if p["group"] == "treatment":
            # Effect size ~0.4 SD = 4 points over 12 weeks
            week_4_change = np.random.normal(-1.3, 3)
            week_8_change = np.random.normal(-2.7, 3)
            week_12_change = np.random.normal(-4.0, 3)
        else:
            # Placebo effect ~0.1 SD = 1 point improvement
            week_4_change = np.random.normal(-0.3, 3)
            week_8_change = np.random.normal(-0.7, 3)
            week_12_change = np.random.normal(-1.0, 3)

        week_4 = round(baseline + week_4_change, 1)
        week_8 = round(baseline + week_8_change, 1)
        week_12 = round(baseline + week_12_change, 1)
        baseline = round(baseline, 1)

        score_change = week_12 - baseline
        if score_change < -5:
            outcome = "improved"
        elif score_change > 3:
            outcome = "worsened"
        else:
            outcome = "stable"

        rows.append({
            "patient_id": p["patient_id"],
            "baseline_score": baseline,
            "week_4_score": week_4,
            "week_8_score": week_8,
            "week_12_score": week_12,
            "final_outcome": outcome,
        })

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    outcomes = {}
    for r in rows:
        outcomes[r["final_outcome"]] = outcomes.get(r["final_outcome"], 0) + 1
    print(f"  Wrote {len(rows)} rows to {filepath}")
    print(f"    Outcomes: {outcomes}")


def generate_adverse_events(filepath, patients):
    """Generate ~300 adverse event records, weighted towards treatment group."""
    fieldnames = [
        "patient_id", "event_type", "severity", "week_reported",
    ]

    # Split patients by group
    treatment_ids = [p["patient_id"] for p in patients if p["group"] == "treatment"]
    control_ids = [p["patient_id"] for p in patients if p["group"] == "control"]

    target_total = 300
    treatment_count = int(target_total * 0.6)
    control_count = target_total - treatment_count

    severity_pool = ["mild"] * 60 + ["moderate"] * 30 + ["severe"] * 10

    rows = []
    for _ in range(treatment_count):
        severity = random.choice(severity_pool)
        # ~5% null in severity
        if random.random() < 0.05:
            severity = ""
        rows.append({
            "patient_id": random.choice(treatment_ids),
            "event_type": random.choice(ADVERSE_EVENT_TYPES),
            "severity": severity,
            "week_reported": random.randint(1, 12),
        })

    for _ in range(control_count):
        severity = random.choice(severity_pool)
        if random.random() < 0.05:
            severity = ""
        rows.append({
            "patient_id": random.choice(control_ids),
            "event_type": random.choice(ADVERSE_EVENT_TYPES),
            "severity": severity,
            "week_reported": random.randint(1, 12),
        })

    # Shuffle so treatment and control rows are interleaved
    random.shuffle(rows)

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    null_count = sum(1 for r in rows if r["severity"] == "")
    print(f"  Wrote {len(rows)} rows to {filepath}")
    print(f"    Null severity values: {null_count}")


if __name__ == "__main__":
    print("Generating Statistical Inference lab data...")
    patients = generate_trial_patients(DATA_DIR / "trial_patients.csv")
    generate_treatment_outcomes(DATA_DIR / "treatment_outcomes.csv", patients)
    generate_adverse_events(DATA_DIR / "adverse_events.csv", patients)
    print("Done!")
