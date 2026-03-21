"""Generate renewable energy grid data for the Time Series and Trends lab."""
import csv
import math
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# 2024 is a leap year: 366 days, 8784 hours
START = datetime(2024, 1, 1, 0, 0, 0)
HOURS_IN_YEAR = 8784

UK_HOLIDAYS_2024 = {
    datetime(2024, 1, 1).date(),    # New Year's Day
    datetime(2024, 3, 29).date(),   # Good Friday
    datetime(2024, 4, 1).date(),    # Easter Monday
    datetime(2024, 5, 6).date(),    # Early May bank holiday
    datetime(2024, 5, 27).date(),   # Spring bank holiday
    datetime(2024, 8, 26).date(),   # Summer bank holiday
    datetime(2024, 12, 25).date(),  # Christmas Day
    datetime(2024, 12, 26).date(),  # Boxing Day
}

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def hour_of_year_timestamps():
    """Return list of datetime objects for every hour of 2024."""
    return [START + timedelta(hours=h) for h in range(HOURS_IN_YEAR)]


def gauss(mu=0, sigma=1):
    """Convenience wrapper around random.gauss."""
    return random.gauss(mu, sigma)


def seasonal_factor(day_of_year, peak_day=172, amplitude=1.0):
    """Cosine seasonal curve. peak_day=172 is ~21 June (summer solstice)."""
    return amplitude * math.cos(2 * math.pi * (day_of_year - peak_day) / 366)


def generate_grid_demand(filepath, timestamps):
    """Generate hourly grid demand data for 2024."""
    fieldnames = ["timestamp", "demand_mw", "temperature_c", "day_of_week", "is_holiday"]
    rows = []

    for ts in timestamps:
        hour = ts.hour
        day_of_year = ts.timetuple().tm_yday
        weekday = ts.weekday()  # 0=Monday, 6=Sunday

        # --- Temperature ---
        # Seasonal: winter ~2-8, summer ~18-28
        seasonal_temp = 12 + 10 * seasonal_factor(day_of_year)
        # Daily cycle: coolest at 05:00, warmest at 15:00
        daily_temp = 3 * math.sin(2 * math.pi * (hour - 5) / 24)
        temperature = seasonal_temp + daily_temp + gauss(0, 1.5)

        # --- Demand ---
        # Base demand with seasonal pattern: higher in winter for heating
        base_demand = 33000 - 4000 * seasonal_factor(day_of_year)

        # Daily cycle: low at night (~25000), morning ramp, peak at 18:00 (~42000)
        if hour <= 5:
            daily_demand = -8000 + 500 * hour
        elif hour <= 9:
            daily_demand = -5500 + 2500 * (hour - 5)
        elif hour <= 16:
            daily_demand = 4500 + 300 * (hour - 9)
        elif hour <= 18:
            daily_demand = 6600 + 700 * (hour - 16)
        elif hour <= 22:
            daily_demand = 8000 - 1500 * (hour - 18)
        else:
            daily_demand = 2000 - 2000 * (hour - 22)

        demand = base_demand + daily_demand

        # Weekend reduction: ~10% lower
        is_weekend = weekday >= 5
        if is_weekend:
            demand *= 0.90

        # Holiday reduction
        is_holiday = ts.date() in UK_HOLIDAYS_2024
        if is_holiday:
            demand *= 0.88

        # Noise
        demand += gauss(0, 1500)

        rows.append({
            "timestamp": ts.strftime("%Y-%m-%d %H:%M"),
            "demand_mw": round(demand, 1),
            "temperature_c": round(temperature, 1),
            "day_of_week": DAY_NAMES[weekday],
            "is_holiday": is_holiday,
        })

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Wrote {len(rows)} rows to {filepath}")


def generate_solar_output(filepath, timestamps):
    """Generate hourly solar output data for 2024."""
    fieldnames = ["timestamp", "output_mw", "cloud_cover_pct", "daylight_hours"]
    rows = []

    # Cloud cover with day-to-day persistence
    cloud_cover = 50.0

    for ts in timestamps:
        hour = ts.hour
        day_of_year = ts.timetuple().tm_yday

        # Daylight hours: seasonal, ~7 in winter to ~17 in summer
        daylight = 12 + 5 * seasonal_factor(day_of_year)

        # Sunrise/sunset times (symmetric around noon)
        sunrise = 12 - daylight / 2
        sunset = 12 + daylight / 2

        # Cloud cover: random walk with mean-reversion
        cloud_cover += gauss(0, 5)
        cloud_cover = 0.95 * cloud_cover + 0.05 * 45  # mean-revert towards 45%
        cloud_cover = max(0.0, min(100.0, cloud_cover))

        # Solar output: bell curve during daylight, zero at night
        if sunrise < hour < sunset:
            # Normalised position in the day (0 at sunrise, 1 at sunset)
            day_fraction = (hour - sunrise) / (sunset - sunrise)
            # Bell curve peaking at 0.5 (solar noon)
            bell = math.sin(math.pi * day_fraction)
            # Peak capacity: higher in summer (~8000 MW) vs winter (~2000 MW)
            peak_mw = 3500 + 4500 * seasonal_factor(day_of_year)
            # Cloud reduction
            cloud_factor = 1 - 0.7 * (cloud_cover / 100)
            output = peak_mw * bell * cloud_factor
            output = max(0.0, output + gauss(0, 100))
        else:
            output = 0.0

        rows.append({
            "timestamp": ts.strftime("%Y-%m-%d %H:%M"),
            "output_mw": round(output, 1),
            "cloud_cover_pct": round(cloud_cover, 1),
            "daylight_hours": round(daylight, 1),
        })

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Wrote {len(rows)} rows to {filepath}")


def generate_wind_output(filepath, timestamps):
    """Generate hourly wind output data for 2024."""
    fieldnames = ["timestamp", "output_mw", "wind_speed_ms", "direction_deg"]
    rows = []

    # Wind speed: persistent multi-day patterns (weather fronts)
    wind_speed = 8.0
    direction = 220.0  # prevailing south-westerly

    for ts in timestamps:
        day_of_year = ts.timetuple().tm_yday

        # Wind speed: random walk with seasonal bias (windier in winter)
        seasonal_wind = 2 * (-seasonal_factor(day_of_year))  # higher in winter
        wind_speed += gauss(0, 0.5)
        # Mean-revert towards seasonal baseline
        target = 9 + seasonal_wind
        wind_speed = 0.98 * wind_speed + 0.02 * target
        wind_speed = max(0.0, min(25.0, wind_speed))

        # Direction: slow random walk
        direction += gauss(0, 5)
        direction = direction % 360

        # Output: roughly cubic relationship with wind speed, capped
        # Cut-in at ~3 m/s, rated at ~12 m/s, cut-out at ~25 m/s
        if wind_speed < 3:
            output = 0.0
        elif wind_speed > 24:
            output = 0.0  # turbines shut down in extreme wind
        elif wind_speed >= 12:
            output = 5500 + gauss(0, 200)
        else:
            # Quadratic ramp between cut-in and rated
            fraction = (wind_speed - 3) / (12 - 3)
            output = 500 + 5000 * (fraction ** 2)
            output += gauss(0, 200)

        output = max(0.0, min(6000.0, output))

        rows.append({
            "timestamp": ts.strftime("%Y-%m-%d %H:%M"),
            "output_mw": round(output, 1),
            "wind_speed_ms": round(wind_speed, 1),
            "direction_deg": int(direction) % 360,
        })

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Wrote {len(rows)} rows to {filepath}")


if __name__ == "__main__":
    print("Generating Time Series and Trends lab data...")
    timestamps = hour_of_year_timestamps()
    generate_grid_demand(DATA_DIR / "grid_demand_hourly.csv", timestamps)
    generate_solar_output(DATA_DIR / "solar_output.csv", timestamps)
    generate_wind_output(DATA_DIR / "wind_output.csv", timestamps)
    print("Done!")
