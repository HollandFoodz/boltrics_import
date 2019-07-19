import os
from selenium.webdriver import Firefox, FirefoxProfile
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from time import sleep
from dotenv import load_dotenv


CWD = os.path.dirname(os.path.realpath(__file__))

if not os.path.exists('csv'):
    os.makedirs('csv')

LOGIN_URL = 'https://bakker-logistiek-iw9.nekovri-dynamics.nl/en-us/welcome.aspx'
VOORRAAD_URL = 'https://bakker-logistiek-iw9.nekovri-dynamics.nl/Lists/tabid/2379/list/PIJN_001/modid/3695/language/en-US/Default.aspx?title=%5cA.+Voorraad+per+artikel'

DESTINATION = os.path.join(CWD, 'csv')

KING_FILE = 'boltrics.csv'

def get_csv():
    browser.get(LOGIN_URL)
    username = browser.find_element_by_id('dnn_ctr3692_Login_Login_DNN_txtUsername')
    password = browser.find_element_by_id('dnn_ctr3692_Login_Login_DNN_txtPassword')
    login_btn = browser.find_element_by_id('dnn_ctr3692_Login_Login_DNN_cmdLogin')

    username.send_keys(USERNAME)
    password.send_keys(PASSWORD)
    login_btn.click()

    sleep(2)

    browser.get(VOORRAAD_URL)
    download_csv_btn = browser.find_element_by_id('dnn_ctr3694_Viewer_bolList_bolRadGrid_rdgList_ctl00_ctl02_ctl00_LinkButton1')
    download_csv_btn.click()
    browser.close()

def move_csv():
    files = os.listdir(DESTINATION)
    paths = [os.path.join(DESTINATION, basename) for basename in files]
    latest_file = max(paths, key=os.path.getctime)
    os.rename(latest_file, KING_FILE)

if __name__ == '__main__':
    load_dotenv()

    USERNAME = os.getenv('USERNAME')
    PASSWORD = os.getenv('PASSWORD')

    profile = FirefoxProfile()
    profile.set_preference('browser.download.folderList', 2) # custom location
    profile.set_preference('browser.download.manager.showWhenStarting', False)
    profile.set_preference('browser.download.dir', DESTINATION)
    profile.set_preference('browser.helperApps.neverAsk.saveToDisk', "text/csv, application/csv, application/*, */*")
    profile.set_preference('browser.helperApps.alwaysAsk.force', False)

    options = Options()
    options.set_headless()
    assert options.headless  # Operating in headless mode
    browser = Firefox(options=options, firefox_profile=profile)

    get_csv()
    move_csv()
