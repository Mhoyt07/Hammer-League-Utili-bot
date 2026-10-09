import json
import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE = Path(__file__).parent
load_dotenv(BASE / ".env")

WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]
STATE = BASE / "state.json"
PLAYERS = ["Jaden", "Varun", "Matthew"]
VALID = [sorted(["2 - 0", "1 - 1", "0 - 2"]), ["1 - 1"] * 3]


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save_state(state):
    STATE.write_text(json.dumps(state, indent=2))


def norm_score(text):
    d = re.findall(r"\d", text)
    if len(d) != 2:
        raise ValueError(f"bad score: {text!r}")
    return f"{d[0]} - {d[1]}"


def table(values):
    name_w = max(len(p) for p in PLAYERS)
    val_w = max(len(v) for v in values)
    return "\n".join(
        f"| {p.ljust(name_w)} | {v.ljust(val_w)} |"
        for p, v in zip(PLAYERS, values)
    )


def render(state):
    results = [state["results"][p] for p in PLAYERS]
    choices = [state["choices"].get(p, "-") for p in PLAYERS]
    return (
        f"# {state['title']}\n"
        f"## Results\n```\n{table(results)}\n```\n"
        f"## Choices\n```\n{table(choices)}\n```"
    )


def push(state):
    body = {"content": render(state)[:2000], "allowed_mentions": {"parse": []}}
    if state.get("message_id"):
        r = requests.patch(f"{WEBHOOK}/messages/{state['message_id']}", json=body)
    else:
        r = requests.post(WEBHOOK, params={"wait": "true"}, json=body)
        if r.ok:
            state["message_id"] = r.json()["id"]
    print(r.status_code)
    if not r.ok:
        print(r.text)
    else:
        save_state(state)
    return r.ok


def new_round():
    title = input("Title: ").strip()
    results = {p: norm_score(input(f"{p} result: ")) for p in PLAYERS}
    if sorted(results.values()) not in VALID:
        sys.exit("Those results are not a valid outcome.")
    push({"title": title, "results": results, "choices": {}})


def add_choice():
    state = load_state()
    if not state:
        sys.exit("No round yet. Run: uv run league.py new")
    for i, p in enumerate(PLAYERS, 1):
        print(i, p)
    player = PLAYERS[int(input("Player number: ")) - 1]
    state["choices"][player] = input(f"{player} choice: ").strip()
    push(state)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"new": new_round, "choice": add_choice}.get(
        cmd, lambda: sys.exit("Use: new | choice")
    )()