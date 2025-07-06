# NeuraMatrix™ AI Kit

**Version:** 1.0  
**Author:** CHARLEYS LLC  
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
├── assistant_core.py
├── backups
│   ├── backup-20250705-215336
│   └── backup-20250705-215603
├── gui_app.py
├── install.sh
├── LICENSE
├── memory
│   └── session_log.txt
├── np
├── plugins
│   ├── cloud_sync.py
│   ├── daily_summary.py
│   ├── __init__.py
│   ├── notepad.py
│   └── __pycache__
├── plugin_states.json
├── profiles
│   ├── calvin.json
│   └── charley.json
├── README.md
├── templates
│   ├── create.html
│   └── index.html
├── uploads
└── venv
    ├── bin
    ├── include
    ├── lib
    ├── lib64 -> lib
    └── pyvenv.cfg

15 directories, 17 files

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
