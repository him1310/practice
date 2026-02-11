from netmiko import ConnectHandler
import re
from datetime import datetime
import csv, os
from pathlib import Path

time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

i = 1

device_details = {}

# reading the details of the devices

with open(f"{Path(__file__).parent}/devices", "r") as f:
    while True:
        content = f.readline()
        if not content:
            break
        device_details[f"device_{i}"] = content.split()
        i+=1
f.close()

# extracting header for the CSV file

device_names = [value[0] for value in device_details.values()]
headers = ['TimeStamp'] + device_names

# creating the CSV file

if not(os.path.exists(f"{Path(__file__).parent}/output/active_calls_1.csv")):
    with open(f"{Path(__file__).parent}/output/active_calls_1.csv", 'w', newline='') as csvf:
        writer = csv.writer(csvf)
        writer.writerow(headers)
    csvf.close()
active_calls = {}

# Connecting to the devices using netmiko

for hostname, credentials in device_details.items():
    device_to_connect = {
        "device_type" : "cisco_ios",
        "host" : credentials[1],
        "username" : credentials[2],
        "password" : credentials[3],
    }
    try:
        net_connect = ConnectHandler(**device_to_connect)

        # Using regex to find the active voice calls

        pattern = r"(\d{1,3} active call[s]? found|no active calls found)"
        active_calls[f'{credentials[0]}'] = str(re.findall(pattern, net_connect.send_command("show voice call status"), re.IGNORECASE)[0]).split()[0]
        net_connect.disconnect()
    except Exception as e:
        active_calls[f'{credentials[0]}'] = e

active_calls['TimeStamp'] = time_now

# writing the data into CSV file

with open(f"{Path(__file__).parent}/output/active_calls_1.csv", "a", newline='') as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writerow(active_calls)
f.close()

