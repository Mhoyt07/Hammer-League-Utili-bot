import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent
HISTORY_FILE = BASE / "history.json"
LEGACY_STATE = BASE / "state.json"


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _empty():
    return {"version": 1, "selected_id": None, "rounds": []}


def load_history():
    if not HISTORY_FILE.exists():
        history = _empty()
        if _migrate_legacy(history):
            save_history(history)
        return history
    try:
        history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(
            f"history.json is not valid JSON ({e}). "
            "A backup may exist as history.json.bak."
        )
    if not isinstance(history, dict) or "rounds" not in history:
        raise ValueError("history.json is missing the 'rounds' list.")
    history.setdefault("version", 1)
    history.setdefault("selected_id", None)
    return history


def save_history(history):
    tmp = HISTORY_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
    if HISTORY_FILE.exists():
        shutil.copy2(HISTORY_FILE, HISTORY_FILE.with_suffix(".json.bak"))
    os.replace(tmp, HISTORY_FILE)


def _migrate_legacy(history):
    if not LEGACY_STATE.exists():
        return False
    try:
        state = json.loads(LEGACY_STATE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    if not state:
        return False
    backup = LEGACY_STATE.with_suffix(".json.bak")
    if not backup.exists():
        shutil.copy2(LEGACY_STATE, backup)
    message_id = str(state.get("message_id") or state.get("id") or "")
    add_round(
        history,
        title=str(state.get("title", "Imported round")),
        message_id=message_id,
        data=state,
    )
    return True


def add_round(history, title, message_id, data=None, pack=None):
    entry = {
        "id": uuid.uuid4().hex[:8],
        "title": title,
        "message_id": str(message_id),
        "pack": pack,
        "data": data or {},
        "created_at": _now(),
        "updated_at": _now(),
    }
    history["rounds"].append(entry)
    history["selected_id"] = entry["id"]
    return entry

def get_round(history, round_id):
    for r in history["rounds"]:
        if r["id"] == round_id:
            return r
    return None


def selected_round(history):
    rid = history.get("selected_id")
    return get_round(history, rid) if rid else None


def select_round(history, round_id):
    if get_round(history, round_id) is None:
        raise KeyError(f"No round with id {round_id}")
    history["selected_id"] = round_id


def update_round(history, round_id, **changes):
    r = get_round(history, round_id)
    if r is None:
        raise KeyError(f"No round with id {round_id}")
    allowed = {"title", "data", "pack", "message_id"}
    for key, value in changes.items():
        if key not in allowed:
            raise ValueError(f"Cannot update field '{key}'")
        r[key] = value
    r["updated_at"] = _now()
    return r


def round_label(r):
    return r["title"]