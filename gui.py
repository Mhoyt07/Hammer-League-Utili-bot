import tkinter as tk
from tkinter import ttk

import league
from history import (
    load_history,
    round_label,
    save_history,
    select_round,
    pull
)


SCORES = ["2 - 0", "1 - 1", "0 - 2"]

OPTIONS = {
    "2 - 0": [
        (
            "3 tournament packs",
            "3 'Tournament {}' Packs",
            "Pack number",
        ),
    ],
    "1 - 1": [
        ("Open six extra packs of next set", "Open three extra packs of {}", "Set Name"),
        ("Limit a card", "Limit '{}'", "Card name"),
    ],
    "0 - 2": [
        ("Reroll next set", "Reroll next set", None),
        ("Ban a card", "Ban '{}'", "Card name"),
    ],
}


root = tk.Tk()
root.title("Hammer League")
root.columnconfigure(0, weight=1)

status = tk.StringVar()

round_var = tk.StringVar()
round_ids = []

title_var = tk.StringVar()
result_vars = {}

player_var = tk.StringVar()
result_text = tk.StringVar(value="Result: -")
option_var = tk.StringVar()
detail_var = tk.StringVar()
detail_label_var = tk.StringVar(value="Detail")
current_options = []


# Saved-round selector
history_frame = ttk.LabelFrame(
    root, text="Round to edit", padding=10
)
history_frame.grid(
    row=0, column=0, padx=10, pady=10, sticky="ew"
)
history_frame.columnconfigure(1, weight=1)

ttk.Label(history_frame, text="Saved round").grid(
    row=0, column=0, sticky="w"
)

round_box = ttk.Combobox(
    history_frame,
    textvariable=round_var,
    state="readonly",
    width=45,
)
round_box.grid(
    row=0, column=1, padx=(10, 0), pady=2, sticky="ew"
)

ttk.Label(
    history_frame,
    text="Save choice updates the selected round.",
).grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))


# New round
round_frame = ttk.LabelFrame(
    root, text="New round", padding=10
)
round_frame.grid(
    row=1, column=0, padx=10, pady=10, sticky="ew"
)
round_frame.columnconfigure(1, weight=1)

ttk.Label(round_frame, text="Title").grid(
    row=0, column=0, sticky="w"
)
ttk.Entry(
    round_frame,
    textvariable=title_var,
    width=40,
).grid(row=0, column=1, pady=2, sticky="ew")

for index, player in enumerate(league.PLAYERS, start=1):
    ttk.Label(round_frame, text=player).grid(
        row=index, column=0, sticky="w"
    )
    value = tk.StringVar()
    ttk.Combobox(
        round_frame,
        textvariable=value,
        values=SCORES,
        state="readonly",
        width=8,
    ).grid(row=index, column=1, sticky="w", pady=2)
    result_vars[player] = value


# Add choice
choice_frame = ttk.LabelFrame(
    root, text="Add choice", padding=10
)
choice_frame.grid(
    row=2, column=0, padx=10, pady=10, sticky="ew"
)

ttk.Label(choice_frame, text="Player").grid(
    row=0, column=0, sticky="w"
)

player_box = ttk.Combobox(
    choice_frame,
    textvariable=player_var,
    values=league.PLAYERS,
    state="readonly",
    width=12,
)
player_box.grid(row=0, column=1, sticky="w", pady=2)

ttk.Label(
    choice_frame, textvariable=result_text
).grid(row=0, column=2, padx=10)

ttk.Label(choice_frame, text="Option").grid(
    row=1, column=0, sticky="w"
)

option_box = ttk.Combobox(
    choice_frame,
    textvariable=option_var,
    state="readonly",
    width=28,
)
option_box.grid(
    row=1, column=1, columnspan=2, sticky="w", pady=2
)

ttk.Label(
    choice_frame, textvariable=detail_label_var
).grid(row=2, column=0, sticky="w")

detail_entry = ttk.Entry(
    choice_frame,
    textvariable=detail_var,
    width=30,
    state="disabled",
)
detail_entry.grid(
    row=2, column=1, columnspan=2, sticky="w", pady=2
)


def reset_choice_form():
    player_var.set("")
    result_text.set("Result: -")
    option_box["values"] = []
    option_var.set("")
    current_options.clear()
    detail_var.set("")
    detail_label_var.set("Detail")
    detail_entry.config(state="disabled")


def refresh_rounds():
    history = load_history()
    entries = list(reversed(history["rounds"]))

    round_ids[:] = [entry["id"] for entry in entries]
    round_box["values"] = [
        round_label(entry) for entry in entries
    ]

    selected_id = history.get("selected_id")
    if selected_id in round_ids:
        round_box.current(round_ids.index(selected_id))
    else:
        round_var.set("")

def reload_all():
    try:
        pull()
        refresh_rounds()
    except (OSError, ValueError, KeyError, TypeError) as error:
        status.set(f"Reload failed: {error}")
        return

    title_var.set("")
    for value in result_vars.values():
        value.set("")
    reset_choice_form()
    status.set("Reloaded from Firebase.")

def on_round_selected(event=None):
    index = round_box.current()
    if index < 0:
        return

    try:
        history = load_history()
        select_round(history, round_ids[index])
        save_history(history)
    except (OSError, ValueError, KeyError, TypeError) as error:
        status.set(f"Could not select round: {error}")
        try:
            refresh_rounds()
        except (OSError, ValueError, KeyError, TypeError):
            round_var.set("")
        reset_choice_form()
        return

    reset_choice_form()
    status.set(
        f"Editing {round_var.get()}. Pick a player below."
    )


def post_round():
    title = title_var.get().strip()
    results = {
        player: value.get()
        for player, value in result_vars.items()
    }

    if not title or "" in results.values():
        status.set("Fill in the title and all results.")
        return

    if sorted(results.values()) not in league.VALID:
        status.set("Not a valid outcome.")
        return

    # A fresh state creates a new round, regardless of the selector.
    state = {
        "title": title,
        "results": results,
        "choices": {},
    }

    try:
        ok = league.push(state)
    except (OSError, ValueError, KeyError, TypeError) as error:
        status.set(f"Post/save error. Check console: {error}")
        return

    if not ok:
        status.set("Post failed. Check console.")
        return

    reset_choice_form()

    try:
        refresh_rounds()
    except (OSError, ValueError, KeyError, TypeError) as error:
        status.set(f"Round posted; selector refresh failed: {error}")
        return

    status.set(f"Posted {round_var.get()}.")


def on_option(event=None):
    index = option_box.current()
    if not 0 <= index < len(current_options):
        return

    prompt = current_options[index][2]
    detail_var.set("")

    if prompt:
        detail_label_var.set(prompt)
        detail_entry.config(state="normal")
    else:
        detail_label_var.set("Detail (not needed)")
        detail_entry.config(state="disabled")

def match_saved(result, existing):
    for index, (_, template, prompt) in enumerate(OPTIONS[result]):
        if not prompt:
            if existing == template:
                return index, ""
            continue

        prefix, suffix = template.split("{}")
        if (
            existing.startswith(prefix)
            and existing.endswith(suffix)
            and len(existing) >= len(prefix) + len(suffix)
        ):
            return index, existing[len(prefix):len(existing) - len(suffix)]
    return None

def on_player(event=None):
    try:
        state = league.load_state()
    except (OSError, ValueError, KeyError, TypeError) as error:
        reset_choice_form()
        status.set(f"Could not load round: {error}")
        return

    if not state:
        reset_choice_form()
        status.set("Post or select a round first.")
        return

    player = player_var.get()
    result = state.get("results", {}).get(player)

    if result not in OPTIONS:
        reset_choice_form()
        status.set("This round has no valid result for that player.")
        return

    result_text.set(f"Result: {result}")
    current_options[:] = OPTIONS[result]
    option_box["values"] = [
        option[0] for option in current_options
    ]
    
    existing = state.get("choices", {}).get(player)
    index, detail = 0, ""
    if existing:
        found = match_saved(result, existing)
        if found:
            index, detail = found

    option_box.current(index)
    on_option()
    if detail:
        detail_var.set(detail)

    if existing:
        status.set(f"{player}'s saved choice: {existing}")
    else:
        status.set(f"Choose an option for {player}.")


def save_choice():
    player = player_var.get()
    index = option_box.current()

    if not player or not 0 <= index < len(current_options):
        status.set("Select a round and pick a player.")
        return

    try:
        state = league.load_state()
    except (OSError, ValueError, KeyError, TypeError) as error:
        status.set(f"Could not load round: {error}")
        return

    if not state:
        status.set("Post or select a round first.")
        return

    result = state.get("results", {}).get(player)
    if result not in OPTIONS or current_options != OPTIONS[result]:
        on_player()
        status.set("Round results changed. Pick your choice again.")
        return

    _, template, prompt = current_options[index]
    detail = detail_var.get().strip()

    if prompt and not detail:
        status.set(f"Enter the {prompt.lower()}.")
        return

    text = template.format(detail) if prompt else template
    state.setdefault("choices", {})[player] = text

    try:
        ok = league.push(state)
    except (OSError, ValueError, KeyError, TypeError) as error:
        status.set(f"Edit/save error. Check console: {error}")
        return

    if ok:
        status.set(f"{player} saved to {round_var.get()}.")
    else:
        status.set("Edit failed. Check console.")


round_box.bind("<<ComboboxSelected>>", on_round_selected)
player_box.bind("<<ComboboxSelected>>", on_player)
option_box.bind("<<ComboboxSelected>>", on_option)

ttk.Button(
    round_frame,
    text="Post round",
    command=post_round,
).grid(
    row=len(league.PLAYERS) + 1,
    column=1,
    sticky="e",
    pady=5,
)

ttk.Button(
    choice_frame,
    text="Save choice",
    command=save_choice,
).grid(row=3, column=1, sticky="e", pady=5)

ttk.Label(
    root,
    textvariable=status,
    wraplength=480,
).grid(row=3, column=0, padx=10, pady=(0, 10), sticky="w")

ttk.Button(
    history_frame, text="Reload", command=reload_all
).grid(row=0, column=2, padx=(10, 0))

try:
    pull()
    refresh_rounds()
    if round_var.get():
        status.set(f"Selected {round_var.get()}.")
    else:
        status.set("Post a round to get started.")
except (OSError, ValueError, KeyError, TypeError) as error:
    status.set(f"Could not load history: {error}")

root.mainloop()