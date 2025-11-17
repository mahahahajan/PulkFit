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
from selenium.webdriver.support import expected_conditions as EC

# -----------------------------
# CONFIG
# -----------------------------
HEVY_EMAIL = "pulkrewards@gmail.com"
HEVY_PASSWORD = "vrpm2281"
DOWNLOAD_DIR = os.path.expanduser("~/Downloads")
CSV_FILE_NAME = "workouts (2).csv"  # name of the CSV after download
OUTPUT_JSON = "data/hevy_daily_data/hevy_data.json"

# -----------------------------
# Selenium: Log in & Export
# -----------------------------
def download_hevy_csv():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # run without opening browser
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "safebrowsing.enabled": True
    })

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://hevy.com/login?utm_source=hevyapp.com&utm_medium=menu")

    # Log in
    wait = WebDriverWait(driver, 15)  # give it a bit more time for React to render

    # Email input
    email_input = wait.until(lambda d: find_email_input(d))

    # Password input
    password_input = wait.until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "input[type='password']")
        )
    )

    email_input.clear()
    email_input.send_keys(HEVY_EMAIL)
    password_input.clear()
    password_input.send_keys(HEVY_PASSWORD)

    login_xpaths = [
        "//button[contains(text(), 'Login')]",
        "//button[contains(text(), 'Login')]",  # div styled as button
        "//button[.//p[text()='Login']]",
        "//button[.//p[text()='Login']]"
    ]

    login_button = None
    # Wait until the button exists and is clickable
    login_button = wait.until(lambda d: find_login_button(d))

    if login_button is None:
        raise Exception("Login button not found")

    login_button.click()
    time.sleep(5)  # wait for login to complete

    # Go to export page
    driver.get("https://hevy.com/settings?export")
    time.sleep(3)

    # Click the export CSV button
    buttons = driver.find_element(By.XPATH, "//button[.//p[text()='Export Workout Data']]")
    buttons.click()
    print("Clicked export CSV button, waiting for download...")

    # Wait for CSV to appear in downloads
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
    workouts = []
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert start_time like '9 Oct 2025, 17:55' to YYYY-MM-DD
            workout_date = datetime.strptime(row["start_time"], "%d %b %Y, %H:%M").strftime("%Y-%m-%d")
            
            workouts.append({
                "date": workout_date,
                "title": row["title"],
                "exercise": row["exercise_title"],
                "set_type": row["set_type"],
                "weight_lbs": row["weight_lbs"],
                "reps": row["reps"],
                "distance_miles": row["distance_miles"],
                "duration_seconds": row["duration_seconds"],
                "rpe": row["rpe"],
                "notes": row["exercise_notes"]
            })
    return workouts

def find_email_input(driver):
    # Try multiple ways to locate email input
    locators = [
        (By.XPATH, "//input[@placeholder='Email or username']"),
        (By.XPATH, "//input[@type='email']"),
        (By.XPATH, "//form//input[1]")  # first input in login form
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
    # Look for any button containing a <p> with text "Login"
    buttons = driver.find_elements(By.XPATH, "//button[.//p[text()='Login']]")
    for b in buttons:
        if b.is_displayed() and b.is_enabled():
            return b
    return None

# -----------------------------
# Main
# -----------------------------
def main():
    # 1. Download latest CSV
    csv_path = download_hevy_csv()

    # 2. Parse CSV into JSON
    workouts = parse_hevy_csv(csv_path)

    # 3. Save JSON
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(workouts, f, indent=2)
    print(f"Saved {len(workouts)} workouts to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()