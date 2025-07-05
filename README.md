# NeuraMatrix™ AI Kit

**Version:** 1.0  
**Author:** CHARLEY’S LLC / Ready-Set Solutions  
**Repo:** https://github.com/fullstackcrypto/neuramatrix-local-ai-kit  

---

## 🔧 What It Is
NeuraMatrix is a fully offline, modular AI assistant kit that runs on a Thin Client or USB-powered device. It uses a locally hosted language model (LLM), voice, vision, and a sci-fi-inspired GUI to serve as a plug-and-play smart console.

**Inspired by Knight Rider’s KITT interface**, NeuraMatrix delivers:

- 🧠 On-device local AI using Ollama + Mistral
- 👤 Per-user profiles + memory
- 📄 File upload & summarizer
- 🧩 Plugin toggle panel
- 🔁 System tools (backup, reset, updates)
- 📡 Secure remote access via Tailscale
- 🎛️ Futuristic sci-fi GUI (Arwes/KITT themed)

---

## 🛠️ Features

| Feature              | Description                                |
|----------------------|--------------------------------------------|
| ✅ Offline AI        | Uses Mistral model via Ollama               |
| ✅ GUI               | Flask + HTML5 + Orbitron font               |
| ✅ File Upload       | Upload `.txt` and receive AI summaries      |
| ✅ Profiles          | JSON-based per-user memory + preferences    |
| ✅ Plugins           | Dynamically loaded from `/plugins/`         |
| ✅ System Panel      | Check updates, back up data, wipe memory   |
| ✅ Remote Access     | Connect from anywhere using Tailscale       |
| ✅ Auto-Boot Ready   | Systemd service auto-launches Flask on boot|

---

## 🧠 How It Works

```bash
Thin Client boots Ubuntu → auto-starts Flask GUI
→ Loads profile → Accepts voice/file/plugin input
→ Returns AI output via local LLM → Optional remote access via Tailscale
```

---

## 💡 Requirements
- Ubuntu Linux (20.04+)
- Python 3.10+ with `venv`
- Ollama (installed via script)
- Flask, Jinja2
- Tailscale (optional remote access)

---

## 🔗 Quickstart (CLI)
```bash
git clone https://github.com/fullstackcrypto/neuramatrix-local-ai-kit
cd neuramatrix-local-ai-kit
python3 -m venv venv
source venv/bin/activate
pip install flask
bash install.sh (optional)
sudo systemctl start neuramatrix
```

GUI: `http://localhost:5000` or `http://<tailscale-ip>:5000`

---

## 📁 Folder Structure
```
neuramatrix/
├── gui_app.py
├── templates/index.html
├── profiles/charley.json
├── memory/session_log.txt
├── plugins/cloud_sync.py
├── plugin_states.json
├── uploads/
└── backups/
```

---

## 📦 Coming Soon
- Audio in/out support
- Visual camera plugins
- Real-time chat mode
- Pre-flashed USB and ISO image builder

---

## 🔒 Disclaimer
This system runs completely offline by default. Remote access is encrypted via Tailscale. No cloud processing is used unless plugin-enabled.

---

## 🚀 Made with ♥ by CHARLEY'S LLC / NeuraMatrix.ai
