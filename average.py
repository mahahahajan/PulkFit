import json
import os

# ------------------------
# Global variables
# ------------------------
steps_arr = []
resting_hr_arr = []
sleep_hours_arr = []
workout_durations_arr = []
total_calories_arr = []

avg_steps = 0
avg_hr = 0
avg_sleep = 0
avg_workout_minutes = 0
avg_calories = 0

# ------------------------
# Helper functions
# ------------------------
def safe_avg(values):
    filtered = [v for v in values if v > 0]
    return sum(filtered) / len(filtered) if filtered else 0

def load_arrays(data):
    for date, info in data.items():
        steps = info.get("steps", 0)
        rhr = info.get("resting_heart_rate", 0)
        sleep_hours = info.get("sleep_hours", 0)
        calories = info.get("total_calories_burned", 0)
        workout_duration_str = info.get("total_workout_duration", "0:00")

        if steps > 0:
            steps_arr.append(steps)
        if rhr > 0:
            resting_hr_arr.append(rhr)
        if sleep_hours > 0:
            sleep_hours_arr.append(sleep_hours)
        if calories > 0 and info.get('calories_burned_from_steps', 0) != 0:
            total_calories_arr.append(calories)

        # Convert workout duration to minutes
        if workout_duration_str != "0:00":
            h, m = map(int, workout_duration_str.split(":"))
            total_minutes = h * 60 + m
            if total_minutes > 0:
                workout_durations_arr.append(total_minutes)

def compute_averages():
    global avg_steps, avg_hr, avg_sleep, avg_workout_minutes, avg_calories

    avg_steps = safe_avg(steps_arr)
    avg_hr = safe_avg(resting_hr_arr)
    avg_sleep = safe_avg(sleep_hours_arr)
    avg_workout_minutes = safe_avg(workout_durations_arr)
    avg_calories = safe_avg(total_calories_arr)

def print_values():
    hours = int(avg_workout_minutes // 60)
    minutes = int(avg_workout_minutes % 60)
    avg_workout_duration = f"{hours} hr {minutes} min"
    print("Averages across valid days:")
    print(f"- Steps: {avg_steps:.0f}")
    print(f"- Resting HR: {avg_hr:.1f} bpm")
    print(f"- Sleep Duration: {avg_sleep:.2f} hours")
    print(f"- Workout Duration: {avg_workout_duration}")
    print(f"- Calories Burned: {avg_calories:.0f}")

# ------------------------
# Main
# ------------------------
def get_averages():
    repo_root = os.getcwd()
    combined_file = os.path.join(repo_root, "data", "combined_v5.json")
    averages_file = os.path.join(repo_root, "data", "averages.json")

    with open(combined_file, "r") as f:
        combined_data = json.load(f)

    load_arrays(combined_data)
    compute_averages()
    print_values()

    averages = {
        "avg_steps": avg_steps,
        "avg_resting_hr": avg_hr,
        "avg_sleep_hours": avg_sleep,
        "avg_workout_duration_minutes": avg_workout_minutes,
        "avg_calories_burned": avg_calories
    }

    os.makedirs(os.path.dirname(averages_file), exist_ok=True)
    with open(averages_file, "w") as f:
        json.dump(averages, f, indent=2)

if __name__ == "__main__":
    get_averages()
