import re

DATA_FILE = "/home/ubuntu/learn/practice/data_1.txt"

TARGET_PLANTS = {
    "Neelam Heera Asset, UT OFFSHOR",
    "Mumbai High Asset, UT OFFSHORE",
    "Bassein&Satellite Asset,UTOFFS",
}

plant_re = re.compile(r"\[IREP_PLNT_T\]\s*=>\s*(.+)")
actual_re = re.compile(r"\[ACTUAL_MT\]\s*=>\s*([\d.]+)")

def total_actual_mt_from_php_dump(file_path, target_plants):
    total = 0.0
    current_plant = None
    i = 0 
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            p = plant_re.search(line)
            if p:
                current_plant = p.group(1).strip()
                continue

            a = actual_re.search(line)
            if a and current_plant in target_plants:
                i += 1
                total += float(a.group(1))
    print(i)
    return round(total, 3)

if __name__ == "__main__":
    total = total_actual_mt_from_php_dump(DATA_FILE, TARGET_PLANTS)
    print("TOTAL ACTUAL_MT:", total)