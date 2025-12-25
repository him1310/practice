import xml.etree.ElementTree as ET
from collections import defaultdict

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
XML_FILE = "practice/HSE.xml"

# Stable keywords (DO NOT use full text equality)
PLANT_KEYWORDS = {
    "Mumbai High Asset": "Mumbai High Asset, UT OFFSHORE",
    "Neelam Heera Asset": "Neelam Heera Asset, UT OFFSHOR",
    "Bassein&Satellite Asset": "Bassein&Satellite Asset,UTOFFS"
}

NS = {
    "a": "http://www.w3.org/2005/Atom",
    "m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
    "d": "http://schemas.microsoft.com/ado/2007/08/dataservices"
}

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def clean(text):
    if text is None:
        return ""
    return (
        text.replace("\xa0", " ")
            .replace("\n", " ")
            .replace("\r", " ")
            .strip()
    )

def safe_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0

# -------------------------------------------------
# MAIN
# -------------------------------------------------
tree = ET.parse(XML_FILE)
root = tree.getroot()

index_score_by_plant = defaultdict(float)
row_count_by_plant = defaultdict(int)

for entry in root.findall(".//a:entry", NS):
    props = entry.find("a:content/m:properties", NS)
    if props is None:
        continue

    plant_el = props.find("d:IREP_PLNT_T", NS)
    score_el = props.find("d:INDEX_SCORE", NS)

    if plant_el is None or score_el is None:
        continue

    plant_text = clean(plant_el.text)
    score = safe_float(score_el.text)

    # 🔑 KEY FIX: keyword-based matching
    for keyword, canonical_name in PLANT_KEYWORDS.items():
        if keyword in plant_text:
            index_score_by_plant[canonical_name] += score
            row_count_by_plant[canonical_name] += 1
            break

# -------------------------------------------------
# OUTPUT
# -------------------------------------------------
print("INDEX_SCORE total per plant:\n")

grand_total = 0.0

for plant in PLANT_KEYWORDS.values():
    total = index_score_by_plant.get(plant, 0.0)
    rows = row_count_by_plant.get(plant, 0)
    grand_total += total

    print(f"{plant:45} -> {round(total, 3)}  (rows: {rows})")

print("\nGrand Total INDEX_SCORE:", round(grand_total, 3))
