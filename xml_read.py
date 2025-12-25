import xml.etree.ElementTree as ET

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
XML_FILE = "practice/results23.xml"

# EXACT plant prefixes as shown in SAP (same case)
ALLOWED_PLANT_PREFIXES = (
    "Mumbai High Asset, UT OFFSHORE",
    "Neelam Heera Asset, UT OFFSHOR",
    "Bassein&Satellite Asset,UTOFFS"
)

# Namespaces (ATOM + SAP OData)
NS = {
    "a": "http://www.w3.org/2005/Atom",
    "m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
    "d": "http://schemas.microsoft.com/ado/2007/08/dataservices"
}

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def safe_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0

def clean(text):
    """Remove invisible unicode spaces but keep case"""
    return text.replace("\xa0", " ").strip()

# -------------------------------------------------
# MAIN
# -------------------------------------------------
tree = ET.parse(XML_FILE)
root = tree.getroot()

total_actual_bb6 = 0.0
matched_rows = 0
with open("practice/entry_oil.log", "w") as f:
    pass
f.close()


with open("practice/entry_oil.log", "a") as f:
# IMPORTANT: entry is in Atom namespace
    for entry in root.findall(".//a:entry", NS):
        props = entry.find("a:content/m:properties", NS)
        if props is None:
            continue

        plant_el = props.find("d:IREP_PLNT_T", NS)
        bb6_el = props.find("d:ACTUAL_BB6", NS)

        if plant_el is None or bb6_el is None:
            continue
        print(plant_el)
        plant_text = clean(plant_el.text)

        # Prefix-based match (NO ROW LOSS)
        if plant_text.startswith(ALLOWED_PLANT_PREFIXES):
            print(bb6_el.text)
            f.write(f"{bb6_el.text} {plant_text}\n")
            total_actual_bb6 += safe_float(bb6_el.text)
            matched_rows += 1

# -------------------------------------------------
# OUTPUT
# -------------------------------------------------
    print("Matched rows :", matched_rows)
    print("Total ACTUAL_BB6 :", round(total_actual_bb6, 3))
    f.write(str(total_actual_bb6))