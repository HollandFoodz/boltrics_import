import os
import logging
from dotenv import load_dotenv
from boltrics_import.mail import mail
from playwright.sync_api import sync_playwright
from shutil import copy
from io import StringIO

LOGIN_URL = "https://bakker-logistiek-iw9.nekovri-dynamics.nl/en-us/welcome.aspx"
VOORRAAD_URL = "https://bakker-logistiek-iw9.nekovri-dynamics.nl/Lists/tabid/2379/list/PIJN_001/modid/3695/language/en-US/Default.aspx?title=%5cA.+Voorraad+per+artikel"

CWD = os.path.dirname(os.path.realpath(__file__))
ARCHIVE_DIR = os.path.join(CWD, "csv")
DESTINATION = "Z:\\_Dashboard\\Databases\\bakker.csv"

# Create an in-memory StringIO object to capture logs for email
log_stream = StringIO()

# Create logging handlers
file_handler = logging.FileHandler("boltrics.log")
stream_handler = logging.StreamHandler(log_stream)

# Set up logging configuration to capture all log levels and output to both file and stream
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[file_handler, stream_handler]
)

def get_csv(USERNAME, PASSWORD):
    logging.info("Fetching CSV file from Boltrics")

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # Login
        page.goto(LOGIN_URL)

        # Wait for the input fields to be visible
        page.wait_for_selector("input#dnn_ctr3692_Login_Login_DNN_txtUsername", timeout=2000)
        page.fill("input#dnn_ctr3692_Login_Login_DNN_txtUsername", USERNAME)
        page.fill("input#dnn_ctr3692_Login_Login_DNN_txtPassword", PASSWORD)

        # Wait until the login button is enabled and visible, then click
        page.evaluate("""__doPostBack('dnn$ctr3692$Login$Login_DNN$cmdLogin','')""")

        # Optional: wait for navigation or some element on the next page to appear
        page.wait_for_load_state("networkidle")

        # Navigate to data page
        page.goto(VOORRAAD_URL)
        page.wait_for_load_state("networkidle")

        # Start download
        with page.expect_download() as download_info:
            page.evaluate("""__doPostBack('dnn$ctr3694$Viewer$bolList$bolRadGrid$rdgList$ctl00$ctl02$ctl00$LinkButton1','')""")

        download = download_info.value
        filepath = os.path.join(ARCHIVE_DIR, download.suggested_filename)
        download.save_as(filepath)
        logging.info(f"Downloaded CSV to archive: {filepath}")
        context.close()
        browser.close()
        return filepath

# Function to get all logs from the in-memory stream
def get_all_logs():
    logs = log_stream.getvalue().strip()
    return logs

if __name__ == "__main__":
    load_dotenv(verbose=True)

    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)

    USERNAME = os.getenv("BOLTRICS_USERNAME")
    PASSWORD = os.getenv("BOLTRICS_PASSWORD")

    SMTP_SERVER = os.getenv("SMTP_SERVER")
    FROM_EMAIL = os.getenv("FROM_EMAIL")
    RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
    SENDER_USERNAME = os.getenv("SENDER_EMAIL")
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

    try:
        csv_filepath = get_csv(USERNAME, PASSWORD)
        copy(csv_filepath, DESTINATION)
        logging.info(f"Bakker data updated to {DESTINATION}")
        exit_code = 0
    except Exception as e:
        logging.error("An import from the Boltrics (Zeewolde) system failed.\n\nPlease contact IT to review the following error:")
        logging.error(e)
        exit_code = 1

    # Get all logs from the in-memory stream for email
    message = get_all_logs()

    # Send the email with the log content
    mail(SMTP_SERVER, SENDER_USERNAME, FROM_EMAIL, RECEIVER_EMAIL, SENDER_PASSWORD, message, exit_code)
