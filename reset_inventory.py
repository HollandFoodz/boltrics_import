import lxml.etree as etree
from utils import *

# Reindex database?
ignored_articles = [
    "TSDFDF",
    "Kok",
    "Deegbereiding",
    "Rollen",
    "Flowpacken",
    "chocolateren",
    "Deegbreiding likz",
    "Inleg lolly",
    "Insteek lolly",
    "Inpak likz",
    "Inpak Nougat",
    "Inpak stokken",
    "Inpak wichtgoed",
    "Magazijn",
    "Nougat snijden",
    "Spinnen lolly",
    "TD",
    "130003",
    "130003-1",
    "130010",
    "130010-1",
    "130011",
    "130011-1",
    "130024",
    "130024-1",
    "130031",
    "130031-1",
    "130031-2",
    "130031-3",
    "130031-4",
    "130092",
    "130092-1",
    "130259",
    "130259-1",
    "130259-3",
    "130259-2",
    "130269-2",
    "130269-3",
    "130269-4",
    "130269-5",
    "130269-6",
    "130269-7",
    "130269-8",
    "130269",
    "130269-1",
    "130269-9",
    "130269-10",
    "130289",
    "130289-1",
    "130290",
    "130290-1",
    "130291",
    "130291-1",
    "130291-2",
    "Handelshof-130013",
    "Handelshof-130018",
    "Handelshof-130022",
    "Handelshof-130039",
    "Handelshof-130004",
    "HANDELSHOF",
    "Handelshof-130012",
    "Handelshof-130042",
    "Handelshof-130044",
    "Handelshof-130095",
    "Handelshof-130107",
    "Handelshof-130140",
    "Handelshof-130141",
    "Handelshof-130143",
    "Handelshof-130146",
    "Handelshof-130156",
    "Handelshof-130252",
    "Handelshof-130254",
    "Handelshof-130255",
    "Handelshof-130255",
    "Handelshof-130255",
    "Handelshof-130255",
    "Handelshof-130255",
    "Handelshof-130255",
    "Handelshof-130255"
]


def reset_inventory(cursor, mag_id, xml_file, output_file):
    root, regels = get_xml_file_insert(xml_file)
    sql_query = "SELECT * from KingSystem.tabArtikel LEFT JOIN KingSystem.tabArtikelPartij \
        ON KingSystem.tabArtikel.ArtGid=KingSystem.tabArtikelPartij.ArtPartijArtGid \
        WHERE KingSystem.tabArtikelPartij.ArtPartijIsGeblokkeerdVoorVerkoop = 0 OR KingSystem.tabArtikel.ArtIsPartijRegistreren = 0"

    cursor.execute(sql_query)
    rows = cursor.fetchall()
    amount = 0
    for row in rows:
        # print(row.ArtSoort, row.ArtHeeftVoorraad)
        if not row.ArtHeeftVoorraad:
            continue

        art_id = str(row.ArtCode)

        # skip all the 000, 001, 099, etc.
        if len(art_id) == 3:
            if art_id[0].isdigit() and art_id[1].isdigit() and art_id[2].isdigit():
                continue

                
        # if art_id in ignored_articles:
        #     continue

        if row.ArtIsPartijRegistreren:
            partij = str(row.ArtPartijNummer)
            add_xml(regels, art_id, str(amount), mag_id, partij)
        else:
            add_xml(regels, art_id, str(amount), mag_id)

    write_xml(output_file, root)
