#!/usr/bin/env python3

from ldap3 import Server, Connection, ALL, Tls
from datetime import datetime, timedelta
import ssl

# --------------------------------
# CONFIGURATION
# --------------------------------
credentials = []
with open("practice/.cred_ad", "r") as f:
    credentials.extend(line.strip() for line in f)

LDAP_HOST = credentials[0]
LDAP_PORT = 389          # 636 for LDAPS
USE_SSL   = False
LDAP_USER = credentials[1]
LDAP_PASS = credentials[2]

LDAP_BASES = {
    "MUMBAI": "OU=Mumbai,OU=MumbaiRegion,DC=ONGC,DC=ONGCGROUP,DC=CO,DC=in",
    "URAN": "OU=URAN,OU=MumbaiRegion,DC=ONGC,DC=ONGCGROUP,DC=CO,DC=in",
    "PANVEL": "OU=Panvel,OU=MumbaiRegion,DC=ONGC,DC=ONGCGROUP,DC=CO,DC=in",
    "NHAVA": "OU=Nhava,OU=MumbaiRegion,DC=ONGC,DC=ONGCGROUP,DC=CO,DC=in",
}

BIRTH_ATTR = "birthdate"     # change if needed

# --------------------------------
# DATE CALCULATION (TOMORROW)
# --------------------------------
tomorrow = datetime.now()
CHECK_DAY = tomorrow.day
CHECK_MONTH = tomorrow.month

# --------------------------------
# HELPERS
# --------------------------------
def parse_ad_date(value):
    """
    Supports:
    - YYYY-MM-DD
    - YYYYMMDD
    - Windows FILETIME
    """
    if not value:
        return None

    try:
        if isinstance(value, str):
            if "-" in value:
                return datetime.strptime(value, "%Y-%m-%d")
            if len(value) == 8:
                return datetime.strptime(value, "%Y%m%d")

        if isinstance(value, int):
            return datetime(1601, 1, 1) + timedelta(microseconds=value // 10)

    except Exception:
        return None

    return None


# --------------------------------
# FUNCTION
# --------------------------------
def get_disabled_users_birthday_tomorrow():
    tls_config = Tls(validate=ssl.CERT_NONE) if USE_SSL else None

    server = Server(
        LDAP_HOST,
        port=LDAP_PORT,
        use_ssl=USE_SSL,
        get_info=ALL,
        tls=tls_config
    )

    conn = Connection(
        server,
        user=LDAP_USER,
        password=LDAP_PASS,
        auto_bind=True
    )

    results = []

    # LDAP filter:
    # - users only
    # - exclude computers
    # - INCLUDE disabled accounts only
    search_filter = (
        "(&"
        "(objectClass=user)"
        "(!(objectClass=computer))"
        ")"
    )

    for location, base_dn in LDAP_BASES.items():
        conn.search(
            search_base=base_dn,
            search_filter=search_filter,
            attributes=[
                "sAMAccountName",
                "displayName",
                "department",
                BIRTH_ATTR
            ]
        )

        for entry in conn.entries:
            raw_date = entry[BIRTH_ATTR].value if BIRTH_ATTR in entry else None
            dob = parse_ad_date(raw_date)

            if not dob:
                continue

            # Match TOMORROW (day & month only)
            if dob.day == CHECK_DAY and dob.month == CHECK_MONTH:
                results.append({
                    "location": location,
                    "username": entry.sAMAccountName.value,
                    "name": entry.displayName.value if "displayName" in entry else "",
                    "department": entry.department.value if "department" in entry else "",
                    "birthdate": dob.strftime("%d-%m-%Y")
                })

    return results


# --------------------------------
# MAIN
# --------------------------------
if __name__ == "__main__":
    users = get_disabled_users_birthday_tomorrow()

    if users:
        for u in users:
            print(f"Location   : {u['location']}")
            print(f"Name       : {u['name']}")
            print(f"Username   : {u['username']}")
            print(f"Department : {u['department']}")
            print(f"Birthdate  : {u['birthdate']}")
            print("-" * 55)
    else:
        print("\nNo disabled users have birthday tomorrow.")
    print(len(users))
