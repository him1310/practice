# credentials = []

# with open("practice/.cred_ad","r") as f:
#     credentials.extend(line.strip() for line in f)
# print(credentials)

# credentials = []
# with open("practice/.cread_ad", "r") as f:
#     credentials.extend(line.strip() for line in f)
from pathlib import Path

print(Path(__file__).parent)