import os
from selenium.webdriver import Firefox, FirefoxProfile
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from time import sleep
from dotenv import load_dotenv
from shutil import move

import pandas as pd
import lxml.etree as etree

import logging


LOGIN_URL = 'https://bakker-logistiek-iw9.nekovri-dynamics.nl/en-us/welcome.aspx'
VOORRAAD_URL = 'https://bakker-logistiek-iw9.nekovri-dynamics.nl/Lists/tabid/2379/list/PIJN_001/modid/3695/language/en-US/Default.aspx?title=%5cA.+Voorraad+per+artikel'

CWD = os.path.dirname(os.path.realpath(__file__))
DESTINATION = os.path.join(CWD, 'csv')

ZEEWOLDE_MAGAZIJN_ID="010"
BOLTRICS_SYNC_SCRIPT_PATH="D:\King\Scripts\BoltricsSync.bat"
BOLTRICS_XML = 'boltrics.xml'
KING_FILE = 'D:\\King\\boltrics.xml'

def get_csv():
    logging.info("Fetching CSV file from Boltrics")
    browser.get(LOGIN_URL)
    username = browser.find_element_by_id('dnn_ctr3692_Login_Login_DNN_txtUsername')
    password = browser.find_element_by_id('dnn_ctr3692_Login_Login_DNN_txtPassword')
    login_btn = browser.find_element_by_id('dnn_ctr3692_Login_Login_DNN_cmdLogin')

    username.send_keys(USERNAME)
    password.send_keys(PASSWORD)
    login_btn.click()

    sleep(1)

    browser.get(VOORRAAD_URL)
    download_csv_btn = browser.find_element_by_id('dnn_ctr3694_Viewer_bolList_bolRadGrid_rdgList_ctl00_ctl02_ctl00_LinkButton1')
    download_csv_btn.click()
    browser.close()


def add_xml(node, art_id, amount):

    # Ignore VP articles for now
    if 'VP' in art_id:
        return
    item = etree.SubElement(node, 'VOORRAADCORRECTIEREGEL')
    etree.SubElement(item, 'VCR_ARTIKEL').text = art_id
    etree.SubElement(item, 'VCR_AANTAL').text = amount
    etree.SubElement(item, 'VCR_MAGAZIJN').text = ZEEWOLDE_MAGAZIJN_ID
    etree.SubElement(item, 'VCR_LOCATIE').text = '(Standaard)'

    # if 'VP' in art_id:
    #     print(art_id)
    #     etree.SubElement(item, 'VCR_PARTIJ').text = '(Standaard)'

def convert_csv():
    logging.info("Converting CSV")
    files = os.listdir(DESTINATION)
    paths = [os.path.join(DESTINATION, basename) for basename in files]
    latest_file = max(paths, key=os.path.getctime)

    df = pd.read_csv(latest_file, sep=';')
    root = etree.parse('king_voorraadcorrectie.xml').getroot()
    regels = root.find("VOORRAADCORRECTIES/VOORRAADCORRECTIE/VOORRAADCORRECTIE_REGELS")
    for i, row in df.iterrows():
        art_id = row['Uw artikelnr.'].strip()
        amount = row['Totaal excl. inslag']
        add_xml(regels, art_id, str(amount).strip())

    with open(BOLTRICS_XML, 'wb') as f:
        f.write(etree.tostring(root, pretty_print=True))
    move(BOLTRICS_XML, KING_FILE)
    os.remove(latest_file)

def sync_king():
    logging.info("Synchronizing KING")
    os.system(BOLTRICS_SYNC_SCRIPT_PATH)

if __name__ == '__main__':
    load_dotenv(verbose=True)

    logging.basicConfig(format='%(asctime)s %(message)s', filename='boltrics.log', level=logging.INFO)

    if not os.path.exists('csv'):
        os.makedirs('csv')

    USERNAME = os.getenv('BOLTRICS_USERNAME')
    PASSWORD = os.getenv('BOLTRICS_PASSWORD')

    SMTP_SERVER = os.getenv('SMTP_SERVER')
    RECEIVER_EMAIL = os.getenv('RECEIVER_EMAIL')
    SENDER_EMAIL = os.getenv('SENDER_EMAIL')
    SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')

    profile = FirefoxProfile()
    profile.set_preference('browser.download.folderList', 2) # custom location
    profile.set_preference('browser.download.manager.showWhenStarting', False)
    profile.set_preference('browser.download.dir', DESTINATION)
    profile.set_preference("browser.download.manager.showWhenStarting", False);
    profile.set_preference('browser.helperApps.neverAsk.saveToDisk', "text/csv,text/xls,application/excel,application/vnd.ms-excel")
    profile.set_preference('browser.helperApps.alwaysAsk.force', False)

    options = Options()
    # options.set_headless()
    # assert options.headless  # Operating in headless mode
    browser = Firefox(options=options, firefox_profile=profile)

    try:
        from mail import mail
        get_csv()
        convert_csv()
        sync_king()
    except Exception as e:
        logging.error(e)
        mail(SMTP_SERVER, SENDER_EMAIL, RECEIVER_EMAIL, SENDER_PASSWORD, e)


