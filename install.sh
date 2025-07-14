#!/bin/bash
# NeuraMatrix AI Kit Auto-Installer - Plug-and-Play for Everyone (July 13, 2025)

echo "NeuraMatrix setup starting automatically - Relax, no tech skills needed!"

# Auto-detect USB (non-savvy: assumes standard mount)
USB_MOUNT=$(findmnt -T . | grep /dev/sd | awk '{print $1}' || echo "/mnt/usb")
mkdir -p "$USB_MOUNT"
if ! mountpoint -q "$USB_MOUNT"; then
    sudo mkdir -p "$USB_MOUNT"
    sudo mount /dev/sdb1 "$USB_MOUNT"  # Adjust /dev/sdb1 to your USB device
fi
export OLLAMA_MODELS="$USB_MOUNT/.ollama/models"

# Symlink models
mkdir -p ~/.ollama
ln -sf "$OLLAMA_MODELS" ~/.ollama/models

# Install Ollama (offline-friendly: assume curl once, or pre-bundle)
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
fi
ollama pull mistral

# Venv and deps
python3 -m venv venv
source venv/bin/activate
pip install --quiet flask jinja2

# Folders
mkdir -p profiles memory plugins
touch memory/session_log.txt

# Auto-launch GUI
python gui_app.py &
sleep 5  # Wait for server
xdg-open http://localhost:5000 || firefox http://localhost:5000 || echo "Open browser to http://localhost:5000"

echo "AI Kit ready! Plug-and-play success. For help: support@neuramatrix.ai" > welcome.txt
xdg-open welcome.txt
