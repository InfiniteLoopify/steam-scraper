import json
from pathlib import Path
from datetime import datetime, timedelta


def write_file(path, data):
    try:
        data = data.decode()
    except (UnicodeDecodeError, AttributeError):
        pass
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def read_file(path):
    if not Path(path).is_file():
        return {}
    with open(path) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            return {}


def has_time_exceeded(timestamp, hours=1):
    try:
        return datetime.now() - timedelta(hours=hours) > datetime.fromtimestamp(
            timestamp
        )
    except Exception as e:
        raise ValueError("Invalid Timestamp provided")
