import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from plyer import notification

# --- Config ---
LOGIN_URL = "https://flexstudent.nu.edu.pk/Login"
KEYWORD = "credit"  # Text that indicates registration is open
CHECK_INTERVAL = 30  # Seconds between checks
LOG_FILE = "registration_checker.log"
PROFILE_PATH = os.path.expanduser("~/.config/selenium-profile")
SOUND_PATH = os.path.abspath("alert-sound.mp3")

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
    while True:
        try:
            driver.get(registration_url)
            time.sleep(3)

            page_text = driver.page_source.lower()

            if KEYWORD.lower() in page_text:
                msg = "✅ Registration is now OPEN!"
                logging.info(msg)
                send_notification("📚 Course Registration", msg)
                play_sound()
                break
            else:
                logging.info("Registration still closed. Retrying...")
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
