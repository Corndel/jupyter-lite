"""
Data generation script for the Data Modelling module.
Generates flat_patient_visits.csv and nhs_trust.sqlite with realistic NHS data.
"""

import csv
import sqlite3
import random
import os
from datetime import datetime, timedelta

random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ── Reference data ──────────────────────────────────────────────────────────

FIRST_NAMES_MALE = [
    "James", "John", "Robert", "David", "Michael", "William", "Richard",
    "Thomas", "Charles", "Daniel", "Matthew", "Andrew", "Christopher",
    "Joseph", "Mark", "Paul", "Steven", "Edward", "Brian", "George",
    "Peter", "Ian", "Stuart", "Graham", "Colin", "Alan", "Keith",
    "Derek", "Trevor", "Barry", "Nigel", "Clive", "Roger", "Simon",
    "Philip", "Stephen", "Martin", "Kevin", "Gary", "Timothy",
    "Mohammed", "Raj", "Tariq", "Kwame", "Oluwaseun", "Chen", "Wei",
    "Sanjay", "Amit", "Vikram"
]

FIRST_NAMES_FEMALE = [
    "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara",
    "Susan", "Jessica", "Sarah", "Karen", "Margaret", "Lisa", "Nancy",
    "Dorothy", "Sandra", "Ashley", "Emily", "Donna", "Carol", "Ruth",
    "Helen", "Sharon", "Deborah", "Laura", "Cynthia", "Janet", "Fiona",
    "Moira", "Eileen", "Brenda", "Wendy", "Tracey", "Nicola", "Joanne",
    "Fatima", "Aisha", "Priya", "Lakshmi", "Mei", "Yuki", "Amara",
    "Ngozi", "Abigail", "Grace", "Olivia", "Charlotte", "Sophia",
    "Isabella", "Mia", "Amelia"
]

SURNAMES = [
    "Smith", "Jones", "Williams", "Taylor", "Brown", "Davies", "Evans",
    "Wilson", "Thomas", "Roberts", "Johnson", "Lewis", "Walker", "Robinson",
    "Wood", "Thompson", "White", "Watson", "Jackson", "Wright", "Green",
    "Harris", "Cooper", "King", "Lee", "Martin", "Clarke", "James",
    "Morgan", "Hughes", "Edwards", "Hill", "Moore", "Clark", "Harrison",
    "Scott", "Young", "Morris", "Hall", "Ward", "Turner", "Carter",
    "Phillips", "Mitchell", "Patel", "Khan", "Singh", "Ahmed", "Ali",
    "Hussain", "Begum", "Chowdhury", "Okonkwo", "Adeyemi", "Chen",
    "Wang", "Zhang", "Kowalski", "Novak", "Murphy", "O'Brien"
]

STREET_NAMES = [
    "High Street", "Church Lane", "Station Road", "Mill Lane",
    "Park Avenue", "Victoria Road", "Queen Street", "King Street",
    "The Green", "Manor Road", "Elm Close", "Oak Drive", "Cedar Way",
    "Birch Lane", "Willow Crescent", "Maple Road", "Ash Grove",
    "Beech Avenue", "Rosemary Lane", "Lavender Close", "Primrose Way",
    "Hawthorn Drive", "Chestnut Road", "Poplar Avenue", "Sycamore Close"
]

TOWNS = [
    "Millbrook", "Ashford", "Westbury", "Northfield", "Eastham",
    "Southgate", "Riverside", "Greendale", "Brookside", "Hillcrest",
    "Woodlands", "Lakeside", "Meadowbank", "Stoneleigh", "Fairfield"
]

POSTCODES_AREA = ["CB", "PE", "IP", "NR", "CO"]


def random_postcode():
    area = random.choice(POSTCODES_AREA)
    district = random.randint(1, 28)
    sector = random.randint(1, 9)
    unit = random.choice("ABDEFGHJKLMNPQRSTUVWXYZ") + random.choice("ABDEFGHJKLMNPQRSTUVWXYZ")
    return f"{area}{district} {sector}{unit}"


def random_address():
    number = random.randint(1, 150)
    street = random.choice(STREET_NAMES)
    town = random.choice(TOWNS)
    return f"{number} {street}, {town}", random_postcode()


def random_name():
    if random.random() < 0.5:
        first = random.choice(FIRST_NAMES_MALE)
    else:
        first = random.choice(FIRST_NAMES_FEMALE)
    return f"{first} {random.choice(SURNAMES)}"


def random_dob(min_age=18, max_age=95):
    today = datetime(2025, 1, 1)
    age_days = random.randint(min_age * 365, max_age * 365)
    return (today - timedelta(days=age_days)).strftime("%Y-%m-%d")


def random_nhs_number():
    """Generate a realistic-looking 10-digit NHS number."""
    return "".join([str(random.randint(0, 9)) for _ in range(10)])


def random_phone():
    return f"01{random.randint(200,999)} {random.randint(100000,999999)}"


# ── GP Practices ────────────────────────────────────────────────────────────

GP_PRACTICES = []
gp_names = [
    "Riverside Medical Centre", "The Willows Surgery", "Oakfield Practice",
    "St. Mary's Surgery", "Brookside Health Centre", "The Elms Medical Practice",
    "Victoria Park Surgery", "Greendale Medical Centre", "Ashford Family Practice",
    "Hillcrest Surgery", "Meadowbank Medical Centre", "Cedar House Surgery",
    "The Pines Practice", "Lakeside Medical Centre", "Manor Road Surgery",
    "Church Lane Surgery", "Beechwood Medical Centre", "Station Road Practice",
    "Primrose Hill Surgery", "Fairfield Health Centre"
]

for i, name in enumerate(gp_names, start=1):
    addr, pc = random_address()
    GP_PRACTICES.append({
        "gp_practice_id": i,
        "name": name,
        "address": addr,
        "postcode": pc,
        "phone": random_phone()
    })

# ── Departments ─────────────────────────────────────────────────────────────

DEPARTMENTS = [
    {"department_id": 1,  "name": "A&E",                "floor": 0, "phone": random_phone()},
    {"department_id": 2,  "name": "Cardiology",          "floor": 2, "phone": random_phone()},
    {"department_id": 3,  "name": "Orthopaedics",        "floor": 3, "phone": random_phone()},
    {"department_id": 4,  "name": "General Medicine",    "floor": 1, "phone": random_phone()},
    {"department_id": 5,  "name": "Paediatrics",         "floor": 2, "phone": random_phone()},
    {"department_id": 6,  "name": "Obstetrics",          "floor": 4, "phone": random_phone()},
    {"department_id": 7,  "name": "Neurology",           "floor": 3, "phone": random_phone()},
    {"department_id": 8,  "name": "Oncology",            "floor": 4, "phone": random_phone()},
    {"department_id": 9,  "name": "Dermatology",         "floor": 1, "phone": random_phone()},
    {"department_id": 10, "name": "Respiratory Medicine", "floor": 2, "phone": random_phone()},
]

# Specialties per department
DEPT_SPECIALTIES = {
    1:  ["Emergency Medicine"],
    2:  ["Cardiology", "Cardiac Surgery"],
    3:  ["Orthopaedic Surgery", "Trauma Surgery"],
    4:  ["General Medicine", "Gastroenterology"],
    5:  ["Paediatrics", "Neonatal Medicine"],
    6:  ["Obstetrics", "Gynaecology"],
    7:  ["Neurology", "Neurosurgery"],
    8:  ["Medical Oncology", "Clinical Oncology"],
    9:  ["Dermatology"],
    10: ["Respiratory Medicine", "Thoracic Surgery"],
}

# ── Doctors ─────────────────────────────────────────────────────────────────

DOCTORS = []
doctor_id = 1
for dept in DEPARTMENTS:
    n_doctors = random.randint(2, 5)
    for _ in range(n_doctors):
        specialty = random.choice(DEPT_SPECIALTIES[dept["department_id"]])
        DOCTORS.append({
            "doctor_id": doctor_id,
            "name": "Dr " + random_name(),
            "specialty": specialty,
            "department_id": dept["department_id"]
        })
        doctor_id += 1

# ── Patients ────────────────────────────────────────────────────────────────

PATIENTS = []
for pid in range(1, 201):
    addr, pc = random_address()
    PATIENTS.append({
        "patient_id": pid,
        "nhs_number": random_nhs_number(),
        "name": random_name(),
        "dob": random_dob(),
        "address": addr,
        "postcode": pc,
        "gp_practice_id": random.choice(GP_PRACTICES)["gp_practice_id"]
    })

# ── Diagnoses and treatments ───────────────────────────────────────────────

DIAGNOSES = {
    1:  ["Fracture", "Laceration", "Concussion", "Sprain", "Burn", "Allergic reaction"],
    2:  ["Angina", "Atrial fibrillation", "Heart failure", "Hypertension", "Myocardial infarction"],
    3:  ["Hip fracture", "Knee osteoarthritis", "Rotator cuff tear", "Spinal stenosis", "Carpal tunnel syndrome"],
    4:  ["Type 2 diabetes", "COPD exacerbation", "Pneumonia", "Gastritis", "Anaemia"],
    5:  ["Asthma", "Bronchiolitis", "Ear infection", "Tonsillitis", "Appendicitis"],
    6:  ["Pre-eclampsia", "Gestational diabetes", "Ectopic pregnancy", "Placenta praevia"],
    7:  ["Migraine", "Epilepsy", "Multiple sclerosis", "Stroke", "Parkinson's disease"],
    8:  ["Breast cancer", "Lung cancer", "Colorectal cancer", "Prostate cancer", "Lymphoma"],
    9:  ["Eczema", "Psoriasis", "Melanoma", "Acne", "Dermatitis"],
    10: ["COPD", "Asthma", "Pulmonary fibrosis", "Pneumonia", "Pleural effusion"],
}

TREATMENTS = {
    1:  ["Suturing", "Plaster cast", "Pain management", "IV fluids", "Observation"],
    2:  ["Beta-blockers", "ACE inhibitors", "Anticoagulants", "Stenting", "Pacemaker insertion"],
    3:  ["Joint replacement", "Physiotherapy", "Arthroscopy", "Spinal fusion", "Corticosteroid injection"],
    4:  ["Insulin therapy", "Antibiotics", "Nebuliser", "PPI medication", "Iron supplements"],
    5:  ["Inhaler therapy", "Antibiotics", "Tonsillectomy", "Appendectomy", "Bronchodilators"],
    6:  ["Magnesium sulphate", "Insulin therapy", "Surgical intervention", "Bed rest", "Monitoring"],
    7:  ["Triptans", "Anti-epileptics", "Immunotherapy", "Thrombolysis", "Levodopa"],
    8:  ["Chemotherapy", "Radiotherapy", "Surgery", "Immunotherapy", "Hormone therapy"],
    9:  ["Topical corticosteroids", "Phototherapy", "Excision", "Retinoids", "Emollients"],
    10: ["Bronchodilators", "Inhaler therapy", "Oxygen therapy", "Antibiotics", "Thoracentesis"],
}

# ── Visits (general outpatient/inpatient) ───────────────────────────────────

VISITS = []
for vid in range(1, 2001):
    patient = random.choice(PATIENTS)
    dept = random.choice(DEPARTMENTS)
    dept_id = dept["department_id"]
    dept_doctors = [d for d in DOCTORS if d["department_id"] == dept_id]
    doctor = random.choice(dept_doctors)
    visit_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 364))
    diagnosis = random.choice(DIAGNOSES[dept_id])
    treatment = random.choice(TREATMENTS[dept_id])
    follow_up = (visit_date + timedelta(days=random.randint(7, 90))).strftime("%Y-%m-%d") if random.random() < 0.6 else None

    VISITS.append({
        "visit_id": vid,
        "patient_id": patient["patient_id"],
        "doctor_id": doctor["doctor_id"],
        "department_id": dept_id,
        "visit_date": visit_date.strftime("%Y-%m-%d"),
        "diagnosis": diagnosis,
        "treatment": treatment,
        "follow_up_date": follow_up
    })

# ── A&E visits ──────────────────────────────────────────────────────────────

TRIAGE_CATEGORIES = [1, 2, 3, 4, 5]  # 1=immediate, 5=non-urgent
ADMISSION_TYPES = ["Walk-in", "Ambulance", "GP Referral", "Transfer", "Police"]
OUTCOMES = ["Discharged", "Admitted", "Transferred", "Left before treatment", "Deceased"]

AE_VISITS = []
for ae_id in range(1, 1001):
    patient = random.choice(PATIENTS)
    triage = random.choices(TRIAGE_CATEGORIES, weights=[5, 15, 40, 30, 10])[0]
    # Wait time correlates inversely with triage severity
    base_wait = {1: 0, 2: 10, 3: 45, 4: 90, 5: 150}[triage]
    wait_mins = max(0, base_wait + random.randint(-10, 60))
    treatment_mins = random.randint(15, 240)
    admission_type = random.choices(
        ADMISSION_TYPES,
        weights=[40, 25, 20, 10, 5]
    )[0]
    outcome = random.choices(
        OUTCOMES,
        weights=[50, 30, 10, 8, 2]
    )[0]

    arrival = datetime(2024, 1, 1) + timedelta(
        days=random.randint(0, 364),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )
    discharge = arrival + timedelta(minutes=wait_mins + treatment_mins + random.randint(10, 60))

    AE_VISITS.append({
        "ae_visit_id": ae_id,
        "patient_id": patient["patient_id"],
        "arrival_time": arrival.strftime("%Y-%m-%d %H:%M"),
        "triage_category": triage,
        "wait_minutes": wait_mins,
        "treatment_minutes": treatment_mins,
        "department_id": 1,  # A&E
        "admission_type": admission_type,
        "outcome": outcome,
        "discharge_time": discharge.strftime("%Y-%m-%d %H:%M")
    })


# ── Generate flat_patient_visits.csv ────────────────────────────────────────

print("Generating flat_patient_visits.csv...")

# Create deliberate inconsistencies for update anomaly demonstration
# Some GP practices will have slightly different addresses in different rows
gp_address_variants = {}
for gp in GP_PRACTICES:
    gp_id = gp["gp_practice_id"]
    correct = gp["address"]
    # For ~5 practices, create a variant address
    if gp_id in [1, 4, 7, 12, 15]:
        # Slightly different address (typo, abbreviation, etc.)
        parts = correct.split(", ")
        if len(parts) == 2:
            variant = parts[0].replace("Road", "Rd").replace("Street", "St").replace("Lane", "Ln").replace("Avenue", "Ave") + ", " + parts[1]
            if variant == correct:
                variant = str(random.randint(1, 150)) + " " + parts[0].split(" ", 1)[1] + ", " + parts[1]
        else:
            variant = correct + " (Suite 2)"
        gp_address_variants[gp_id] = (correct, variant)
    else:
        gp_address_variants[gp_id] = (correct, correct)

# Some departments listed on different floors
dept_floor_variants = {}
for dept in DEPARTMENTS:
    did = dept["department_id"]
    correct_floor = dept["floor"]
    if did in [3, 5, 9]:  # Ortho, Paediatrics, Dermatology
        dept_floor_variants[did] = (correct_floor, correct_floor + 1)
    else:
        dept_floor_variants[did] = (correct_floor, correct_floor)

flat_rows = []
for _ in range(500):
    patient = random.choice(PATIENTS)
    gp = next(g for g in GP_PRACTICES if g["gp_practice_id"] == patient["gp_practice_id"])
    dept = random.choice(DEPARTMENTS)
    dept_id = dept["department_id"]
    dept_doctors = [d for d in DOCTORS if d["department_id"] == dept_id]
    doctor = random.choice(dept_doctors)
    visit_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 364))
    diagnosis = random.choice(DIAGNOSES[dept_id])
    treatment = random.choice(TREATMENTS[dept_id])
    follow_up = (visit_date + timedelta(days=random.randint(7, 90))).strftime("%Y-%m-%d") if random.random() < 0.6 else ""

    # Deliberately pick the variant address ~30% of the time
    gp_addr_correct, gp_addr_variant = gp_address_variants[gp["gp_practice_id"]]
    gp_address_used = gp_addr_variant if random.random() < 0.3 else gp_addr_correct

    # Deliberately pick the wrong floor ~20% of the time
    floor_correct, floor_variant = dept_floor_variants[dept_id]
    floor_used = floor_variant if random.random() < 0.2 else floor_correct

    flat_rows.append({
        "patient_id": patient["patient_id"],
        "patient_name": patient["name"],
        "patient_dob": patient["dob"],
        "patient_address": patient["address"],
        "patient_postcode": patient["postcode"],
        "gp_practice_id": gp["gp_practice_id"],
        "gp_practice_name": gp["name"],
        "gp_address": gp_address_used,
        "gp_postcode": gp["postcode"],
        "gp_phone": gp["phone"],
        "visit_date": visit_date.strftime("%Y-%m-%d"),
        "department": dept["name"],
        "department_floor": floor_used,
        "doctor_name": doctor["name"],
        "doctor_specialty": doctor["specialty"],
        "diagnosis": diagnosis,
        "treatment": treatment,
        "follow_up_date": follow_up
    })

csv_path = os.path.join(DATA_DIR, "flat_patient_visits.csv")
with open(csv_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=flat_rows[0].keys())
    writer.writeheader()
    writer.writerows(flat_rows)

print(f"  Written {len(flat_rows)} rows to {csv_path}")

# ── Generate nhs_trust.sqlite ──────────────────────────────────────────────

print("Generating nhs_trust.sqlite...")

db_path = os.path.join(DATA_DIR, "nhs_trust.sqlite")
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("""
CREATE TABLE gp_practices (
    gp_practice_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    postcode TEXT NOT NULL,
    phone TEXT NOT NULL
)
""")

cur.execute("""
CREATE TABLE patients (
    patient_id INTEGER PRIMARY KEY,
    nhs_number TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    dob TEXT NOT NULL,
    address TEXT NOT NULL,
    postcode TEXT NOT NULL,
    gp_practice_id INTEGER NOT NULL,
    FOREIGN KEY (gp_practice_id) REFERENCES gp_practices(gp_practice_id)
)
""")

cur.execute("""
CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    floor INTEGER NOT NULL,
    phone TEXT NOT NULL
)
""")

cur.execute("""
CREATE TABLE doctors (
    doctor_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    specialty TEXT NOT NULL,
    department_id INTEGER NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
)
""")

cur.execute("""
CREATE TABLE visits (
    visit_id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    department_id INTEGER NOT NULL,
    visit_date TEXT NOT NULL,
    diagnosis TEXT NOT NULL,
    treatment TEXT NOT NULL,
    follow_up_date TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
)
""")

cur.execute("""
CREATE TABLE ae_visits (
    ae_visit_id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    arrival_time TEXT NOT NULL,
    triage_category INTEGER NOT NULL,
    wait_minutes INTEGER NOT NULL,
    treatment_minutes INTEGER NOT NULL,
    department_id INTEGER NOT NULL,
    admission_type TEXT NOT NULL,
    outcome TEXT NOT NULL,
    discharge_time TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
)
""")

# Insert GP practices
for gp in GP_PRACTICES:
    cur.execute(
        "INSERT INTO gp_practices VALUES (?, ?, ?, ?, ?)",
        (gp["gp_practice_id"], gp["name"], gp["address"], gp["postcode"], gp["phone"])
    )

# Insert patients
for p in PATIENTS:
    cur.execute(
        "INSERT INTO patients VALUES (?, ?, ?, ?, ?, ?, ?)",
        (p["patient_id"], p["nhs_number"], p["name"], p["dob"],
         p["address"], p["postcode"], p["gp_practice_id"])
    )

# Insert departments
for d in DEPARTMENTS:
    cur.execute(
        "INSERT INTO departments VALUES (?, ?, ?, ?)",
        (d["department_id"], d["name"], d["floor"], d["phone"])
    )

# Insert doctors
for doc in DOCTORS:
    cur.execute(
        "INSERT INTO doctors VALUES (?, ?, ?, ?)",
        (doc["doctor_id"], doc["name"], doc["specialty"], doc["department_id"])
    )

# Insert visits
for v in VISITS:
    cur.execute(
        "INSERT INTO visits VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (v["visit_id"], v["patient_id"], v["doctor_id"], v["department_id"],
         v["visit_date"], v["diagnosis"], v["treatment"], v["follow_up_date"])
    )

# Insert A&E visits
for ae in AE_VISITS:
    cur.execute(
        "INSERT INTO ae_visits VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (ae["ae_visit_id"], ae["patient_id"], ae["arrival_time"],
         ae["triage_category"], ae["wait_minutes"], ae["treatment_minutes"],
         ae["department_id"], ae["admission_type"], ae["outcome"],
         ae["discharge_time"])
    )

conn.commit()
conn.close()

print(f"  Written database to {db_path}")
print(f"  Tables: gp_practices({len(GP_PRACTICES)}), patients({len(PATIENTS)}), "
      f"departments({len(DEPARTMENTS)}), doctors({len(DOCTORS)}), "
      f"visits({len(VISITS)}), ae_visits({len(AE_VISITS)})")
print("Done!")
