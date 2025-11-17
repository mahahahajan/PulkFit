import os
import json
import base64
import datetime
from email.message import EmailMessage
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# ----------------------------
# PATH HELPERS
# ----------------------------
def repo_path(*paths):
    """Return repo-relative path for GitHub Actions or local usage."""
    return os.path.join(os.getcwd(), *paths)

TOKEN_PATH = repo_path("auth_details", "token.json")
CREDS_PATH = repo_path("auth_details", "credentials.json")
LLM_RESPONSE_FILE = repo_path("temp", "llm_response.json")

# ----------------------------
# LOAD SECRETS FROM ENV
# ----------------------------
GMAIL_CREDENTIALS_JSON = os.environ.get("GMAIL_CREDENTIALS")
GMAIL_TOKEN_JSON = os.environ.get("GMAIL_TOKEN")

# ----------------------------
# GENERATE HTML EMAIL
# ----------------------------
def generate_html_email(workout_json):
    focus = workout_json.get("day_focus", "Full Body")
    notes = workout_json.get("notes", "")
    warmup = workout_json.get("warmup", [])
    main_lifts = workout_json.get("main_lifts", [])
    accessories = workout_json.get("accessories", [])
    conditioning = workout_json.get("conditioning", "")

    warmup_html = "".join(f"<li>{item}</li>" for item in warmup)

    main_lifts_html = ""
    for lift in main_lifts:
        main_lifts_html += f"""
        <p><strong>{lift.get("exercise")}</strong><br>
        Sets × Reps: {lift.get("sets")}×{lift.get("reps_range","")}<br>
        Weight / Assistance: {lift.get("target_weight_lbs", lift.get("assistance_lbs",""))}<br>
        RPE: {lift.get("rpe_range","")}<br>
        Notes: {lift.get("notes","")}</p>
        """

    accessories_html = ""
    for acc in accessories:
        accessories_html += f"""
        <p><strong>{acc.get("exercise")}</strong><br>
        Sets × Reps: {acc.get("sets")}×{acc.get("reps_range","")}<br>
        Weight: {acc.get("target_weight_lbs","")}<br>
        RPE: {acc.get("rpe_range","")}<br>
        Notes: {acc.get("notes","")}</p>
        """

    html = f"""
    <html>
    <body>
        <h2>Today's Workout</h2>
        <h3>Focus</h3><p>{focus}</p>

        <h3>Notes</h3><p>{notes}</p>

        <h3>Warm Up</h3><ul>{warmup_html}</ul>

        <h3>Main Lifts</h3>{main_lifts_html}

        <h3>Accessories</h3>{accessories_html}

        <h3>Conditioning</h3><p>{conditioning}</p>
    </body>
    </html>
    """
    return html

# ----------------------------
# LOAD CREDENTIALS
# ----------------------------
def load_creds():
    creds_data = json.loads(GMAIL_TOKEN_JSON)
    return Credentials(
        token=creds_data.get("token"),
        refresh_token=creds_data.get("refresh_token"),
        token_uri=creds_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=creds_data.get("client_id"),
        client_secret=creds_data.get("client_secret"),
        scopes=SCOPES,
    )

# ----------------------------
# SEND EMAIL
# ----------------------------
def send_email(to_email, subject, html_body, from_email="test@gmail.com"):
    creds = load_creds()
    service = build("gmail", "v1", credentials=creds)

    msg = EmailMessage()
    msg["To"] = to_email
    msg["From"] = from_email
    msg["Subject"] = subject
    msg.set_content("Your client doesn't support HTML.")
    msg.add_alternative(html_body, subtype="html")

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    return service.users().messages().send(
        userId="me",
        body={"raw": raw}
    ).execute()

# ----------------------------
# CREATE AND SEND EMAIL
# ----------------------------
def create_and_send_email():
    # Load AI-generated plan from GitHub Actions path
    with open(LLM_RESPONSE_FILE, 'r') as f:
        ai_plan = json.load(f)

    html_body = generate_html_email(ai_plan)
    print(html_body)

    # Send email
    send_email(
        to_email="pulkit8.mahajan@gmail.com",
        subject=f"Workout {datetime.date.today()}",
        html_body=html_body
    )

# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    create_and_send_email()
