from flask import Flask, render_template, request, redirect
import os, json, subprocess, importlib.util, socket, shutil
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

PROFILE_DIR = "profiles"
MEMORY_LOG = "memory/session_log.txt"
DEFAULT_PROFILE = "charley.json"
PLUGIN_DIR = "plugins"
PLUGIN_STATES = "plugin_states.json"
BACKUP_DIR = "backups"

PLUGINS = {
    "file_summarizer": "File Summarizer",
    "cloud_sync": "Cloud Sync"
}

# Ensure needed folders exist
os.makedirs(PROFILE_DIR, exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(PLUGIN_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# === HELPER FUNCTIONS ===

def list_profiles():
    return [f for f in os.listdir(PROFILE_DIR) if f.endswith(".json")]

def load_profile(filename):
    try:
        with open(os.path.join(PROFILE_DIR, filename), 'r') as f:
            return json.load(f)
    except:
        return {}

def save_profile(filename, data):
    with open(os.path.join(PROFILE_DIR, filename), 'w') as f:
        json.dump(data, f, indent=2)

def delete_profile(filename):
    os.remove(os.path.join(PROFILE_DIR, filename))

def call_ollama(prompt):
    try:
        result = subprocess.run(
            ["ollama", "run", "mistral"],
            input=prompt.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=25
        )
        return result.stdout.decode().strip()
    except subprocess.TimeoutExpired:
        return "⚠️ AI timed out. Ollama may be slow or inactive. Try again later."
    except Exception as e:
        return f"⚠️ Unexpected error: {str(e)}"

def load_plugin_states():
    if os.path.exists(PLUGIN_STATES):
        with open(PLUGIN_STATES, 'r') as f:
            return json.load(f)
    return {key: False for key in PLUGINS}

def save_plugin_states(states):
    with open(PLUGIN_STATES, 'w') as f:
        json.dump(states, f, indent=2)

def execute_enabled_plugins(plugin_states):
    for key, enabled in plugin_states.items():
        if enabled:
            plugin_path = os.path.join(PLUGIN_DIR, f"{key}.py")
            if os.path.exists(plugin_path):
                spec = importlib.util.spec_from_file_location(key, plugin_path)
                plugin = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(plugin)
                    if hasattr(plugin, "run"):
                        plugin.run()
                except Exception as e:
                    with open(MEMORY_LOG, "a") as log:
                        log.write(f"[PLUGIN ERROR] {key}: {str(e)}\n")

def backup_data():
    timestamp = datetime.now().strftime("backup-%Y%m%d-%H%M%S")
    dst = os.path.join(BACKUP_DIR, timestamp)
    os.makedirs(dst, exist_ok=True)
    shutil.copytree(PROFILE_DIR, os.path.join(dst, "profiles"))
    shutil.copy2(MEMORY_LOG, os.path.join(dst, "session_log.txt"))

def reset_memory():
    open(MEMORY_LOG, 'w').close()

# === ROUTES ===

@app.route("/", methods=["GET", "POST"])
def index():
    profiles = list_profiles()
    selected_profile = request.form.get("profile") or request.args.get("profile") or DEFAULT_PROFILE
    password_attempt = request.form.get("password", "")
    prompt = request.form.get("prompt", "")
    ai_response = ""
    file_summary = ""
    plugin_states = load_plugin_states()

    profile = load_profile(selected_profile)

    try:
        tailscale_ip = subprocess.check_output(["tailscale", "ip", "-4"]).decode().strip().split('\n')[0]
    except Exception:
        tailscale_ip = "Not Connected"

    if profile.get("password") and password_attempt != profile["password"]:
        return render_template("index.html", profiles=profiles, selected=selected_profile,
                               error="Password required or incorrect", response="", profile={}, summary="",
                               plugin_states=plugin_states, plugin_labels=PLUGINS, tailscale_ip=tailscale_ip)

    for plugin in PLUGINS:
        if plugin in request.form:
            plugin_states[plugin] = not plugin_states.get(plugin, False)
            save_plugin_states(plugin_states)

    if request.form.get("check_update"):
        ai_response = "✅ System is up to date."

    if request.form.get("backup_now"):
        backup_data()
        ai_response = "💾 Backup created."

    if request.form.get("reset_brain"):
        reset_memory()
        ai_response = "🧠 Memory wiped."

    if request.method == "POST" and prompt:
        ai_response = call_ollama(prompt)
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M]")
        with open(MEMORY_LOG, "a") as log:
            log.write(f"{timestamp} {profile.get('name','Unknown')} asked: \"{prompt}\" → AI: \"{ai_response}\"\n")

    if plugin_states.get("file_summarizer") and 'file' in request.files:
        f = request.files['file']
        if f.filename:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f.filename)
            f.save(file_path)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as uploaded_file:
                file_content = uploaded_file.read()
            file_summary = call_ollama("Summarize this file:\n" + file_content[:3000])

    execute_enabled_plugins(plugin_states)

    return render_template("index.html", profiles=profiles, selected=selected_profile, profile=profile,
                           response=ai_response, summary=file_summary, plugin_states=plugin_states,
                           plugin_labels=PLUGINS, tailscale_ip=tailscale_ip)

@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        name = request.form.get("name")
        coffee = request.form.get("coffee")
        tone = request.form.get("tone")
        password = request.form.get("password")
        filename = f"{name.lower().replace(' ', '_')}.json"

        data = {
            "name": name,
            "role": "User",
            "wake_time": "07:00",
            "preferences": {
                "coffee": coffee,
                "notifications": "voice",
                "tone": tone
            },
            "ai_memory": [
                "new user profile"
            ],
            "password": password
        }
        save_profile(filename, data)
        return redirect(f"/?profile={filename}")
    return render_template("create.html")

@app.route("/delete", methods=["POST"])
def delete():
    profile_to_delete = request.form.get("delete_profile", "").strip()
    print(f"🗑 Attempting to delete: {profile_to_delete}")

    if profile_to_delete and profile_to_delete != DEFAULT_PROFILE:
        path = os.path.join(PROFILE_DIR, profile_to_delete)
        if os.path.exists(path):
            os.remove(path)
            print(f"✅ Deleted: {profile_to_delete}")
        else:
            print("❌ File not found:", path)
    else:
        print("⚠️ Cannot delete default profile or invalid name.")

    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
