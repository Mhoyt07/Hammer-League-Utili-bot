import tkinter as tk
from tkinter import ttk

import league

SCORES = ["2 - 0", "1 - 1", "0 - 2"]

OPTIONS = {
    "2 - 0": [("3 tournament packs", "3 'Tournament {}' Packs", "Pack number")],
    "1 - 1": [
        ("Open two sets of 24", "Open two sets of 24", None),
        ("Limit a card", "Limit '{}'", "Card name"),
    ],
    "0 - 2": [
        ("Reroll next set", "Reroll next set", None),
        ("Ban a card", "Ban '{}'", "Card name"),
    ],
}

root = tk.Tk()
root.title("Hammer League")
status = tk.StringVar()

# New round
round_frame = ttk.LabelFrame(root, text="New round", padding=10)
round_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

ttk.Label(round_frame, text="Title").grid(row=0, column=0, sticky="w")
title_var = tk.StringVar()
ttk.Entry(round_frame, textvariable=title_var, width=40).grid(row=0, column=1, pady=2)

result_vars = {}
for i, p in enumerate(league.PLAYERS, start=1):
    ttk.Label(round_frame, text=p).grid(row=i, column=0, sticky="w")
    v = tk.StringVar()
    ttk.Combobox(
        round_frame, textvariable=v, values=SCORES, state="readonly", width=8
    ).grid(row=i, column=1, sticky="w", pady=2)
    result_vars[p] = v


def post_round():
    results = {p: v.get() for p, v in result_vars.items()}
    if not title_var.get().strip() or "" in results.values():
        status.set("Fill in the title and all results.")
        return
    if sorted(results.values()) not in league.VALID:
        status.set("Not a valid outcome.")
        return
    ok = league.push(
        {"title": title_var.get().strip(), "results": results, "choices": {}}
    )
    status.set("Round posted." if ok else "Post failed. Check console.")
    if ok:
        player_var.set("")
        result_text.set("Result: -")
        option_box["values"] = []
        option_var.set("")
        current_options.clear()


ttk.Button(round_frame, text="Post round", command=post_round).grid(
    row=4, column=1, sticky="e", pady=5
)

# Add choice
choice_frame = ttk.LabelFrame(root, text="Add choice", padding=10)
choice_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

player_var = tk.StringVar()
result_text = tk.StringVar(value="Result: -")
option_var = tk.StringVar()
detail_var = tk.StringVar()
detail_label_var = tk.StringVar(value="Detail")
current_options = []

ttk.Label(choice_frame, text="Player").grid(row=0, column=0, sticky="w")
player_box = ttk.Combobox(
    choice_frame, textvariable=player_var, values=league.PLAYERS, state="readonly", width=12
)
player_box.grid(row=0, column=1, sticky="w", pady=2)
ttk.Label(choice_frame, textvariable=result_text).grid(row=0, column=2, padx=10)

ttk.Label(choice_frame, text="Option").grid(row=1, column=0, sticky="w")
option_box = ttk.Combobox(choice_frame, textvariable=option_var, state="readonly", width=28)
option_box.grid(row=1, column=1, columnspan=2, sticky="w", pady=2)

ttk.Label(choice_frame, textvariable=detail_label_var).grid(row=2, column=0, sticky="w")
detail_entry = ttk.Entry(choice_frame, textvariable=detail_var, width=30, state="disabled")
detail_entry.grid(row=2, column=1, columnspan=2, sticky="w", pady=2)


def on_option(event=None):
    idx = option_box.current()
    if idx < 0:
        return
    prompt = current_options[idx][2]
    detail_var.set("")
    if prompt:
        detail_label_var.set(prompt)
        detail_entry.config(state="normal")
    else:
        detail_label_var.set("Detail (not needed)")
        detail_entry.config(state="disabled")


def on_player(event=None):
    state = league.load_state()
    if not state:
        status.set("Post a round first.")
        return
    result = state["results"][player_var.get()]
    result_text.set(f"Result: {result}")
    current_options[:] = OPTIONS[result]
    option_box["values"] = [o[0] for o in current_options]
    option_box.current(0)
    on_option()


player_box.bind("<<ComboboxSelected>>", on_player)
option_box.bind("<<ComboboxSelected>>", on_option)


def save_choice():
    state = league.load_state()
    idx = option_box.current()
    if not state or not player_var.get() or idx < 0:
        status.set("Post a round and pick a player.")
        return
    _, template, prompt = current_options[idx]
    detail = detail_var.get().strip()
    if prompt and not detail:
        status.set(f"Enter the {prompt.lower()}.")
        return
    text = template.format(detail) if prompt else template
    state["choices"][player_var.get()] = text
    ok = league.push(state)
    status.set(f"{player_var.get()} saved." if ok else "Edit failed. Check console.")


ttk.Button(choice_frame, text="Save choice", command=save_choice).grid(
    row=3, column=1, sticky="e", pady=5
)

ttk.Label(root, textvariable=status).grid(row=2, column=0, pady=(0, 10))

root.mainloop()