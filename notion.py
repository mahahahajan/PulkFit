# notion_client.py
import datetime
import json
import os
import time
from datetime import timedelta
from notion_client import Client

# ------------------------
# CONFIGURATION
# ------------------------
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")  # Must be set in GH Actions or local env

# Mapping your text block IDs in Notion to the data keys in averages.json
AVG_BLOCK_MAP = {
    "steps": "28eae2c9f8d68089bf20ef8f19e898b5",
    "resting_hr": "28eae2c9f8d68086ad06f0d58f9dafc0",
    "sleep": "28eae2c9f8d6808cb032c453b8d7905e",
    "workout_duration": "28eae2c9f8d680179be7c67e44307be2",
    "calories": "28eae2c9f8d68074a5f0dc2a7a7e2acf"
}

# ------------------------
# HELPER FUNCTIONS
# ------------------------
def format_workout(exercises):
    """Converts structured workout data into a Strava-style text summary."""
    from collections import defaultdict

    grouped = defaultdict(list)
    notes_map = {}

    for ex in exercises:
        name = ex["exercise"]
        grouped[name].append(ex)
        if ex.get("notes"):
            notes_map[name] = ex["notes"]

    lines = []
    for exercise, sets in grouped.items():
        lines.append(exercise)
        note = notes_map.get(exercise)
        if note:
            lines.append(f"\"{note}\"")
        for i, s in enumerate(sets, 1):
            reps = s.get("reps")
            weight = s.get("weight_lbs")
            if weight and weight != 0:
                lines.append(f"Set {i}: {int(weight)} lbs x {reps}")
            else:
                lines.append(f"Set {i}: {reps} reps")
        lines.append("")  # blank line

    return "\n".join(lines).strip()

def format_number(num):
    if num >= 1_000_000:
        return f"{round(num / 1_000_000, 1)}M"
    if num >= 1000:
        return f"{round(num / 1000, 1)}k"
    return str(int(num))

def format_hours_minutes(minutes):
    h = int(minutes // 60)
    m = int(round(minutes % 60))
    return f"{h} hr {m} min" if h else f"{m} min"

def format_sleep(hours):
    h = int(hours)
    m = int(round((hours - h) * 60))
    return f"{h} hr {m} min"

# ------------------------
# FILE LOADING
# ------------------------
def load_averages():
    repo_root = os.getcwd()
    path = os.path.join(repo_root, "data", "averages.json")
    with open(path, "r") as f:
        return json.load(f)

def load_combined_data():
    repo_root = os.getcwd()
    path = os.path.join(repo_root, "data", "combined_v5.json")
    with open(path, "r") as f:
        return json.load(f)

# ------------------------
# NOTION FUNCTIONS
# ------------------------
def create_metric_page(notion, date_str, name, metric_type, value):
    try:
        notion.pages.create(
            parent={"database_id": "28eae2c9f8d680198475d912c5b6ce4f"},
            properties={
                "Name": {"title": [{"text": {"content": name}}]},
                "Date": {"date": {"start": date_str}},
                "Metric Type": {"select": {"name": metric_type}},
                "Value": {"rich_text": [{"text": {"content": str(value)}}]},
            },
        )
        print(f"✅ Created: {name} ({date_str})")
    except Exception as e:
        print(f"❌ Failed to create {name} for {date_str}: {e}")

def extract_metrics(date_str, day_data):
    metrics = []
    print(f"Day data found was: {day_data}")

    steps = day_data.get("steps", 0)
    if steps:
        metrics.append(("Steps", f"🦶 {int(steps):,}", int(steps)))

    sleep_hours = day_data.get("sleep_hours", 0)
    if sleep_hours:
        metrics.append(("Sleep", f"🛏️ {format_sleep(sleep_hours)}", round(sleep_hours, 2)))

    calories = day_data.get("total_calories_burned", 0)
    if calories:
        metrics.append(("Calories", f"🔥 {format_number(int(calories))} cal", int(calories)))

    rhr = day_data.get("resting_heart_rate", 0)
    if rhr:
        metrics.append(("Heart Rate", f"💓 {int(rhr)} BPM", int(rhr)))

    bodyweight = day_data.get("bodyweight", 0)
    if bodyweight:
        metrics.append(("Weight", f"🍪 {float(bodyweight)} lbs", float(bodyweight)))

    duration = day_data.get("total_workout_duration", "0:00")
    workout = day_data.get("exercises", "")
    if duration != "0:00":
        metrics.append(("Workout", f"🏋 {duration}", format_workout(workout)))

    return metrics

# ------------------------
# PUSH FUNCTIONS
# ------------------------
def push_averages():
    notion = Client(auth=NOTION_API_KEY)
    averages = load_averages()

    updates = {
        AVG_BLOCK_MAP["steps"]: f"Average Daily Steps: {int(round(averages['avg_steps']))}",
        AVG_BLOCK_MAP["resting_hr"]: f"Average Resting Heart Rate: {int(round(averages['avg_resting_hr']))}",
        AVG_BLOCK_MAP["sleep"]: f"Average Sleep: {format_hours_minutes(averages['avg_sleep_hours']*60)}",
        AVG_BLOCK_MAP["workout_duration"]: f"Average Workout Duration: {format_hours_minutes(averages['avg_workout_duration_minutes'])}",
        AVG_BLOCK_MAP["calories"]: f"Average Calories Burned: {int(round(averages['avg_calories_burned']))}"
    }

    for block_id, text in updates.items():
        try:
            notion.blocks.update(
                block_id=block_id,
                paragraph={
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                }
            )
        except Exception as e:
            print(f"❌ Failed updating block {block_id}: {e}")

    print("✅ Averages successfully pushed to Notion!")

def push_all_metrics():
    notion = Client(auth=NOTION_API_KEY)
    combined = load_combined_data()

    for date_str, day_data in sorted(combined.items()):
        metrics = extract_metrics(date_str, day_data)
        for metric_type, name, value in metrics:
            create_metric_page(notion, date_str, name, metric_type, value)
            time.sleep(2)

    print("✅ Finished backfilling all metrics to Notion.")

def push_daily_metrics():
    notion = Client(auth=NOTION_API_KEY)
    combined = load_combined_data()
    today = (datetime.date.today() - timedelta(days=1)).isoformat()  # yesterday
    print(f"Push daily metrics for {today} ")

    if today not in combined:
        print(f"No data for today ({today}) in combined_v5.json")
        return
    
    # print(f"found combined to be {combined.popitem()}")

    metrics = extract_metrics(today, combined[today])
    for metric_type, name, value in metrics:
        create_metric_page(notion, today, name, metric_type, value)

    print(f"✅ Finished uploading today's metrics ({today}).")

def push_missing_metrics(input_date):
    notion = Client(auth=NOTION_API_KEY)
    combined = load_combined_data()
    start_date = datetime.date.fromisoformat(input_date)
    end_date = datetime.date.today()

    for i in range((end_date - start_date).days + 1):
        day = start_date + timedelta(days=i)
        day_str = str(day)
        if day_str not in combined:
            print(f"Date {day_str} not found")
            continue

        metrics = extract_metrics(day_str, combined[day_str])
        for metric_type, name, value in metrics:
            create_metric_page(notion, day_str, name, metric_type, value)
        print(f"✅ Finished uploading metrics for {day_str}")
