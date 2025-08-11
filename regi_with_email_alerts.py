import os
import time
import logging
import smtplib
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from plyer import notification

from dotenv import load_dotenv
load_dotenv()

LOGIN_URL = os.environ.get("LOGIN_URL")
KEYWORD = os.environ.get("KEYWORD")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 30))
ALERT_COOLDOWN = int(os.environ.get("ALERT_COOLDOWN", 60))
LOG_FILE = os.environ.get("LOG_FILE", "registration_checker.log")
PROFILE_PATH = os.environ.get("PROFILE_PATH", os.path.expanduser("~/.config/selenium-profile"))
SOUND_PATH = os.environ.get("SOUND_PATH", os.path.abspath("alert-sound.mp3"))

# --- Email Config ---
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

# --- Logging Setup ---
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s — %(levelname)s — %(message)s'
)

# --- Functions ---

def init_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument(f"--user-data-dir={PROFILE_PATH}")
    return webdriver.Chrome(options=options)

def send_notification(title, message):
    notification.notify(
        title=title,
        message=message,
        timeout=10
    )

def send_email(subject, body):
    if not EMAIL_ENABLED:
        return
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = ", ".join(EMAIL_RECIPIENTS)  # for display in inbox

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, EMAIL_RECIPIENTS, msg.as_string())
        
        logging.info(f"Email notification sent to: {', '.join(EMAIL_RECIPIENTS)}")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

def play_sound():
    if os.path.exists(SOUND_PATH):
        os.system(f'aplay \"{SOUND_PATH}\"')
    else:
        logging.warning("Sound file not found. Skipping.")

def wait_for_manual_login_and_navigation(driver):
    print("🔐 Opening login page...")
    driver.get(LOGIN_URL)

    input(
        "\n⚠️ Please log in manually, solve CAPTCHA, and navigate to the registration page.\n"
        "✅ Once you're on the page with 'dump=...' in the URL, press Enter to continue...\n"
    )

    current_url = driver.current_url
    if "dump=" not in current_url:
        logging.error("URL does not contain expected 'dump=' token.")
        raise Exception("❌ Invalid registration page. Did you forget to navigate there?")
    
    logging.info(f"Captured dynamic registration URL: {current_url}")
    return current_url

def auto_check_loop(driver, registration_url, interval=CHECK_INTERVAL):
    logging.info(f"Starting auto-check loop every {interval} seconds.")
    last_alert_time = 0

    while True:
        try:
            driver.get(registration_url)
            time.sleep(3)

            page_text = driver.page_source.lower()

            if KEYWORD.lower() in page_text:
                now = time.time()
                if now - last_alert_time >= ALERT_COOLDOWN:
                    msg = "✅ Registration is now OPEN!"
                    logging.info(msg)
                    send_notification("📚 Course Registration", msg)
                    send_email("📚 Course Registration Alert", msg)
                    play_sound()
                    last_alert_time = now
                else:
                    logging.info("Registration open, alert suppressed (cooldown).")
            else:
                logging.info("Registration still closed.")

            time.sleep(interval)

        except Exception as e:
            logging.error(f"Error during check: {e}")
            time.sleep(interval)

def main():
    logging.info("Script started.")
    driver = init_driver()

    try:
        registration_url = wait_for_manual_login_and_navigation(driver)
        auto_check_loop(driver, registration_url)
    finally:
        input("Press Enter to close the browser...")
        driver.quit()
        logging.info("Script ended.")

if __name__ == "__main__":
    main()