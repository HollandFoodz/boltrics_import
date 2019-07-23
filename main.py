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

import pyodbc

from mail import mail
from reset_inventory import reset_inventory

from utils import add_xml, write_xml, get_xml_file_insert, get_latest_file

from article import Article


LOGIN_URL = 'https://bakker-logistiek-iw9.nekovri-dynamics.nl/en-us/welcome.aspx'
VOORRAAD_URL = 'https://bakker-logistiek-iw9.nekovri-dynamics.nl/Lists/tabid/2379/list/PIJN_001/modid/3695/language/en-US/Default.aspx?title=%5cA.+Voorraad+per+artikel'

CWD = os.path.dirname(os.path.realpath(__file__))
DESTINATION = os.path.join(CWD, 'csv')

ZEEWOLDE_MAGAZIJN_ID="010"
BOLTRICS_SYNC_SCRIPT_PATH="D:\King\Scripts\BoltricsSync.bat"
BOLTRICS_XML = 'boltrics.xml'
KING_FILE = 'D:\\King\\boltrics.xml'
KING_XML_TEMPLATE = 'king_voorraadcorrectie.xml'

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


def convert_csv(cursor, mag_id, xml_template_file, output_file):
    logging.info("Converting CSV")
    latest_file = get_latest_file(DESTINATION)
    root, regels = get_xml_file_insert(xml_template_file)

    df = pd.read_csv(latest_file, sep=';')
    articles = ', '.join('\'{}\''.format(str(row['Uw artikelnr.']).strip()) for _, row in df.iterrows())
    sql_query = 'SELECT ArtCode, ArtIsPartijRegistreren, KingSystem.tabArtikelPartij.ArtPartijNummer as ArtPartijNummer \
        from KingSystem.tabArtikel LEFT JOIN KingSystem.tabArtikelPartij \
        ON KingSystem.tabArtikel.ArtGid=KingSystem.tabArtikelPartij.ArtPartijArtGid \
        WHERE (KingSystem.tabArtikelPartij.ArtPartijIsGeblokkeerdVoorVerkoop = 0 OR KingSystem.tabArtikel.ArtIsPartijRegistreren = 0) AND \
        KingSystem.tabArtikel.ArtCode in ({})'.format(articles)

    # Fetch partij information
    cursor.execute(sql_query)
    rows = cursor.fetchall()
    articles = {}
    for row in rows:
        articles[row.ArtCode] = Article(row.ArtCode, row.ArtPartijNummer, row.ArtIsPartijRegistreren)

    print(len(rows), len(df))
    for i, row in df.iterrows():
        art_id = row['Uw artikelnr.'].strip()
        article = articles[art_id]
        # amount = row['Totaal excl. inslag']
        amount = row['Aantal eenheden']

        if article.partijregistratie:
            add_xml(regels, art_id, str(amount).strip(), mag_id, article.partijnummer)
        else:
            add_xml(regels, art_id, str(amount).strip(), mag_id)

    write_xml(output_file, root)
    os.remove(latest_file)

def sync_king(output_file):
    logging.info("Synchronizing KING")
    move(output_file, KING_FILE)
    return os.system(BOLTRICS_SYNC_SCRIPT_PATH)

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

    ODBC_SOURCE = os.getenv('ODBC_SOURCE')
    ODBC_UID = os.getenv('ODBC_UID')
    ODBC_PWD = os.getenv('ODBC_PWD')

    conn_str = 'DSN={};UID={};PWD={}'.format(ODBC_SOURCE, ODBC_UID, ODBC_PWD)

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()


    profile = FirefoxProfile()
    profile.set_preference('browser.download.folderList', 2) # custom location
    profile.set_preference('browser.download.manager.showWhenStarting', False)
    profile.set_preference('browser.download.dir', DESTINATION)
    profile.set_preference("browser.download.manager.showWhenStarting", False);
    profile.set_preference('browser.helperApps.neverAsk.saveToDisk', "text/csv,text/xls,application/excel,application/vnd.ms-excel")
    profile.set_preference('browser.helperApps.alwaysAsk.force', False)

    options = Options()
    options.set_headless()
    assert options.headless  # Operating in headless mode
    browser = Firefox(options=options, firefox_profile=profile)

    exit_code = 0
    error_msg = ''
    try:
        # Reset the inventory first for MagID Zeewolde (010)
        reset_inventory(cursor, ZEEWOLDE_MAGAZIJN_ID, KING_XML_TEMPLATE, BOLTRICS_XML)

        # Update with new values
        get_csv()
        convert_csv(cursor, ZEEWOLDE_MAGAZIJN_ID, BOLTRICS_XML, BOLTRICS_XML)
        exit_code = sync_king(BOLTRICS_XML)

        if exit_code:
            error_msg = 'King could not import new inventory (Job failed)'

    except Exception as e:
        logging.error(e)
        exit_code = 1
        error_msg = e

    if exit_code:
        error_msg = 'An import from the Boltrics (Zeewolde) system failed.\n\nPlease contact IT to review the following error:\n\n{}'.format(error_msg)
        mail(SMTP_SERVER, SENDER_EMAIL, RECEIVER_EMAIL, SENDER_PASSWORD, error_msg)
    else:
        logging.info("Completed successfully")
