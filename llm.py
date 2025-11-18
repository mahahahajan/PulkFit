import json
import os
from openai import OpenAI
import re
import datetime

# ----------------------------
# PATH HELPERS
# ----------------------------
def repo_path(*paths):
    """Return repo-relative path for GitHub Actions or local usage."""
    return os.path.join(os.getcwd(), *paths)

# ----------------------------
# CONFIG / FILE PATHS
# ----------------------------
SYSTEM_PROMPT_FILE = repo_path("prompts", "systemPrompt.md")       # persona + daily instructions
STABLE_PROFILE_FILE = repo_path("prompts", "stableProfile.md")     # long-term goals, training preferences
PAYLOAD_FILE = repo_path("data", "llm_payload.json")              # last N workouts + daily metrics
OUTPUT_FILE = repo_path("temp", "llm_response.json")              # save generated plan

# ----------------------------
# HELPER: read file
# ----------------------------
def read_file(file_path):
    with open(file_path, "r") as f:
        return f.read()

# ----------------------------
# HELPER: load JSON payload
# ----------------------------
def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

# ----------------------------
# BUILD USER PROMPT
# ----------------------------
def build_user_prompt(payload, stable_profile):
    sleep_details = payload.get('sleep_last_night', {})
    bodyweight = payload.get('bodyweight', 'N/A')
    recent_workouts = payload.get('recent_workouts', {})
    last_workout_summary = payload.get('last_workout_summary', {})
    week_volume = payload.get('week_volume', {})
    todays_date = datetime.date.today()

    user_prompt = f"""
Stable Profile:
{stable_profile}

Daily Metrics:
- Sleep: {sleep_details.get('hours', 'N/A')} hours, {sleep_details.get("score", "N/A")}
- Resting Heart Rate: {sleep_details.get('resting_hr', 'N/A')}
- Bodyweight: {bodyweight} lbs


Week Volume:
{week_volume}

Recent Workouts:
{recent_workouts}

Last Workout:
{last_workout_summary}

Today's date:
{todays_date}


Please generate today's workout plan, step goal, and macros.
"""
    return user_prompt

# ----------------------------
# CALL OPENAI
# ----------------------------
def get_daily_plan_with_gemini(system_prompt: str, user_prompt: str, model: str = "gemini-2.5-flash"):
    client = OpenAI(
        api_key=os.environ.get("GEMINI_AI_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        tools=[{"type": "web_search"}]
    )

    output = response.output_text
    if not output:
        raise RuntimeError("No output from model")

    return output

# ----------------------------
# RUN LLM
# ----------------------------
def run_llm():
    # Read inputs
    system_prompt = read_file(SYSTEM_PROMPT_FILE)
    stable_profile = read_file(STABLE_PROFILE_FILE)
    payload = load_json(PAYLOAD_FILE)

    # Build prompt
    user_prompt = build_user_prompt(payload, stable_profile)
    print("\n=== USER PROMPT ===\n")
    print(user_prompt)

    # Get AI-generated daily plan
    daily_plan = get_daily_plan_with_gemini(system_prompt, user_prompt)
    print("\n=== DAILY PLAN OUTPUT ===\n")
    print(daily_plan)
    
    # Clean output and parse JSON
    cleaned_text = re.sub(r"^json\s*|\s*$", "", daily_plan.strip(), flags=re.MULTILINE)
    cleaned_text = cleaned_text.replace("```json", "").replace("```", "").strip()
    print("Cleaned text")
    print(cleaned_text)

    plan = json.loads(cleaned_text)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w+") as f:
        json.dump(plan, f, indent=2)

# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    run_llm()
