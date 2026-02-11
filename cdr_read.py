#!/usr/bin/env python3

import pandas as pd
from datetime import datetime, timezone
import socket
import struct

# ----------------------------
# CONFIG
# ----------------------------
INPUT_FILE = "cdr.txt"
OUTPUT_FILE = "cdr_clean.csv"
CHUNK_SIZE = 200_000
TARGET_TIMEZONE = "Asia/Kolkata"

GW_Server = {
    "10.208.159.198" : "Gateway_GB_198",
    "10.208.159.196" : "Gateway_GB_196",
    "10.205.116.1" : "Gateway_11_high",
    "10.202.164.5" : "Gateway_Nhava",
    "10.205.143.14" : "Gateway_HB",
    "10.208.159.217" : "SVR_GB_217",
    "10.208.159.218" : "SVR_GB_218",
    "10.208.159.219" : "SVR_GB_219",
    "10.205.151.205" : "SVR_11_High_205",
    "10.205.151.206" : "SVR_11_High_206",
    "10.208.196.203" : "SVR_VB_203",
    "10.208.196.204" : "SVR_VB_204",
}

# ----------------------------
# HELPERS
# ----------------------------
def unix_to_datetime(ts):
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc)
    except Exception:
        return pd.NaT


def signed_int_to_ip(val):
    try:
        val = int(val)
        if val < 0:
            val += 4294967296
        reversed_ip = socket.inet_ntoa(struct.pack("!I", val))
        ip = ".".join(reversed(reversed_ip.split(".")))
        return GW_Server[ip]
    except KeyError:
        return ip
    except Exception:
        return None


# ----------------------------
# MAIN
# ----------------------------
def main():
    print("📞 Processing CUCM CDR CSV (robust mode)")
    print("----------------------------------")

    first_chunk = True
    total_calls = 0
    total_minutes = 0.0

    for chunk in pd.read_csv(
        INPUT_FILE,
        chunksize=CHUNK_SIZE,
        engine="python",
        on_bad_lines="skip"
    ):
        rows = len(chunk)
        total_calls += rows

        # Timestamp
        if "dateTimeOrigination" in chunk.columns:
            chunk["Call Start Time"] = (
                chunk["dateTimeOrigination"]
                .apply(unix_to_datetime)
                .dt.tz_convert(TARGET_TIMEZONE)
            )

        # IP conversion
        if "origIpAddr" in chunk.columns:
            chunk["Origin IP"] = chunk["origIpAddr"].apply(signed_int_to_ip)

        if "destIpAddr" in chunk.columns:
            chunk["Destination IP"] = chunk["destIpAddr"].apply(signed_int_to_ip)

        # Duration
        if "duration" in chunk.columns:
            chunk["Duration (min)"] = chunk["duration"] / 60
            total_minutes += chunk["Duration (min)"].sum()

        export_cols = [
            c for c in [
                "Call Start Time",
                "callingPartyNumber",
                "originalCalledPartyNumber",
                "Duration (min)",
                "Origin IP",
                "Destination IP",
                "origDeviceName",
                "destDeviceName"
            ] if c in chunk.columns
        ]

        chunk[export_cols].to_csv(
            OUTPUT_FILE,
            mode="w" if first_chunk else "a",
            index=False,
            header=first_chunk
        )

        first_chunk = False
        print(f"✔ Processed {total_calls:,} rows", end="\r")

    print("\n\n✅ PROCESS COMPLETED")
    print(f"Total Calls        : {total_calls:,}")
    print(f"Total Call Minutes : {total_minutes:,.2f}")
    print(f"Output File        : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
