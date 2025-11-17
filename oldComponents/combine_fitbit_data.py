#!/usr/bin/env python3
import json
import os

OLD_FILE = 'data/fitbit_daily_data/2025-10-12.json'       # your old 30-day file
NEW_COMBINED_FILE = 'data/fitbit_daily_data/fitbit_combined.json'
OUTPUT_FILE = 'data/fitbit_daily_data/fitbit_combined_merged.json'


def flatten_old_fitbit_format(old_data):
    """
    Convert old Fitbit JSON (with time_series + sleep arrays) into
    the new date-keyed format:
      { "YYYY-MM-DD": { "steps_activities-steps": value, ... } }
    """
    daily_data = {}

    time_series = old_data.get("time_series", {})

    # Process each metric (e.g., steps, calories_out, etc.)
    for key, dataset in time_series.items():
        # Handle nested dicts (e.g., active_minutes)
        if isinstance(dataset, dict) and "activities-minutesVeryActive" not in dataset:
            for subkey, subval in dataset.items():
                series_key = f"{key}_{subkey}"
                for subdataset in subval.values() if isinstance(subval, dict) else [subval]:
                    for entry in subdataset:
                        date = entry["dateTime"]
                        daily_data.setdefault(date, {})[series_key] = entry["value"]

        else:
            # Standard Fitbit series: {"activities-steps": [ {dateTime, value}, ... ]}
            for inner_key, values in dataset.items():
                for entry in values:
                    date = entry["dateTime"]
                    series_key = f"{key}_{inner_key}"
                    daily_data.setdefault(date, {})[series_key] = entry["value"]

    # Handle sleep data
    sleep_entries = old_data.get("sleep", [])
    for entry in sleep_entries:
        date = entry.get("dateOfSleep")
        if not date:
            continue
        daily_data.setdefault(date, {})
        daily_data[date]["sleep_duration"] = entry.get("duration")
        daily_data[date]["sleep_efficiency"] = entry.get("efficiency")
        daily_data[date]["sleep_start"] = entry.get("startTime")
        daily_data[date]["sleep_end"] = entry.get("endTime")

    return daily_data


def merge_datasets(old_flattened, new_data):
    """Merge two Fitbit datasets (both date-keyed)."""
    merged = {}
    merged.update(old_flattened)
    merged.update(new_data)
    return dict(sorted(merged.items()))


def main():
    if not os.path.exists(OLD_FILE):
        raise FileNotFoundError(f"Old Fitbit data file not found at {OLD_FILE}")
    if not os.path.exists(NEW_COMBINED_FILE):
        raise FileNotFoundError(f"New combined file not found at {NEW_COMBINED_FILE}")

    # Load both datasets
    with open(OLD_FILE) as f:
        old_data = json.load(f)
    with open(NEW_COMBINED_FILE) as f:
        new_data = json.load(f)

    # Flatten old data into new format
    old_flattened = flatten_old_fitbit_format(old_data)

    # Merge them
    merged = merge_datasets(old_flattened, new_data)

    # Save merged result
    with open(OUTPUT_FILE, "w") as f:
        json.dump(merged, f, indent=2)

    print(f"Merged dataset saved to: {OUTPUT_FILE}")
    print(f"Total days of data: {len(merged)}")


if __name__ == "__main__":
    main()
