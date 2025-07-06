# File: plugins/calendar_sync.py

from ics import Calendar
from datetime import datetime, timedelta
import os

ICS_PATH = "calendar.ics"  # Place your .ics file in the NeuraMatrix root

def run():
    print("[📅 Calendar Sync Plugin] Loading events...")
    if not os.path.exists(ICS_PATH):
        print("⚠️ No calendar.ics file found. Please export from Google/Apple Calendar.")
        return

    with open(ICS_PATH, "r", encoding="utf-8") as f:
        cal = Calendar(f.read())

    now = datetime.now()
    week_later = now + timedelta(days=7)

    upcoming = [e for e in cal.timeline if now <= e.begin.datetime <= week_later]

    if not upcoming:
        print("📭 No upcoming events in the next 7 days.")
        return

    print("\n🗓️ Events This Week:\n")
    for event in upcoming:
        print(f"- {event.name} @ {event.begin.humanize()} → {event.begin.format('dddd, MMM D h:mm A')}")
