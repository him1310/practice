import xml.etree.ElementTree as ET

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
XML_FILE = "practice/results.xml"

# Namespaces (ATOM + SAP OData)
NS = {
    "a": "http://www.w3.org/2005/Atom",
    "m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
    "d": "http://schemas.microsoft.com/ado/2007/08/dataservices"
}

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def clean(text):
    """Remove invisible unicode spaces and trim"""
    return text.replace("\xa0", " ").strip()

# -------------------------------------------------
# MAIN
# -------------------------------------------------
tree = ET.parse(XML_FILE)
root = tree.getroot()

plants = set()

for entry in root.findall(".//a:entry", NS):
    props = entry.find("a:content/m:properties", NS)
    if props is None:
        continue

    plant_el = props.find("d:IREP_PLNT_T", NS)
    if plant_el is None or plant_el.text is None:
        continue

    plant_name = clean(plant_el.text)
    plants.add(plant_name)

# -------------------------------------------------
# OUTPUT
# -------------------------------------------------
print(f"Total unique IREP_PLNT_T values: {len(plants)}\n")

for name in sorted(plants):
    print(name)
