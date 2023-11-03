import xml.etree.ElementTree as ET


tree = ET.parse("exclude.xml")
root = tree.getroot()
exclude = []
for i in root[0][0][1]:
    if len(i) == 5:
        exclude.append(i[0].text)

tree = ET.parse("art_voorraad.xml")
root = tree.getroot()


def fmt(nr, magazijn, locatie):
    return f"""<VOORRAADCORRECTIEREGEL>
<VCR_ARTIKEL>{nr}</VCR_ARTIKEL>
<VCR_AANTAL>0</VCR_AANTAL>
<VCR_MAGAZIJN>{magazijn}</VCR_MAGAZIJN>
<VCR_LOCATIE>{locatie}</VCR_LOCATIE>
</VOORRAADCORRECTIEREGEL>\n"""


strs = []
for child in root[1]:
    art_nr = child.attrib["Artikelnummer"]
    magazijn = child.attrib["Magazijn"]
    locatie = child.attrib["Locatie"]
    aantal = child.attrib["Aantal"]
    if (
        aantal != "0.00"
        and art_nr not in exclude
        and "vp" not in art_nr.lower()
        and "gr" not in art_nr.lower()
    ):
        strs.append(fmt(art_nr, magazijn, locatie))


with open("voorraadcorrectie.xml", "w") as f:
    f.writelines(strs)
