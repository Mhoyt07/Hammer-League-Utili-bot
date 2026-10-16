import copy
import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from history import (
    check_fresh,
    push_history
)

from history import (
    add_round,
    get_round,
    load_history,
    save_history,
    selected_round,
    update_round,
)


BASE = Path(__file__).parent
load_dotenv(BASE / ".env")

WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"].strip()
PLAYERS = ["Jaden", "Varun", "Matthew"]
VALID = [
    sorted(["2 - 0", "1 - 1", "0 - 2"]),
    ["1 - 1"] * 3,
]


def load_state():
    """Return the selected round in the format the existing GUI expects."""
    history = load_history()
    entry = selected_round(history)

    if entry is None:
        return {}

    state = copy.deepcopy(entry["data"])
    state["title"] = entry["title"]
    state["message_id"] = entry["message_id"]
    state["history_id"] = entry["id"]
    state.setdefault("choices", {})
    return state


def save_state(state):
    """Add a posted round or update an existing history entry."""
    if not state.get("message_id"):
        raise ValueError("Cannot save a round without a Discord message ID.")

    history = load_history()
    round_id = state.get("history_id")
    entry = get_round(history, round_id) if round_id else None

    if round_id and entry is None:
        raise ValueError(
            f"Saved round {round_id!r} no longer exists in history.json."
        )

    # Also recognize existing rounds loaded without a history_id.
    if entry is None:
        message_id = str(state["message_id"])
        entry = next(
            (
                item
                for item in history["rounds"]
                if str(item["message_id"]) == message_id
            ),
            None,
        )

    data = copy.deepcopy(state)

    # These belong to the history entry, not its nested round data.
    data.pop("history_id", None)
    data.pop("message_id", None)

    if entry is None:
        entry = add_round(
            history,
            title=state["title"],
            message_id=state["message_id"],
            data=data,
        )
        # add_round selects the newly posted round.
    else:
        update_round(
            history,
            entry["id"],
            title=state["title"],
            message_id=str(state["message_id"]),
            data=data,
        )

    push_history(history)

    # Keep the caller's state linked to its saved history entry.
    state["history_id"] = entry["id"]


def norm_score(text):
    digits = re.findall(r"\d", text)
    if len(digits) != 2:
        raise ValueError(f"bad score: {text!r}")
    return f"{digits[0]} - {digits[1]}"


def table(values):
    name_width = max(len(player) for player in PLAYERS)
    value_width = max(len(value) for value in values)

    return "\n".join(
        f"| {player.ljust(name_width)} | {value.ljust(value_width)} |"
        for player, value in zip(PLAYERS, values)
    )


def render(state):
    results = [state["results"][player] for player in PLAYERS]
    choices = [
        state["choices"].get(player, "-")
        for player in PLAYERS
    ]

    return (
        f"# {state['title']}\n"
        f"## Results\n```\n{table(results)}\n```\n"
        f"## Choices\n```\n{table(choices)}\n```"
    )


def push(state):
    """Send to Discord, then save locally only after Discord succeeds."""
    content = render(state)

    if len(content) > 2000:
        print("Message is too long. Shorten the title or choices.")
        return False

    check_fresh(load_history())

    body = {
        "content": content,
        "allowed_mentions": {"parse": []},
    }

    # Work on a copy so failed requests don't modify the caller's state.
    pending = copy.deepcopy(state)

    try:
        if pending.get("message_id"):
            response = requests.patch(
                f"{WEBHOOK}/messages/{pending['message_id']}",
                json=body,
                timeout=20,
            )
        else:
            if pending.get("history_id"):
                raise ValueError(
                    "This saved round has no Discord message ID. "
                    "Refusing to create a duplicate message."
                )

            response = requests.post(
                WEBHOOK,
                params={"wait": "true"},
                json=body,
                timeout=20,
            )

        print(response.status_code)

        if not response.ok:
            print(response.text)
            return False

        if not pending.get("message_id"):
            pending["message_id"] = response.json()["id"]

    except requests.RequestException as error:
        print(f"Discord request failed: {error}")
        return False

    # Preserve the returned message ID even if the disk save fails.
    state.update(pending)

    try:
        save_state(state)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(
            "Discord was updated, but local history could not be saved: "
            f"{error}"
        )
        print(f"Discord message ID: {state['message_id']}")
        raise

    return True


def new_round():
    title = input("Title: ").strip()
    results = {
        player: norm_score(input(f"{player} result: "))
        for player in PLAYERS
    }

    if sorted(results.values()) not in VALID:
        sys.exit("Those results are not a valid outcome.")

    # No message_id or history_id means this is a new round.
    push({
        "title": title,
        "results": results,
        "choices": {},
    })


def add_choice():
    state = load_state()

    if not state:
        sys.exit("No round yet. Run: uv run league.py new")

    for number, player in enumerate(PLAYERS, 1):
        print(number, player)

    try:
        number = int(input("Player number: "))
    except ValueError:
        sys.exit("Enter a valid player number.")

    if not 1 <= number <= len(PLAYERS):
        sys.exit("Enter a valid player number.")

    player = PLAYERS[number - 1]
    state["choices"][player] = input(
        f"{player} choice: "
    ).strip()

    push(state)


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""

    {
        "new": new_round,
        "choice": add_choice,
    }.get(
        command,
        lambda: sys.exit("Use: new | choice"),
    )()