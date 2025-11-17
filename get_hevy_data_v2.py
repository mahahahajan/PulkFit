#!/usr/bin/env python3
import os
import time
import csv
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from send2trash import send2trash

# -----------------------------
# CONFIG
# -----------------------------
HEVY_EMAIL = os.environ.get("HEVY_EMAIL")
HEVY_PASSWORD = os.environ.get("HEVY_PASSWORD")

# GitHub Actions cannot rely on ~/Downloads
REPO_ROOT = os.getcwd()
DOWNLOAD_DIR = os.path.join(REPO_ROOT, "temp_downloads")
CSV_FILE_NAME = "workouts.csv"  # after export
OUTPUT_JSON = os.path.join(REPO_ROOT, "data", "hevy_daily_data", "hevy_data_v3.json")

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)

# -----------------------------
# Selenium: Log in & Export
# -----------------------------
def download_hevy_csv():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "safebrowsing.enabled": True
    })

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://hevy.com/login?utm_source=hevyapp.com&utm_medium=menu")
    wait = WebDriverWait(driver, 15)

    email_input = wait.until(lambda d: find_email_input(d))
    password_input = wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "input[type='password']"))

    email_input.clear()
    email_input.send_keys(HEVY_EMAIL)
    password_input.clear()
    password_input.send_keys(HEVY_PASSWORD)

    login_button = wait.until(lambda d: find_login_button(d))
    if login_button is None:
        raise Exception("Login button not found")
    login_button.click()
    time.sleep(5)

    # Export CSV
    driver.get("https://hevy.com/settings?export")
    time.sleep(3)
    button = driver.find_element(By.XPATH, "//button[.//p[text()='Export Workout Data']]")
    driver.execute_script("arguments[0].scrollIntoView(true);", button)
    driver.execute_script("arguments[0].click();", button)

    print("Clicked export CSV button, waiting for download...")

    download_path = os.path.join(DOWNLOAD_DIR, CSV_FILE_NAME)
    timeout = 30
    while timeout > 0:
        if os.path.exists(download_path):
            print(f"CSV downloaded to {download_path}")
            break
        time.sleep(1)
        timeout -= 1
    else:
        raise RuntimeError("CSV download timed out")

    driver.quit()
    return download_path

# -----------------------------
# CSV Parsing
# -----------------------------
def parse_hevy_csv(csv_path):
    workouts_by_date = {}
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            workout_date = datetime.strptime(row["start_time"], "%d %b %Y, %H:%M").strftime("%Y-%m-%d")
            start_dt = datetime.strptime(row["start_time"], "%d %b %Y, %H:%M")
            end_dt = datetime.strptime(row["end_time"], "%d %b %Y, %H:%M")
            duration_sec = (end_dt - start_dt).total_seconds()
            hours = int(duration_sec // 3600)
            minutes = int((duration_sec % 3600) // 60)
            duration_str = f"{hours}:{minutes:02d}"

            if workout_date not in workouts_by_date:
                workouts_by_date[workout_date] = {
                    "Date": workout_date,
                    "Workout_Title": row["title"],
                    "Workout_Duration": duration_str,
                    "exercises": []
                }

            workouts_by_date[workout_date]["exercises"].append({
                "exercise": row["exercise_title"],
                "set_type": row["set_type"],
                "weight_lbs": row["weight_lbs"] or None,
                "reps": row["reps"] or None,
                "distance_miles": row["distance_miles"] or None,
                "duration_seconds": row["duration_seconds"] or None,
                "rpe": row["rpe"] or None,
                "notes": row["exercise_notes"] or ""
            })

    return list(workouts_by_date.values())

# -----------------------------
# Helpers
# -----------------------------
def find_email_input(driver):
    locators = [
        (By.XPATH, "//input[@placeholder='Email or username']"),
        (By.XPATH, "//input[@type='email']"),
        (By.XPATH, "//form//input[1]")
    ]
    for by, selector in locators:
        try:
            el = driver.find_element(by, selector)
            if el.is_displayed():
                return el
        except:
            continue
    raise Exception("Email input not found")

def find_login_button(driver):
    buttons = driver.find_elements(By.XPATH, "//button[.//p[text()='Login']]")
    for b in buttons:
        if b.is_displayed() and b.is_enabled():
            return b
    return None

# -----------------------------
# JSON Merge Logic
# -----------------------------
def merge_existing_data(existing_file, new_workouts):
    if os.path.exists(existing_file):
        with open(existing_file) as f:
            existing = json.load(f)
    else:
        existing = []

    existing_dates = {w["Date"]: w for w in existing}
    for w in new_workouts:
        if w["Date"] not in existing_dates:
            existing.append(w)

    existing.sort(key=lambda x: x["Date"])
    with open(existing_file, 'w') as f:
        json.dump(existing, f, indent=2)

    print(f"Updated {existing_file} with {len(new_workouts)} new entries. Total workouts stored: {len(existing)}")

# -----------------------------
# Main
# -----------------------------
def main():
    csv_path = download_hevy_csv()
    new_workouts = parse_hevy_csv(csv_path)

    merge_existing_data(OUTPUT_JSON, new_workouts)

    # Delete CSV after processing
    send2trash(csv_path)

if __name__ == "__main__":
    main()
