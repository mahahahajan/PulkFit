import os
import glob
import json
from collections import defaultdict

# ------------------------
# Muscle group mapping
# ------------------------
EXERCISE_TO_MUSCLE = {
    "Pull Up": ["Back"],
    "Pull Up (Assisted)": ["Back"],
    "Chin Up": ["Biceps", "Back"],
    "Chin Up (Assisted)": ["Biceps", "Back"],
    "Bent Over Row (Barbell)": ["Back", "Rear Delts"],
    "Seated Row (Machine)": ["Back", "Rear Delts"],
    "Lat Pulldown (Cable)": ["Back", "Biceps"],
    "Lat Pulldown - Close Grip (Cable)": ["Back", "Biceps"],
    "lat pulldown Burn Outs": ["Back"],
    "Negative Pull Up": ["Back", "Biceps"],
    "Bench Press": ["Chest", "Triceps", "Shoulders"],
    "Incline Bench Press": ["Chest", "Shoulders", "Triceps"],
    "Incline Bench Press (Barbell)": ["Chest", "Shoulders", "Triceps"],
    "Incline Bench Press (Dumbbell)": ["Chest", "Shoulders", "Triceps"],
    "Overhead Press": ["Shoulders", "Triceps"],
    "Overhead Press (Barbell)": ["Shoulders", "Triceps"],
    "Overhead Press (Smith Machine)": ["Shoulders", "Triceps"],
    "Shoulder Press (Dumbbell)": ["Shoulders", "Triceps"],
    "Seated Shoulder Press (Machine)": ["Shoulders", "Triceps"],
    "Chest Dip": ["Chest", "Triceps", "Shoulders"],
    "Chest Dip (Assisted)": ["Chest", "Triceps", "Shoulders"],
    "Push Up": ["Chest", "Triceps", "Shoulders"],
    "Face Pull": ["Rear Delts", "Traps"],
    "Triceps Extension (Barbell)": ["Triceps"],
    "Triceps Extension (Cable)": ["Triceps"],
    "Overhead Triceps Extension (Cable)": ["Triceps"],
    "Triceps Rope Pushdown": ["Triceps"],
    "Hammer Curl (Dumbbell)": ["Biceps", "Forearms"],
    "Bicep Curl (Barbell)": ["Biceps"],
    "EZ Bar Biceps Curl": ["Biceps"],
    "Bicep Curl (Cable)": ["Biceps"],
    "Reverse Curl (Barbell)": ["Biceps", "Forearms"],
    "Lateral Raise (Dumbbell)": ["Shoulders"],
    "Single Arm Lateral Raise (Cable)": ["Shoulders"],
    "Lateral Raise (Cable)": ["Shoulders"],
    "Rear Delt Reverse Fly (Machine)": ["Rear Delts"],
    "Squat": ["Quads", "Glutes", "Hamstrings"],
    "Squat (Barbell)": ["Quads", "Glutes", "Hamstrings"],
    "Front Squat": ["Quads", "Glutes", "Hamstrings"],
    "Leg Press Horizontal (Machine)": ["Quads", "Glutes"],
    "Bulgarian Split Squat": ["Quads", "Glutes", "Hamstrings"],
    "Deadlift": ["Hamstrings", "Glutes", "Back"],
    "Deadlift (Barbell)": ["Hamstrings", "Glutes", "Back"],
    "Romanian Deadlift (Barbell)": ["Hamstrings", "Glutes", "Back"],
    "Hip Thrust (Barbell)": ["Glutes", "Hamstrings"],
    "Hanging Knee Raise": ["Abs"],
    "Leg Raise Parallel Bars": ["Abs"],
}

# Rough MET values per exercise for calorie estimation
EXERCISE_TO_MET = {
    # Back / Biceps
    "Pull Up": 8,
    "Pull Up (Assisted)": 6,
    "Chin Up": 8,
    "Chin Up (Assisted)": 6,
    "Bent Over Row (Barbell)": 6,
    "Seated Row (Machine)": 5.5,
    "Lat Pulldown (Cable)": 5.5,
    "Lat Pulldown - Close Grip (Cable)": 5.5,
    "Lat Pulldown Burn Outs": 5.5,
    "Negative Pull Up": 7,

    # Chest / Shoulders / Triceps
    "Bench Press": 6,
    "Incline Bench Press": 6,
    "Incline Bench Press (Barbell)": 6,
    "Incline Bench Press (Dumbbell)": 6,
    "Overhead Press": 5.5,
    "Overhead Press (Barbell)": 5.5,
    "Overhead Press (Smith Machine)": 5.5,
    "Shoulder Press (Dumbbell)": 5.5,
    "Seated Shoulder Press (Machine)": 5,
    "Chest Dip": 6,
    "Chest Dip (Assisted)": 5,
    "Push Up": 5.5,
    "Face Pull": 4.5,
    "Triceps Extension (Barbell)": 4,
    "Triceps Extension (Cable)": 4,
    "Triceps Rope Pushdown": 4,

    # Biceps
    "Hammer Curl (Dumbbell)": 4,
    "Bicep Curl (Barbell)": 4,
    "EZ Bar Biceps Curl": 4,
    "Bicep Curl (Cable)": 4,
    "Reverse Curl (Barbell)": 4,

    # Shoulders
    "Lateral Raise (Dumbbell)": 3.5,
    "Single Arm Lateral Raise (Cable)": 3.5,
    "Lateral Raise (Cable)": 3.5,
    "Rear Delt Reverse Fly (Machine)": 4,

    # Legs / Glutes / Core
    "Squat": 7,
    "Squat (Barbell)": 7,
    "Front Squat": 7,
    "Leg Press Horizontal (Machine)": 6.5,
    "Bulgarian Split Squat": 6.5,
    "Deadlift": 7,
    "Deadlift (Barbell)": 7,
    "Romanian Deadlift (Barbell)": 6.5,
    "Hip Thrust (Barbell)": 6,

    # Abs / Core
    "Hanging Knee Raise": 3.5,
    "Leg Raise Parallel Bars": 3.5,
}

LB_TO_KG = 0.453592

# ------------------------
# Helpers
# ------------------------
def km_to_miles(km):
    return km * 0.621371

def estimate_exercise_calories(exercise, weight_lbs, reps, duration_seconds=None, user_weight_lbs=160):
    """
    Rough calorie estimate per set
    """
    MET = EXERCISE_TO_MET.get(exercise, 5)  # default MET=5
    weight_kg = user_weight_lbs * LB_TO_KG

    # Estimate duration if not provided
    if duration_seconds is None or duration_seconds == 0:
        duration_minutes = (reps * 3) / 60  # 3 sec per rep
    else:
        duration_minutes = duration_seconds / 60

    calories = MET * 3.5 * weight_kg / 200 * duration_minutes
    return calories

# ------------------------
# Load data
# ------------------------
def load_all_fitbit_data(folder='data/fitbit_daily_data'):
    fitbit_data_list = []
    for filename in sorted(glob.glob(os.path.join(folder, '*.json'))):
        with open(filename) as f:
            fitbit_data_list.append(json.load(f))
    print(f"Loaded {len(fitbit_data_list)} Fitbit JSON files.")
    return fitbit_data_list

def load_hevy_workouts(json_file='data/hevy_daily_data/hevy_data_v2.json'):
    with open(json_file) as f:
        hevy_workouts = json.load(f)
    return hevy_workouts

# ------------------------
# Combine datasets
# ------------------------
def combine_fitbit_hevy(fitbit_data_list, hevy_workouts, user_weight_lbs=160):
    combined = defaultdict(lambda: {
        "steps": 0,
        "distance": 0.0,
        "total_calories_burned": 0,
        "sleep_hours": 0.0,
        "sleep_score": None,
        "workout_title": None,
        "exercises": [],
        "total_workout_duration": "0:00",
        "calories_burned_from_workout": 0,
        "calories_burned_from_steps": 0
    })

    # --------- Process Fitbit data ----------
    for data in fitbit_data_list:
        steps_ts = data['time_series']['steps'].get('activities-steps', [])
        distance_ts = data['time_series']['distance'].get('activities-distance', [])
        calories_ts = data['time_series']['calories_out'].get('activities-calories', [])
        sleep_data = data.get('sleep', [])

        for entry in steps_ts:
            date = entry['dateTime']
            combined[date]['steps'] = int(entry['value'])

        for entry in distance_ts:
            date = entry['dateTime']
            combined[date]['distance'] = float(entry['value'])

        for entry in calories_ts:
            date = entry['dateTime']
            combined[date]['calories_burned_from_steps'] = int(entry['value'])

        for entry in sleep_data:
            date = entry['dateOfSleep']
            combined[date]['sleep_hours'] = entry['duration'] / 1000 / 60 / 60
            combined[date]['sleep_score'] = None  # placeholder

    # --------- Process Hevy workouts ----------
    for workout in hevy_workouts:
        date = workout["Date"]
        combined[date]['workout_title'] = workout.get('Workout_Title')
        combined[date]['total_workout_duration'] = workout.get('Workout_Duration', "0:00")
        combined[date]['exercises'] = []

        total_workout_calories = 0

        for e in workout['exercises']:
            weight = float(e['weight_lbs']) if e.get('weight_lbs') else 0
            reps = int(e['reps']) if e.get('reps') else 0
            duration_seconds = int(e['duration_seconds']) if e.get('duration_seconds') else None
            exercise_name = e.get('exercise', '').lower()
            notes = e.get('notes', '').lower()

            # ---- Weight expansion logic ----
            actual_weight = weight
            if "barbell" in exercise_name.lower():
                actual_weight = 2 * weight + 45
            elif "assisted" in exercise_name.lower():
                bodyweight = user_weight_lbs
                actual_weight = bodyweight - weight
            elif "smith" in exercise_name.lower() or "smith" in notes.lower():
                actual_weight = 2 * weight
            elif "pull up" in exercise_name.lower() or "chest dip" in notes.lower():
                actual_weight = bodyweight

            # Calculate calories based on expanded weight
            calories = estimate_exercise_calories(
                e['exercise'],
                weight_lbs=actual_weight,
                reps=reps,
                duration_seconds=duration_seconds,
                user_weight_lbs=user_weight_lbs
            )
            total_workout_calories += calories

            combined[date]['exercises'].append({
                "exercise": e['exercise'],
                "set_type": e.get('set_type', ''),
                "weight_lbs": actual_weight,  # store expanded weight here
                "reps": reps if reps != 0 else None,
                "distance": float(e['distance_miles']) if e.get('distance_miles') else None,
                "notes": e.get('notes', ''),
                "muscle_groups": EXERCISE_TO_MUSCLE.get(e['exercise'], [])
            })

            if e['exercise'] not in EXERCISE_TO_MUSCLE:
                print(f"Didn't find exercise mapping for {e['exercise']}")

        combined[date]['calories_burned_from_workout'] = int(total_workout_calories)
        
        # combined[date]['calories_burned_from_steps'] = calories_from_fitbit

    for date, day in combined.items():
        steps_cal = day.get('calories_burned_from_steps', 0)
        workout_cal = day.get('calories_burned_from_workout', 0)
        day['total_calories_burned'] = steps_cal + workout_cal
        
    # # Grab calories burned from steps directly from Fitbit if available
    # calories_from_fitbit = int(combined[date]['calories_burned_from_steps'])
    # calories_from_workout = int(combined[date]['calories_burned_from_workout'])

    # # Total calories = steps + workout calories
    # combined[date]['total_calories_burned'] = calories_from_fitbit + calories_from_workout

    return dict(combined)

# ------------------------
# Main
# ------------------------
def main():
    fitbit_data_list = load_all_fitbit_data()
    hevy_workouts = load_hevy_workouts()
    combined = combine_fitbit_hevy(fitbit_data_list, hevy_workouts)

     # Sort combined dict by date
    combined_sorted = dict(sorted(combined.items(), key=lambda x: x[0]))

    os.makedirs('data', exist_ok=True)
    with open('data/combined_v5.json', 'w') as f:
        json.dump(combined_sorted, f, indent=2)

    print("Combined data saved to data/combined_v5.json")

if __name__ == "__main__":
    main()
