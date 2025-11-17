import os
import glob
import json
from get_hevy_data import parse_hevy_csv
from collections import defaultdict


def load_all_fitbit_data(folder='data/fitbit_daily_data'):
    fitbit_data_list = []
    for filename in sorted(glob.glob(os.path.join(folder, '*.json'))):
        with open(filename) as f:
            fitbit_data_list.append(json.load(f))
    print(f"Loaded {len(fitbit_data_list)} Fitbit JSON files.")
    return fitbit_data_list

def km_to_miles(km):
    return km * 0.621371

def load_hevy_workouts(json_file='workouts.csv'):
    with open('data/hevy_daily_data/hevy_data.json') as f:
        hevy_workouts = json.load(f)
    return hevy_workouts

def combine_fitbit_hevy(fitbit_data_list, hevy_workouts):
    """
    Combine Fitbit and Hevy data into a per-date schema:
    {
        "steps": int,
        "distance": float,  <-- we’ll convert to miles instead
        "calories_burned": int,
        "sleep_hours": float,
        "sleep_score": int or None,
        "workout_title": str or None,
        "exercises": list of dict
    }
    """
    combined = defaultdict(lambda: {
        "steps": None,
        "distance": None,  # changed from km
        "calories_burned": None,
        "sleep_hours": None,
        "sleep_score": None,
        "workout_title": None,
        "exercises": []
    })

    # --------- Process Fitbit data ----------
    for data in fitbit_data_list:
        steps_ts = data['time_series']['steps'].get('activities-steps', [])
        distance_ts = data['time_series']['distance'].get('activities-distance', [])
        calories_ts = data['time_series']['calories_out'].get('activities-calories', [])
        sleep_data = data.get('sleep', [])

        # Steps
        for entry in steps_ts:
            date = entry['dateTime']
            combined[date]['steps'] = int(entry['value'])

        # Distance
        for entry in distance_ts:
            date = entry['dateTime']
            combined[date]['distance'] = float(entry['value'])

        # Calories
        for entry in calories_ts:
            date = entry['dateTime']
            combined[date]['calories_burned'] = int(entry['value'])

        # Sleep
        for entry in sleep_data:
            date = entry['dateOfSleep']
            combined[date]['sleep_hours'] = entry['duration'] / 1000 / 60 / 60  # ms → hours
            combined[date]['sleep_score'] = None  # Fitbit sleep score not fetched yet

    # --------- Process Hevy workouts ----------
    workouts_by_date = defaultdict(list)
    for w in hevy_workouts:
        workouts_by_date[w['date']].append(w)

    for date, exercises in workouts_by_date.items():
        if exercises:
            combined[date]['workout_title'] = exercises[0]['title']
            combined[date]['exercises'] = [
                {
                    "exercise": e['exercise'],
                    "set_type": e['set_type'],
                    "weight_lbs": e['weight_lbs'] if e['weight_lbs'] != '' else None,
                    "reps": int(e['reps']) if e['reps'] else None,
                    "distance": float(e['distance_miles']) if e['distance_miles'] else None,
                    "duration_seconds": int(e['duration_seconds']) if e['duration_seconds'] else None,
                    "notes": e.get('notes', '')
                } for e in exercises
            ]

    return dict(combined)

def main():
    # Load all Fitbit data
    fitbit_data_list = load_all_fitbit_data('data/fitbit_daily_data')

    # Load Hevy workouts
    hevy_workouts = load_hevy_workouts('data/hevy_daily_data/hevy_data.json')

    # Combine everything
    combined = combine_fitbit_hevy(fitbit_data_list, hevy_workouts)
    # print (combined)

    # Save final JSON
    # os.makedirs('data', exist_ok=True)
    with open('data/combined.json', 'w') as f:
        json.dump(combined, f, indent=2)

    print("Combined data saved to data/combined.json")
