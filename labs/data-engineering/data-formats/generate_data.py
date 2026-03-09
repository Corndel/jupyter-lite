"""Generate all data files for the Data Formats module."""

import csv
import json
import os
import random
import math
from datetime import datetime, timedelta

random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Helper data
# ---------------------------------------------------------------------------

STATIONS = [
    ("WS001", "Zurich Central", "Switzerland", 47.3769, 8.5417, 408),
    ("WS002", "Sao Paulo Paulista", "Brazil", -23.5505, -46.6333, 760),
    ("WS003", "Malmo Harbour", "Sweden", 55.6050, 13.0038, 12),
    ("WS004", "London Heathrow", "United Kingdom", 51.4700, -0.4543, 25),
    ("WS005", "Dusseldorf Rhine", "Germany", 51.2277, 6.7735, 38),
    ("WS006", "Montreal Centre", "Canada", 45.5017, -73.5673, 36),
    ("WS007", "Goteborg Coast", "Sweden", 57.7089, 11.9746, 5),
    ("WS008", "Jyvaskyla Lake", "Finland", 62.2415, 25.7209, 78),
    ("WS009", "Cordoba Sierra", "Spain", 37.8882, -4.7794, 106),
    ("WS010", "Brno South", "Czech Republic", 49.1951, 16.6068, 237),
    ("WS011", "Wurzburg Valley", "Germany", 49.7913, 9.9534, 177),
    ("WS012", "Strasbourg East", "France", 48.5734, 7.7521, 142),
    ("WS013", "Krakow Old Town", "Poland", 50.0647, 19.9450, 219),
    ("WS014", "Reykjavik Port", "Iceland", 64.1466, -21.9426, 14),
    ("WS015", "Tromso Arctic", "Norway", 69.6492, 18.9553, 10),
    ("WS016", "Oulu North", "Finland", 65.0121, 25.4651, 15),
    ("WS017", "Cluj-Napoca Centre", "Romania", 46.7712, 23.6236, 405),
    ("WS018", "Porto Atlantic", "Portugal", 41.1579, -8.6291, 85),
    ("WS019", "Thessaloniki Bay", "Greece", 40.6401, 22.9444, 5),
    ("WS020", "Izmir Coastal", "Turkey", 38.4192, 27.1287, 2),
    ("WS021", "Gdansk Baltic", "Poland", 54.3520, 18.6466, 7),
    ("WS022", "Bergen Fjord", "Norway", 60.3913, 5.3221, 12),
    ("WS023", "Ljubljana Basin", "Slovenia", 46.0569, 14.5058, 295),
    ("WS024", "Bratislava Danube", "Slovakia", 48.1486, 17.1077, 134),
    ("WS025", "Tallinn Harbour", "Estonia", 59.4370, 24.7536, 9),
]

# Proper Unicode names (for UTF-8 / Latin-1 test)
UNICODE_NAMES = {
    "WS001": "Z\u00fcrich Central",
    "WS002": "S\u00e3o Paulo Paulista",
    "WS003": "Malm\u00f6 Harbour",
    "WS005": "D\u00fcsseldorf Rhine",
    "WS006": "Montr\u00e9al Centre",
    "WS007": "G\u00f6teborg Coast",
    "WS008": "Jyv\u00e4skyl\u00e4 Lake",
    "WS009": "C\u00f3rdoba Sierra",
    "WS010": "Brn\u011b South",  # note: ě is NOT in Latin-1 -- we'll replace with Brno
    "WS011": "W\u00fcrzburg Valley",
    "WS012": "Strasbourg Est",
    "WS013": "Krak\u00f3w Old Town",
    "WS017": "Cluj-Napoca Centre",
    "WS018": "P\u00f4rto Atlantic",
    "WS022": "Bergen Fj\u00f8rd",
    "WS025": "R\u00e9val Harbour",  # old name for Tallinn
}

# For the Latin-1 file we must only use characters in Latin-1 range (0-255).
# ě (U+011B) is outside Latin-1, so we override those.
LATIN1_SAFE_NAMES = dict(UNICODE_NAMES)
LATIN1_SAFE_NAMES["WS010"] = "Brno South"  # drop the háček


def _base_temp(lat, month):
    """Very rough baseline temperature from latitude and month."""
    # Higher latitude = colder; northern hemisphere summer in Jul
    lat_factor = (90 - abs(lat)) / 90 * 30  # 0-30 range
    season = 10 * math.sin((month - 1) / 12 * 2 * math.pi - math.pi / 2)
    if lat < 0:
        season = -season
    return lat_factor + season - 5


# ---------------------------------------------------------------------------
# 1. weather_stations.csv (UTF-8)  ~500 rows
# ---------------------------------------------------------------------------

def generate_weather_stations_csv():
    rows = []
    start_date = datetime(2023, 1, 1)
    for day_offset in range(20):  # 20 dates
        date = start_date + timedelta(days=day_offset * 18)  # spread over a year
        for sid, name, country, lat, lon, elev in STATIONS:
            display_name = UNICODE_NAMES.get(sid, name)
            month = date.month
            base_t = _base_temp(lat, month)
            temp = round(base_t + random.gauss(0, 3), 1)
            humidity = round(max(20, min(100, 65 + random.gauss(0, 15))), 1)
            wind = round(max(0, 4 + random.gauss(0, 2.5)), 1)
            rows.append({
                "station_id": sid,
                "station_name": display_name,
                "country": country,
                "latitude": lat,
                "longitude": lon,
                "elevation_m": elev,
                "avg_temp_c": temp,
                "avg_humidity_pct": humidity,
                "avg_wind_speed_ms": wind,
                "measurement_date": date.strftime("%Y-%m-%d"),
            })

    path = os.path.join(DATA_DIR, "weather_stations.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"  weather_stations.csv: {len(rows)} rows")


# ---------------------------------------------------------------------------
# 2. weather_stations_latin1.csv  (ISO-8859-1 encoded)
# ---------------------------------------------------------------------------

def generate_weather_stations_latin1():
    rows = []
    start_date = datetime(2023, 1, 1)
    for day_offset in range(20):
        date = start_date + timedelta(days=day_offset * 18)
        for sid, name, country, lat, lon, elev in STATIONS:
            display_name = LATIN1_SAFE_NAMES.get(sid, name)
            month = date.month
            base_t = _base_temp(lat, month)
            temp = round(base_t + random.gauss(0, 3), 1)
            humidity = round(max(20, min(100, 65 + random.gauss(0, 15))), 1)
            wind = round(max(0, 4 + random.gauss(0, 2.5)), 1)
            rows.append({
                "station_id": sid,
                "station_name": display_name,
                "country": country,
                "latitude": lat,
                "longitude": lon,
                "elevation_m": elev,
                "avg_temp_c": temp,
                "avg_humidity_pct": humidity,
                "avg_wind_speed_ms": wind,
                "measurement_date": date.strftime("%Y-%m-%d"),
            })

    path = os.path.join(DATA_DIR, "weather_stations_latin1.csv")
    with open(path, "w", newline="", encoding="latin-1") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"  weather_stations_latin1.csv: {len(rows)} rows (Latin-1 encoded)")


# ---------------------------------------------------------------------------
# 3. ocean_buoys.json  (~100 buoy readings, nested)
# ---------------------------------------------------------------------------

BUOY_LOCATIONS = [
    ("NDBC-44013", 42.346, -70.651, "Boston Harbor"),
    ("NDBC-41002", 32.309, -75.483, "South Atlantic Bight"),
    ("NDBC-46029", 46.144, -124.514, "Columbia River Bar"),
    ("NDBC-51003", 19.196, -160.639, "Western Hawaii"),
    ("NDBC-42001", 25.888, -89.658, "Gulf of Mexico Central"),
    ("EMB-62163", 58.200, -5.100, "North Minch"),
    ("EMB-62105", 50.100, -6.100, "Seven Stones Light"),
    ("EMB-62303", 53.500, -3.500, "Liverpool Bay"),
    ("JMA-21004", 29.000, 135.000, "Southeast of Honshu"),
    ("JMA-22001", 34.000, 145.000, "Northwest Pacific"),
    ("BOM-55015", -34.000, 151.400, "Sydney Offshore"),
    ("BOM-55019", -27.500, 153.600, "Brisbane Approaches"),
    ("METNO-76923", 66.000, 2.000, "Norwegian Sea"),
    ("METNO-76928", 73.000, 13.000, "Barents Sea South"),
    ("BSH-FINO1", 54.015, 6.588, "German Bight"),
    ("IFREMER-08501", 47.500, -8.500, "Bay of Biscay North"),
    ("IFREMER-08504", 43.500, -1.500, "Bay of Biscay South"),
    ("CDIP-071", 33.221, -117.440, "San Diego Nearshore"),
    ("CDIP-073", 34.452, -120.650, "Santa Barbara Channel"),
    ("INCOIS-AD07", 15.000, 69.000, "Arabian Sea"),
]

BUOY_STATUSES = ["active", "active", "active", "active", "maintenance", "active",
                  "active", "inactive", "active", "active"]


def generate_ocean_buoys_json():
    readings = []
    base_time = datetime(2024, 3, 15, 0, 0, 0)
    for i in range(100):
        buoy = BUOY_LOCATIONS[i % len(BUOY_LOCATIONS)]
        bid, lat, lon, name = buoy
        ts = base_time + timedelta(hours=i * 3, minutes=random.randint(0, 59))
        water_temp = round(random.uniform(2, 28), 1)
        wave_h = round(random.uniform(0.3, 5.0), 1)
        wave_p = round(random.uniform(3, 14), 1)
        wind_spd = round(random.uniform(1, 20), 1)
        wind_dir = random.randint(0, 359)

        readings.append({
            "buoy_id": bid,
            "location": {
                "lat": lat + round(random.gauss(0, 0.002), 4),
                "lon": lon + round(random.gauss(0, 0.002), 4),
                "name": name,
            },
            "measurements": {
                "water_temp_c": water_temp,
                "wave_height_m": wave_h,
                "wave_period_s": wave_p,
                "wind": {
                    "speed_ms": wind_spd,
                    "direction_deg": wind_dir,
                },
            },
            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": random.choice(BUOY_STATUSES),
        })

    path = os.path.join(DATA_DIR, "ocean_buoys.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(readings, f, indent=2)
    print(f"  ocean_buoys.json: {len(readings)} readings")


# ---------------------------------------------------------------------------
# 4. temperature_historical.csv  (~50,000 rows)
# ---------------------------------------------------------------------------

def generate_temperature_historical():
    """Hourly readings from one station over ~6 years."""
    path = os.path.join(DATA_DIR, "temperature_historical.csv")
    start = datetime(2018, 1, 1, 0, 0, 0)
    n_hours = 50000  # ~5.7 years of hourly data

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["station_id", "date", "hour", "temp_c",
                          "humidity_pct", "pressure_hpa"])
        for i in range(n_hours):
            ts = start + timedelta(hours=i)
            month = ts.month
            hour = ts.hour
            # Seasonal cycle + diurnal cycle + noise
            seasonal = 10 * math.sin((month - 1) / 12 * 2 * math.pi - math.pi / 2)
            diurnal = 4 * math.sin((hour - 6) / 24 * 2 * math.pi)
            temp = round(12 + seasonal + diurnal + random.gauss(0, 2.5), 1)
            humidity = round(max(15, min(100, 60 - diurnal * 3 + random.gauss(0, 8))), 1)
            pressure = round(1013.25 + random.gauss(0, 8), 1)
            writer.writerow([
                "WS001",
                ts.strftime("%Y-%m-%d"),
                hour,
                temp,
                humidity,
                pressure,
            ])
    print(f"  temperature_historical.csv: {n_hours} rows")


# ---------------------------------------------------------------------------
# 5. station_config.yaml
# ---------------------------------------------------------------------------

def generate_station_config_yaml():
    yaml_content = """network:
  name: "Global Climate Monitoring Network"
  version: "2.1"
  contact:
    email: "ops@gcmn-climate.org"
    phone: "+41-44-555-0100"

defaults:
  sampling_interval_s: 600
  transmission_protocol: "MQTT"
  data_format: "JSON"
  retry_attempts: 3

stations:
  - id: "WS001"
    name: "Zurich Central"
    country: "Switzerland"
    location:
      lat: 47.3769
      lon: 8.5417
      elevation_m: 408
    sensors:
      - temperature
      - humidity
      - pressure
      - wind_speed
      - wind_direction
    calibration_date: "2024-01-15"
    status: "active"
    notes: "Primary reference station for Alpine region"

  - id: "WS002"
    name: "Sao Paulo Paulista"
    country: "Brazil"
    location:
      lat: -23.5505
      lon: -46.6333
      elevation_m: 760
    sensors:
      - temperature
      - humidity
      - pressure
      - rainfall
    calibration_date: "2024-02-20"
    status: "active"
    notes: "Urban heat island study participant"

  - id: "WS003"
    name: "Malmo Harbour"
    country: "Sweden"
    location:
      lat: 55.6050
      lon: 13.0038
      elevation_m: 12
    sensors:
      - temperature
      - humidity
      - wind_speed
      - wind_direction
      - sea_surface_temp
    calibration_date: "2023-11-10"
    status: "active"
    notes: "Coastal station, co-located with tide gauge"

  - id: "WS004"
    name: "London Heathrow"
    country: "United Kingdom"
    location:
      lat: 51.4700
      lon: -0.4543
      elevation_m: 25
    sensors:
      - temperature
      - humidity
      - pressure
      - wind_speed
      - wind_direction
      - visibility
    calibration_date: "2024-03-01"
    status: "active"
    notes: "Aviation weather station, high-frequency sampling"

  - id: "WS014"
    name: "Reykjavik Port"
    country: "Iceland"
    location:
      lat: 64.1466
      lon: -21.9426
      elevation_m: 14
    sensors:
      - temperature
      - humidity
      - pressure
      - wind_speed
      - wind_direction
    calibration_date: "2023-09-22"
    status: "maintenance"
    notes: "Wind sensor replacement scheduled"

  - id: "WS015"
    name: "Tromso Arctic"
    country: "Norway"
    location:
      lat: 69.6492
      lon: 18.9553
      elevation_m: 10
    sensors:
      - temperature
      - humidity
      - pressure
      - uv_index
      - aurora_activity
    calibration_date: "2024-01-05"
    status: "active"
    notes: "Part of Arctic monitoring programme"

alerts:
  temperature_range:
    min_c: -60
    max_c: 60
  wind_speed_max_ms: 75
  pressure_range:
    min_hpa: 870
    max_hpa: 1084
  notification_channels:
    - email
    - sms
    - slack
"""
    path = os.path.join(DATA_DIR, "station_config.yaml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    print("  station_config.yaml: written")


# ---------------------------------------------------------------------------
# 6. satellite_metadata.xml  (~15 datasets)
# ---------------------------------------------------------------------------

SATELLITE_DATASETS = [
    ("SAT-001", "MODIS Terra Surface Temperature", "Terra", "MODIS", 1,
     "2000-02-24", "2024-12-31",
     [("LST_Day", "K"), ("LST_Night", "K")]),
    ("SAT-002", "MODIS Aqua Ocean Colour", "Aqua", "MODIS", 4,
     "2002-07-04", "2024-12-31",
     [("chlor_a", "mg/m^3"), ("Rrs_443", "sr^-1"), ("Rrs_555", "sr^-1")]),
    ("SAT-003", "Landsat 8 Surface Reflectance", "Landsat 8", "OLI", 0.03,
     "2013-04-11", "2024-12-31",
     [("SR_B1", "reflectance"), ("SR_B2", "reflectance"), ("SR_B3", "reflectance"), ("SR_B4", "reflectance")]),
    ("SAT-004", "Sentinel-2 MSI Level-2A", "Sentinel-2A", "MSI", 0.01,
     "2015-06-23", "2024-12-31",
     [("B02_Blue", "reflectance"), ("B03_Green", "reflectance"), ("B04_Red", "reflectance"), ("B08_NIR", "reflectance")]),
    ("SAT-005", "GOES-16 ABI Cloud and Moisture", "GOES-16", "ABI", 2,
     "2017-12-18", "2024-12-31",
     [("CMI_C08", "K"), ("CMI_C09", "K"), ("CMI_C10", "K")]),
    ("SAT-006", "VIIRS Sea Surface Temperature", "Suomi NPP", "VIIRS", 0.75,
     "2012-01-19", "2024-12-31",
     [("SST", "K"), ("SST_quality", "flag")]),
    ("SAT-007", "AIRS Atmospheric Temperature Profile", "Aqua", "AIRS", 50,
     "2002-08-30", "2024-12-31",
     [("TAirSup", "K"), ("TAirMid", "K"), ("H2OMMRSup", "g/kg")]),
    ("SAT-008", "CERES Energy Balanced and Filled", "Terra", "CERES", 100,
     "2000-03-01", "2024-12-31",
     [("SW_TOA", "W/m^2"), ("LW_TOA", "W/m^2"), ("NET_TOA", "W/m^2")]),
    ("SAT-009", "GRACE-FO Gravity Anomaly", "GRACE-FO", "MWI", 300,
     "2018-05-22", "2024-12-31",
     [("lwe_thickness", "cm"), ("uncertainty", "cm")]),
    ("SAT-010", "ICESat-2 Ice Sheet Elevation", "ICESat-2", "ATLAS", 0.01,
     "2018-09-15", "2024-12-31",
     [("h_li", "m"), ("h_li_sigma", "m"), ("signal_conf", "flag")]),
    ("SAT-011", "Sentinel-5P Tropospheric NO2", "Sentinel-5P", "TROPOMI", 7,
     "2018-04-30", "2024-12-31",
     [("tropospheric_NO2", "mol/m^2"), ("stratospheric_NO2", "mol/m^2")]),
    ("SAT-012", "GPM IMERG Precipitation", "GPM Core", "GMI/DPR", 10,
     "2014-03-12", "2024-12-31",
     [("precipitation", "mm/hr"), ("precipitationQualityIndex", "unitless")]),
    ("SAT-013", "SMAP Soil Moisture", "SMAP", "Radiometer", 36,
     "2015-03-31", "2024-12-31",
     [("soil_moisture", "cm^3/cm^3"), ("vegetation_water_content", "kg/m^2")]),
    ("SAT-014", "CryoSat-2 Sea Ice Thickness", "CryoSat-2", "SIRAL", 1,
     "2010-07-08", "2024-12-31",
     [("sea_ice_thickness", "m"), ("freeboard", "m"), ("snow_depth", "m")]),
    ("SAT-015", "MetOp-C IASI Ozone Profile", "MetOp-C", "IASI", 25,
     "2018-11-07", "2024-12-31",
     [("ozone_total_column", "DU"), ("ozone_profile", "ppmv")]),
]


def generate_satellite_xml():
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<catalogue agency="Global Climate Data Alliance" updated="2024-06-01">')
    for ds in SATELLITE_DATASETS:
        did, name, sat, inst, res, start, end, variables = ds
        lines.append(f'  <dataset id="{did}">')
        lines.append(f'    <name>{name}</name>')
        lines.append(f'    <satellite>{sat}</satellite>')
        lines.append(f'    <instrument>{inst}</instrument>')
        lines.append(f'    <resolution_km>{res}</resolution_km>')
        lines.append(f'    <temporal_coverage>')
        lines.append(f'      <start>{start}</start>')
        lines.append(f'      <end>{end}</end>')
        lines.append(f'    </temporal_coverage>')
        lines.append(f'    <variables>')
        for vname, unit in variables:
            lines.append(f'      <variable name="{vname}" unit="{unit}" />')
        lines.append(f'    </variables>')
        lines.append(f'  </dataset>')
    lines.append('</catalogue>')
    lines.append('')

    path = os.path.join(DATA_DIR, "satellite_metadata.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  satellite_metadata.xml: {len(SATELLITE_DATASETS)} datasets")


# ---------------------------------------------------------------------------
# Run all generators
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Generating data files...")
    generate_weather_stations_csv()
    generate_weather_stations_latin1()
    generate_ocean_buoys_json()
    generate_temperature_historical()
    generate_station_config_yaml()
    generate_satellite_xml()
    print("Done.")
