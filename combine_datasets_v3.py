import os
import json
from collections import defaultdict
import datetime

# ------------------------
# Muscle group mapping
# ------------------------
EXERCISE_TO_MUSCLE = {
    "Pull Up": ["Back"],
    "Pull Up (Assisted)": ["Back"],
    "Neutral Grip Pull Up": ["Back", "Forearm"],
    "Neutral Grip Pull Up (Assisted)": ["Back", "Forearm"],
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
    "Overhead Press": ["Shoulders"],
    "Overhead Press (Barbell)": ["Shoulders"],
    "Overhead Press (Smith Machine)": ["Shoulders"],
    "Shoulder Press (Dumbbell)": ["Shoulders"],
    "Seated Shoulder Press (Machine)": ["Shoulders"],
    "Chest Dip": ["Chest", "Triceps", "Shoulders"],
    "Chest Dip (Assisted)": ["Chest", "Triceps", "Shoulders"],
    "Push Up": ["Chest", "Triceps", "Shoulders"],
    "Face Pull": ["Rear Delts", "Traps"],
    "Triceps Extension (Barbell)": ["Triceps"],
    "Triceps Extension (Cable)": ["Triceps"],
    "Triceps Rope Pushdown": ["Triceps"],
    "Overhead Triceps Extension (Cable)": ["Triceps"],
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

# Rough MET values per exercise
EXERCISE_TO_MET = {
    "Pull Up": 8, "Pull Up (Assisted)": 6, "Chin Up": 8, "Chin Up (Assisted)": 6,
    "Bent Over Row (Barbell)": 6, "Seated Row (Machine)": 5.5, "Lat Pulldown (Cable)": 5.5,
    "Lat Pulldown - Close Grip (Cable)": 5.5, "lat pulldown Burn Outs": 5.5, "Negative Pull Up": 7,
    "Bench Press": 6, "Incline Bench Press": 6, "Incline Bench Press (Barbell)": 6, 
    "Incline Bench Press (Dumbbell)": 6, "Overhead Press": 5.5, "Overhead Press (Barbell)": 5.5,
    "Overhead Press (Smith Machine)": 5.5, "Shoulder Press (Dumbbell)": 5.5, 
    "Seated Shoulder Press (Machine)": 5, "Chest Dip": 6, "Chest Dip (Assisted)": 5, "Push Up": 5.5,
    "Face Pull": 4.5, "Triceps Extension (Barbell)": 4, "Triceps Extension (Cable)": 4,
    "Triceps Rope Pushdown": 4, "Hammer Curl (Dumbbell)": 4, "Bicep Curl (Barbell)": 4,
    "EZ Bar Biceps Curl": 4, "Bicep Curl (Cable)": 4, "Reverse Curl (Barbell)": 4,
    "Lateral Raise (Dumbbell)": 3.5, "Single Arm Lateral Raise (Cable)": 3.5,
    "Lateral Raise (Cable)": 3.5, "Rear Delt Reverse Fly (Machine)": 4,
    "Squat": 7, "Squat (Barbell)": 7, "Front Squat": 7, "Leg Press Horizontal (Machine)": 6.5,
    "Bulgarian Split Squat": 6.5, "Deadlift": 7, "Deadlift (Barbell)": 7, "Romanian Deadlift (Barbell)": 6.5,
    "Hip Thrust (Barbell)": 6, "Hanging Knee Raise": 3.5, "Leg Raise Parallel Bars": 3.5
}

LB_TO_KG = 0.453592

# ------------------------
# Helpers
# ------------------------
def estimate_exercise_calories(exercise, weight_lbs, reps, duration_seconds=None, user_weight_lbs=160):
    MET = EXERCISE_TO_MET.get(exercise, 5)
    weight_kg = user_weight_lbs * LB_TO_KG
    duration_minutes = (reps * 3) / 60 if not duration_seconds else duration_seconds / 60
    calories = MET * 3.5 * weight_kg / 200 * duration_minutes
    return calories

# ------------------------
# Load data (GitHub Actions paths)
# ------------------------
REPO_ROOT = os.getcwd()
FITBIT_JSON = os.path.join(REPO_ROOT, "data", "fitbit_daily_data", "fitbit_combined.json")
HEVY_JSON = os.path.join(REPO_ROOT, "data", "hevy_daily_data", "hevy_data_v3.json")
OUTPUT_JSON = os.path.join(REPO_ROOT, "data", "combined_v5.json")

def load_fitbit_data(file=FITBIT_JSON):
    with open(file) as f:
        return json.load(f)

def load_hevy_workouts(file=HEVY_JSON):
    with open(file) as f:
        return json.load(f)

# ------------------------
# Combine datasets
# ------------------------
def combine_fitbit_hevy(fitbit_data, hevy_workouts, user_weight_lbs=160):
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
        "calories_burned_from_steps": 0,
        "resting_heart_rate": 0,
        "bodyweight": 0,
    })

    # --------- Fitbit ----------
    for date, data in fitbit_data.items():
        combined[date]["steps"] = int(data.get("steps_activities-steps", 0))
        combined[date]["distance"] = float(data.get("distance_activities-distance", 0.0))
        combined[date]["calories_burned_from_steps"] = int(data.get("calories_out_activities-calories", 0))
        combined[date]["sleep_hours"] = data.get("sleep_duration", 0) / 1000 / 60 / 60
        combined[date]["sleep_score"] = data.get("sleep_efficiency", None)
        heart_info = data.get("heart_activities-heart") or {}
        combined[date]["resting_heart_rate"] = int(heart_info.get("restingHeartRate") or 0)
        combined[date]["bodyweight"] = float(data.get('weight_body-weight', 0.0))

    # --------- Hevy ----------
    for workout in hevy_workouts:
        date = workout["Date"]
        combined[date]["workout_title"] = workout.get("Workout_Title")
        combined[date]["total_workout_duration"] = workout.get("Workout_Duration", "0:00")
        combined[date]["exercises"] = []

        total_workout_calories = 0
        for e in workout.get("exercises", []):
            weight = float(e.get("weight_lbs") or 0)
            reps = int(e.get("reps") or 0)
            duration_seconds = int(e.get("duration_seconds") or 0)
            exercise_name = e.get("exercise", "")
            notes = e.get("notes", "")

            # Expand weight
            actual_weight = weight
            if "barbell" in exercise_name.lower():
                actual_weight = 2 * weight + 45
            elif "assisted" in exercise_name.lower():
                actual_weight = user_weight_lbs - weight
            elif "smith" in exercise_name.lower() or "smith" in notes.lower():
                actual_weight = 2 * weight
            elif "pull up" in exercise_name.lower() or "chest dip" in notes.lower():
                actual_weight = user_weight_lbs

            calories = estimate_exercise_calories(exercise_name, actual_weight, reps, duration_seconds, user_weight_lbs)
            total_workout_calories += calories

            muscle_groups = EXERCISE_TO_MUSCLE.get(exercise_name, [])
            if muscle_groups == []: 
                print(f"No muscle group found for {exercise_name}")

            combined[date]["exercises"].append({
                "exercise": exercise_name,
                "set_type": e.get("set_type", ""),
                "weight_lbs": actual_weight,
                "reps": reps or None,
                "distance": float(e.get("distance") or 0) or None,
                "notes": notes,
                "muscle_groups": muscle_groups
            })

        combined[date]["calories_burned_from_workout"] = int(total_workout_calories)

    # --------- Total calories ----------
    for day in combined.values():
        day["total_calories_burned"] = day.get("calories_burned_from_steps", 0) + day.get("calories_burned_from_workout", 0)

    return dict(sorted(combined.items()))

# ------------------------
# Main
# ------------------------
def main():
    
    fitbit_data = load_fitbit_data()
    hevy_workouts = load_hevy_workouts()
    print(f"Today's date in UTC: {datetime.date.today()}")
    print(f"Fitbit CSV date range: {list(fitbit_data.keys())[:5]} ... {list(fitbit_data.keys())[-5:]}")

    combined = combine_fitbit_hevy(fitbit_data, hevy_workouts)

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(combined, f, indent=2)

    print(f"Combined data saved to {OUTPUT_JSON}")
    print(f"{combined.popitem()}")

if __name__ == "__main__":
    main()
