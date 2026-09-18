import json
import os

def load_items(filename):
    """Load items from JSON file and return items list only"""
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data["items"]


def get_unclaimed_items(items):
    """Filter and return only unclaimed items"""
    return [item for item in items if item["status"] == "unclaimed"]


def save_result(result, filename):
    """Save result as JSON. Create directory if it does not exist."""
    directory_path = os.path.dirname(filename)
    if directory_path and not os.path.exists(directory_path):
        os.makedirs(directory_path)
    with open(filename, "w", encoding="utf-8") as out_file:
        json.dump(result, out_file, indent=4, ensure_ascii=False)
