import json
import firebase_store as fb

with open("history.json", encoding="utf-8") as f:
    data = json.load(f)
data.pop("selected_id", None)
data["revision"] = 1
fb.put("history", data)
fb.put("test", None)