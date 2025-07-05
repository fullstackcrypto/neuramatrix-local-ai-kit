import json
import subprocess
from datetime import datetime

# === File Paths ===
profile_path = "profiles/charley.json"
memory_log_path = "memory/session_log.txt"

# === Load Profile ===
with open(profile_path, 'r') as f:
    profile = json.load(f)

name = profile.get("name", "User")
prefs = profile.get("preferences", {})
memory = profile.get("ai_memory", [])

# === Greet User ===
print(f"👋 Hello {name}!")
print(f"☕ Your coffee: {prefs.get('coffee', 'unknown')}")
print(f"🔔 Notifications: {prefs.get('notifications', 'none')}")
print(f"🧠 I remember: {', '.join(memory)}")
print("\nType your question (or 'exit'):")

# === Assistant Loop ===
while True:
    user_input = input("> You: ")
    if user_input.lower() in ["exit", "quit"]:
        break

    # === Send prompt to Ollama ===
    try:
        result = subprocess.run(
            ["ollama", "run", "mistral"],
            input=user_input.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=45
        )
        ai_response = result.stdout.decode().strip()
    except Exception as e:
        ai_response = f"(Error getting response from AI: {e})"

    # Show response
    print(f"🤖 NeuraMatrix: {ai_response}")

    # === Log Interaction ===
    now = datetime.now().strftime("[%Y-%m-%d %H:%M]")
    with open(memory_log_path, 'a') as log:
        log.write(f"{now} {name} asked: \"{user_input}\" → AI: \"{ai_response}\"\n")
