import os
import pyodbc
from shutil import move
from dotenv import load_dotenv

from reset_inventory import reset_inventory
from main import sync_king

MAGAZIJNEN = [""]

KING_XML_TEMPLATE = "king_voorraadcorrectie.xml"
XML_FILE = "./tmp.xml"

KING_FILE = "D:\\King\\dachser.xml"
SYNC_SCRIPT_PATH = "D:\King\Scripts\DachserSync.bat"


def sync_king(output_file):
    print("Synchronizing KING")
    move(output_file, KING_FILE)
    return os.system(SYNC_SCRIPT_PATH)


if __name__ == "__main__":
    load_dotenv(verbose=True)
    ODBC_SOURCE = os.getenv("ODBC_SOURCE")
    ODBC_UID = os.getenv("ODBC_UID")
    ODBC_PWD = os.getenv("ODBC_PWD")

    conn_str = "DSN={};UID={};PWD={}".format(ODBC_SOURCE, ODBC_UID, ODBC_PWD)

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    for MAGAZIJN_ID in MAGAZIJNEN:
        reset_inventory(cursor, MAGAZIJN_ID, KING_XML_TEMPLATE, XML_FILE)
        sync_king(XML_FILE)
