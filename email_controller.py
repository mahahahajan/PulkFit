import json
import smtplib
from email.message import EmailMessage

def send_email_html(
    subject: str,
    html_body: str,
    to_email: str,
    from_email: str,
    smtp_server: str,
    smtp_port: int,
    username: str,
    password: str
):
    """
    Sends an HTML email using standard SMTP.
    Inserts both plain text fallback + HTML body.
    """

    # Create the email message
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    # Plain text fallback so your email doesn't look cursed in old clients
    plain_text = "Your device doesn't support HTML email. Please view this on a modern client."

    # Add both versions
    msg.set_content(plain_text)
    msg.add_alternative(html_body, subtype="html")

    # Send the email
    with smtplib.SMTP_SSL(smtp_server, smtp_port) as smtp:
        smtp.login(username, password)
        smtp.send_message(msg)

def render_workout_email(plan_json):
    """
    Converts the GPT workout JSON into a clean HTML email string.
    Expected keys:
    - day_focus
    - main_lifts
    - accessories
    - conditioning
    - warmup
    - notes
    """

    def list_to_html(items):
        if not items:
            return "<li>None</li>"
        return "".join(f"<li>{item}</li>" for item in items)

    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px; color: #222;">
        
        <h2>🏋️ Today's Workout</h2>
        <p style="color: #666;">Automatically generated</p>

        <h3>Focus: {plan_json.get("day_focus", "N/A")}</h3>

        <h3>Main Lifts</h3>
        <ul>{list_to_html(plan_json.get("main_lifts", []))}</ul>

        <h3>Accessories</h3>
        <ul>{list_to_html(plan_json.get("accessories", []))}</ul>

        <h3>Conditioning</h3>
        <ul>{plan_json.get("conditioning", [])}</ul>

        <h3>Warmup</h3>
        <ul>{list_to_html(plan_json.get("warmup", []))}</ul>

        <h3>Notes</h3>
        <p style="white-space: pre-wrap;">{plan_json.get("notes", "")}</p>

      </body>
    </html>
    """
    return html

if __name__ == "__main__":
    with open('temp/llm_response.json', 'r') as f:
        ai_plan = json.load(f)
    html_body = render_workout_email(ai_plan)
    print(html_body)
    send_email_html(
        subject="Today's Workout Plan",
        html_body=html_body,
        to_email="pulkit8.mahajan@gmail.com",
        from_email="yourbot@example.com",
        smtp_server="smtp.gmail.com",
        smtp_port=465,
    )