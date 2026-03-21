"""Generate the metro_transit.sqlite database for the Databases and SQL lab."""

import os
import random
import sqlite3
from datetime import date, timedelta

random.seed(42)

DB_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DB_DIR, "metro_transit.sqlite")
os.makedirs(DB_DIR, exist_ok=True)

# Remove existing database so we start fresh
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

cur.executescript("""
CREATE TABLE stations (
    station_id        INTEGER PRIMARY KEY,
    name              TEXT NOT NULL,
    line              TEXT NOT NULL,
    zone              INTEGER NOT NULL,
    opened_year       INTEGER NOT NULL,
    has_accessibility INTEGER NOT NULL
);

CREATE TABLE routes (
    route_id           INTEGER PRIMARY KEY,
    line_name          TEXT NOT NULL,
    origin_station_id  INTEGER NOT NULL REFERENCES stations(station_id),
    dest_station_id    INTEGER NOT NULL REFERENCES stations(station_id),
    distance_km        REAL NOT NULL
);

CREATE TABLE ridership (
    ridership_id     INTEGER PRIMARY KEY,
    station_id       INTEGER NOT NULL REFERENCES stations(station_id),
    date             TEXT NOT NULL,
    hour             INTEGER NOT NULL,
    passenger_count  INTEGER NOT NULL
);

CREATE TABLE incidents (
    incident_id    INTEGER PRIMARY KEY,
    station_id     INTEGER NOT NULL REFERENCES stations(station_id),
    date           TEXT NOT NULL,
    incident_type  TEXT NOT NULL,
    severity       TEXT NOT NULL,
    delay_minutes  INTEGER NOT NULL
);

CREATE TABLE staff (
    staff_id   INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    role       TEXT NOT NULL,
    station_id INTEGER REFERENCES stations(station_id),
    hire_date  TEXT NOT NULL
);
""")

# ---------------------------------------------------------------------------
# Stations (~50)
# ---------------------------------------------------------------------------

STATION_NAMES = [
    "Riverside", "Market Square", "University", "Parliament", "Harbour Front",
    "Cathedral", "Kingsway", "Greenfield", "Elm Grove", "Ashton Road",
    "Victoria Park", "Lakeside", "Mill Hill", "Oakwood", "Bridgewater",
    "Southgate", "Northfields", "Westbourne", "Eastleigh", "Thornton Heath",
    "Blackfriars", "Whitechapel", "Silver Street", "Copper Lane", "Golden Gate",
    "Newtown", "Old Town", "Highbury", "Lowlands", "Central Plaza",
    "Beacon Hill", "Waterloo", "St James", "Queen Street", "Prince Edward",
    "Moorgate", "Bankside", "Wharfside", "Docklands", "Meadowbank",
    "Stonebridge", "Ironworks", "Sandford", "Claygate", "Bracken Hill",
    "Willowbrook", "Cedar Park", "Birchwood", "Hawthorn Rise", "Foxglove Lane",
]

LINES = ["Red", "Blue", "Green", "Yellow", "Circle"]

stations = []
for i, name in enumerate(STATION_NAMES, start=1):
    line = LINES[i % len(LINES)]
    zone = random.choices([1, 2, 3, 4], weights=[20, 35, 30, 15])[0]
    opened_year = random.randint(1960, 2020)
    has_accessibility = 1 if random.random() < 0.70 else 0
    stations.append((i, name, line, zone, opened_year, has_accessibility))

cur.executemany(
    "INSERT INTO stations VALUES (?, ?, ?, ?, ?, ?)", stations
)

# ---------------------------------------------------------------------------
# Routes (~15)
# ---------------------------------------------------------------------------

routes = []
route_id = 1
for line in LINES:
    line_stations = [s for s in stations if s[2] == line]
    random.shuffle(line_stations)
    # Create 3 routes per line (some lines share stations via Circle)
    pairs_count = min(3, len(line_stations) - 1)
    for j in range(pairs_count):
        origin = line_stations[j][0]
        dest = line_stations[j + 1][0]
        distance = round(random.uniform(2.0, 18.0), 1)
        routes.append((route_id, line, origin, dest, distance))
        route_id += 1

cur.executemany(
    "INSERT INTO routes VALUES (?, ?, ?, ?, ?)", routes
)

# ---------------------------------------------------------------------------
# Ridership (~15,000 rows)
# ---------------------------------------------------------------------------

# Pick a subset of stations to generate ridership for (all of them, sampled dates)
START_DATE = date(2024, 1, 1)
END_DATE = date(2024, 12, 31)
all_dates = []
d = START_DATE
while d <= END_DATE:
    all_dates.append(d)
    d += timedelta(days=1)

# Sample ~30 dates spread across the year for variety, then pick a handful of
# hours per station-date to reach ~15k rows.
sampled_dates = sorted(random.sample(all_dates, 60))

RUSH_HOURS = {7, 8, 9, 17, 18, 19}
HOURS = list(range(5, 24))  # trains run 05:00-23:00

ridership_rows = []
ridership_id = 1

for station in stations:
    sid = station[0]
    zone = station[3]
    # Higher base ridership for central zones
    zone_factor = {1: 1.8, 2: 1.3, 3: 1.0, 4: 0.7}[zone]

    for d in sampled_dates:
        # Pick 4-6 hours per station-date
        n_hours = random.randint(4, 6)
        hours = sorted(random.sample(HOURS, n_hours))
        is_weekend = d.weekday() >= 5

        # Seasonal factor: summer higher, winter lower
        month = d.month
        if month in (6, 7, 8):
            season_factor = 1.15
        elif month in (12, 1, 2):
            season_factor = 0.85
        else:
            season_factor = 1.0

        for h in hours:
            if h in RUSH_HOURS and not is_weekend:
                base = random.randint(300, 900)
            elif is_weekend:
                base = random.randint(40, 250)
            else:
                base = random.randint(60, 350)

            count = max(1, int(base * zone_factor * season_factor))
            ridership_rows.append((ridership_id, sid, d.isoformat(), h, count))
            ridership_id += 1

cur.executemany(
    "INSERT INTO ridership VALUES (?, ?, ?, ?, ?)", ridership_rows
)

# ---------------------------------------------------------------------------
# Incidents (~500 rows)
# ---------------------------------------------------------------------------

INCIDENT_TYPES = [
    "signal_failure", "overcrowding", "medical_emergency", "security",
    "power_outage",
]
SEVERITIES = ["minor", "moderate", "major"]
SEVERITY_WEIGHTS = [50, 35, 15]

# Ensure some stations have NO incidents (for LEFT JOIN teaching).
# Exclude roughly 10 stations from incidents.
stations_with_incidents = [s[0] for s in stations]
no_incident_stations = set(random.sample(stations_with_incidents, 10))
incident_eligible = [s for s in stations_with_incidents if s not in no_incident_stations]

incident_rows = []
for incident_id in range(1, 501):
    sid = random.choice(incident_eligible)
    d = random.choice(all_dates).isoformat()
    itype = random.choice(INCIDENT_TYPES)
    severity = random.choices(SEVERITIES, weights=SEVERITY_WEIGHTS)[0]
    if severity == "minor":
        delay = random.randint(1, 10)
    elif severity == "moderate":
        delay = random.randint(10, 30)
    else:
        delay = random.randint(25, 90)
    incident_rows.append((incident_id, sid, d, itype, severity, delay))

cur.executemany(
    "INSERT INTO incidents VALUES (?, ?, ?, ?, ?, ?)", incident_rows
)

# ---------------------------------------------------------------------------
# Staff (~200 rows)
# ---------------------------------------------------------------------------

FIRST_NAMES = [
    "James", "Sarah", "David", "Emma", "Michael", "Lucy", "Daniel", "Sophie",
    "Andrew", "Charlotte", "Thomas", "Hannah", "Robert", "Olivia", "William",
    "Amelia", "Richard", "Grace", "Joseph", "Ella", "Christopher", "Mia",
    "Matthew", "Chloe", "Benjamin", "Emily", "Samuel", "Jessica", "George",
    "Alice", "Henry", "Lily", "Edward", "Ruby", "Alexander", "Isabelle",
    "Jack", "Freya", "Oscar", "Poppy",
]

LAST_NAMES = [
    "Smith", "Jones", "Williams", "Taylor", "Brown", "Davies", "Evans",
    "Wilson", "Thomas", "Roberts", "Johnson", "Lewis", "Walker", "Robinson",
    "Wood", "Thompson", "White", "Watson", "Jackson", "Wright", "Green",
    "Harris", "Cooper", "King", "Lee", "Martin", "Clarke", "James", "Morgan",
    "Hughes", "Edwards", "Hill", "Moore", "Clark", "Harrison", "Scott",
    "Young", "Adams", "Mitchell", "Turner",
]

ROLES = ["station_manager", "ticket_officer", "maintenance", "security", "control_room"]

staff_rows = []
for staff_id in range(1, 201):
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    name = f"{first} {last}"
    role = random.choice(ROLES)

    # Control room staff have NULL station_id
    if role == "control_room":
        sid = None
    else:
        sid = random.choice([s[0] for s in stations])

    # Hire dates spread from 2005 to 2024
    hire_date = date(
        random.randint(2005, 2024),
        random.randint(1, 12),
        random.randint(1, 28),
    ).isoformat()

    staff_rows.append((staff_id, name, role, sid, hire_date))

cur.executemany(
    "INSERT INTO staff VALUES (?, ?, ?, ?, ?)", staff_rows
)

conn.commit()

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

tables = ["stations", "routes", "ridership", "incidents", "staff"]
print(f"Database created at: {DB_PATH}\n")
for table in tables:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0]
    print(f"  {table:12s}  {count:>6,} rows")

# Extra stats
cur.execute("SELECT COUNT(DISTINCT station_id) FROM incidents")
stations_with = cur.fetchone()[0]
print(f"\n  Stations with at least one incident: {stations_with}")
print(f"  Stations with zero incidents:        {len(stations) - stations_with}")

cur.execute("SELECT COUNT(*) FROM staff WHERE station_id IS NULL")
null_station = cur.fetchone()[0]
print(f"  Staff with NULL station_id (control room): {null_station}")

conn.close()
