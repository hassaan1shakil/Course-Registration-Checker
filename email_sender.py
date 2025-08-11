import os
import smtplib
from email.mime.text import MIMEText

from dotenv import load_dotenv
load_dotenv()

EMAIL_ENABLED = os.environ.get("EMAIL_ENABLED", "True").lower() == "true"
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECIPIENTS = os.environ.get("EMAIL_RECIPIENTS")
if EMAIL_RECIPIENTS:
    EMAIL_RECIPIENTS = [email.strip() for email in EMAIL_RECIPIENTS.split(",") if email.strip()]
else:
    EMAIL_RECIPIENTS = []

def send_email(subject, body):
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = ", ".join(EMAIL_RECIPIENTS)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, EMAIL_RECIPIENTS, msg.as_string())

        print(f"✅ Email sent to: {', '.join(EMAIL_RECIPIENTS)}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

if __name__ == "__main__":
    send_email("📧 Test Email from Python", "Hello! This is a test email to verify SMTP settings.")
