# File: plugins/notepad.py

import os

NOTES_FILE = os.path.expanduser("~/.neuramatrix_notepad.txt")

def run():
    print("NeuraMatrix Smart Notepad")
    print("Type 'exit' to quit.")
    while True:
        try:
            line = input("> ")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        line = line.strip()
        if not line:
            continue
        if line.lower() == "exit":
            print("Bye!")
            break

        if line.lower().startswith("save "):
            note = line[5:].strip()
            if note:
                with open(NOTES_FILE, "a") as f:
                    f.write(note + "\n")
                print(f"Saved note: {note}")
            else:
                print("No note to save.")
        elif line.lower() == "show":
            if os.path.exists(NOTES_FILE):
                print("--- Notes ---")
                with open(NOTES_FILE) as f:
                    for idx, n in enumerate(f, 1):
                        print(f"{idx}. {n.strip()}")
                print("-------------")
            else:
                print("No notes yet.")
        else:
            print("Commands: 'save <note>', 'show', 'exit'")

if __name__ == "__main__":
    run()
