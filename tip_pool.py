import json
import os
from datetime import datetime, timedelta

_HISTORY_DIR = os.getenv("HISTORY_DIR", os.path.dirname(__file__))
_HISTORY_FILE = os.path.join(_HISTORY_DIR, "tips_history.json")


def save_to_history(pool):
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_tips": pool.total_tips,
        "staff": [m.to_dict() for m in pool.members],
    }
    try:
        with open(_HISTORY_FILE) as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = []
    history.append(entry)
    with open(_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def load_history(days):
    try:
        with open(_HISTORY_FILE) as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return [e for e in history if e["date"] >= cutoff]


def delete_history_date(date_str):
    try:
        with open(_HISTORY_FILE) as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0
    kept = [e for e in history if e["date"] != date_str]
    removed = len(history) - len(kept)
    if removed:
        with open(_HISTORY_FILE, "w") as f:
            json.dump(kept, f, indent=2)
    return removed


class TipPool:
    def __init__(self, total_tips):
        self.total_tips = total_tips
        self.members = []

    def add_member(self, member):
        self.members.append(member)

    def split(self):
        kitchen_pool = self.total_tips / 2
        service_pool = self.total_tips / 2

        kitchen_wh = sum(m.weighted_hours() for m in self.members if m.department == "Kitchen")
        service_wh = sum(m.weighted_hours() for m in self.members if m.department == "Service")

        kitchen_rate = kitchen_pool / kitchen_wh
        service_rate = service_pool / service_wh

        for member in self.members:
            if member.department == "Kitchen":
                member.tips = member.weighted_hours() * kitchen_rate
            else:
                member.tips = member.weighted_hours() * service_rate

    def show(self):
        for member in self.members:
            member.info()
