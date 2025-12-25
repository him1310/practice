import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import shutil

with open("practice/hse_index_json.json", "r") as f:
    data = json.load(f)

plant_to_site = {
    '11' : 'MH_Asset',
    '12': 'NH_Asset',
    '13': 'BS_Asset',
    '10D1': 'DRILLING',
    '10P1' : 'URAN',
}
months = sorted({
    datetime.fromisoformat(item["Date"].replace("Z", "+00:00")).replace(day=1)
    for item in data
    if "Date" in item and item["Date"]
})

# Safety check
if not months:
    print("No valid dates found")
    exit()

start = months[0]
end = months[-1]

# Step 3: format output
if start.year == end.year and start.month == end.month:
    result = start.strftime("%B %Y")
elif start.year == end.year:
    result = f"{start.strftime('%B')} to {end.strftime('%B %Y')}"
else:
    result = f"{start.strftime('%B %Y')} to {end.strftime('%B %Y')}"

print(result)


site_sum = defaultdict(float)
site_count = defaultdict(int)

for values in data:
    total = values.get('Total')
    if total == '' or None:
        continue
    plant = values.get('Plant Code', '')
    site = plant_to_site.get(plant) or plant_to_site.get(plant[:2])
    
    if site:
        site_sum[site] += total
        site_count[site] += 1

site_index = {site: round(site_sum[site] / site_count[site], 1) for site in site_sum}


site_index['period'] = result

current_date = datetime.now().strftime("%d-%m-%Y")
file_path = Path(f"/home/ubuntu/learn/practice/index_{current_date}.log")
with file_path.open("w") as f:
    json.dump(site_index, f, indent=4)

