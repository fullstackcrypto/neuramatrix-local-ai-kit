# /plugins/daily_summary.py

import os
from datetime import datetime, timedelta

LOG_PATH = "memory/session_log.txt"


def run():
    if not os.path.exists(LOG_PATH):
        print("[Daily Summary] No session log found.")
        return

    try:
        with open(LOG_PATH, 'r') as log_file:
            lines = log_file.readlines()

        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        summary = []

        for line in lines:
            if line.startswith("["):
                timestamp_str = line.split("]")[0][1:]
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")
                if timestamp.date() == yesterday:
                    summary.append(line.strip())

        if summary:
            print("\n[🧠 Daily Summary for", yesterday.strftime("%Y-%m-%d"), "]")
            print("\n".join(summary))
        else:
            print("[Daily Summary] No entries for yesterday.")

    except Exception as e:
        print("[Daily Summary Error]", str(e))
