#!/usr/bin/env python3
import json
import os
from datetime import datetime, timedelta
from fitbit import Fitbit
import pytz

# ------------------------
# Config / Files
# ------------------------
RESULT_DIR = os.path.join(os.getcwd(), 'data', 'fitbit_daily_data')
COMBINED_FILE = os.path.join(RESULT_DIR, 'fitbit_combined.json')
os.makedirs(RESULT_DIR, exist_ok=True)

# ------------------------
# Helpers
# ------------------------
def refresh_callback(token):
    """Called automatically when Fitbit refreshes your token."""
    # In GitHub Actions, we cannot update secrets; store token in file if needed
    token_path = os.path.join(RESULT_DIR, "user_details.json")
    with open(token_path, 'w') as f:
        json.dump(token, f, indent=2)
    print("Token refreshed and saved to file (not repo secret).")

def load_json(secret_value):
    """Convert JSON string from GitHub Actions secret into dict."""
    return json.loads(secret_value)


# --- Determine the last full Fitbit day ---
def get_yesterday_date_et():
    """
    Returns yesterday's date in ET as ISO string.
    This ensures we only request Fitbit data that actually exists.
    """
    et = pytz.timezone("America/New_York")
    now_et = datetime.datetime.now(et)
    yesterday_et = now_et - datetime.timedelta(days=1)
    return yesterday_et.date().isoformat()

# ------------------------
# Fetch Fitbit Data
# ------------------------
def fetch_fitbit_data(auth2_client, days=7):
    # today = datetime.now().date()
    today = get_yesterday_date_et()
    print(f"Using {today} as reference date for Fitbit merging")
    period = f"{days}d"

    # Time series data
    time_series = {
        "steps": auth2_client.time_series('activities/steps', period=period),
        "calories_out": auth2_client.time_series('activities/calories', period=period),
        "calories_in": auth2_client.time_series('foods/log/caloriesIn', period=period),
        "distance": auth2_client.time_series('activities/distance', period=period),
        "floors": auth2_client.time_series('activities/floors', period=period),
        "heart": auth2_client.time_series('activities/heart', period=period),
        "active_minutes": {
            "very": auth2_client.time_series('activities/minutesVeryActive', period=period),
            "fairly": auth2_client.time_series('activities/minutesFairlyActive', period=period),
            "light": auth2_client.time_series('activities/minutesLightlyActive', period=period),
            "sedentary": auth2_client.time_series('activities/minutesSedentary', period=period)
        },
        "weight": auth2_client.time_series('body/weight', period=period),
        "fat": auth2_client.time_series('body/fat', period=period)
    }

    # Sleep data
    sleep_data = []
    for i in range(days):
        day = today - timedelta(days=i)
        sleep_day = auth2_client.sleep(date=day.strftime('%Y-%m-%d'))
        if 'sleep' in sleep_day:
            sleep_data.extend(sleep_day['sleep'])

    return {
        "date_fetched": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "time_series": time_series,
        "sleep": sleep_data
    }

# ------------------------
# Flatten & Merge
# ------------------------
def extract_daily_records(data):
    daily_data = {}

    # Flatten time series
    for key, value in data['time_series'].items():
        if isinstance(value, dict) and 'very' in value:
            # active_minutes dict
            for subkey, subval in value.items():
                dataset = list(subval.values())[0] if isinstance(subval, dict) else subval
                for entry in dataset:
                    date = entry['dateTime']
                    daily_data.setdefault(date, {})[f"{key}_{subkey}"] = entry['value']
        else:
            dataset = list(value.values())[0] if isinstance(value, dict) else value
            for entry in dataset:
                date = entry['dateTime']
                daily_data.setdefault(date, {})[key] = entry['value']

    # Sleep
    for entry in data.get('sleep', []):
        date = entry.get('dateOfSleep')
        if not date:
            continue
        daily_data.setdefault(date, {})
        daily_data[date]['sleep_duration'] = entry.get('duration')
        daily_data[date]['sleep_efficiency'] = entry.get('efficiency')
        daily_data[date]['sleep_start'] = entry.get('startTime')
        daily_data[date]['sleep_end'] = entry.get('endTime')

    return daily_data

def merge_and_save(new_data):
    if os.path.exists(COMBINED_FILE):
        with open(COMBINED_FILE) as f:
            combined = json.load(f)
    else:
        combined = {}

    combined.update(new_data)
    combined = dict(sorted(combined.items()))
    with open(COMBINED_FILE, 'w') as f:
        json.dump(combined, f, indent=2)

    print(f"Merged and saved {len(new_data)} days of data to {COMBINED_FILE}")

# ------------------------
# Main
# ------------------------
def main():
    # Load credentials from GitHub Actions secrets
    client_details = load_json(os.environ["FITBIT_CLIENT_DETAILS"])
    user_details = load_json(os.environ["FITBIT_USER_DETAILS"])

    auth2_client = Fitbit(
        client_details['client_id'],
        client_details['client_secret'],
        oauth2=True,
        access_token=user_details['access_token'],
        refresh_token=user_details['refresh_token'],
        expires_at=user_details['expires_at'],
        refresh_cb=refresh_callback
    )

    data = fetch_fitbit_data(auth2_client, days=7)
    new_data = extract_daily_records(data)
    merge_and_save(new_data)

if __name__ == "__main__":
    main()
