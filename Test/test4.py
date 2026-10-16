import history
h = history.pull()
print(h["revision"], h["selected_id"], len(h["rounds"]))