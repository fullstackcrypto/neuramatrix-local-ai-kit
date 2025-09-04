#!/bin/bash
<<<<<<< HEAD
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
=======

# NeuraMatrix Local AI Kit Installation Script
# Version 2.0 - Enhanced Security & Performance

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_MIN_VERSION="3.8"
NEURAMATRIX_USER="neuramatrix"
INSTALL_DIR="/opt/neuramatrix"
SERVICE_NAME="neuramatrix"
LOG_DIR="/var/log/neuramatrix"

echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        NeuraMatrix AI Kit v2.0       ║${NC}"
echo -e "${BLUE}║     Enhanced Installation Script     ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_status "Running with root privileges ✓"
    else
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_status "Linux system detected ✓"
    else
        print_error "This installer only supports Linux systems"
        exit 1
    fi
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        print_status "Python ${PYTHON_VERSION} detected ✓"
        
        # Version comparison
        if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"; then
            print_status "Python version is compatible ✓"
        else
            print_error "Python 3.8 or higher is required. Found: ${PYTHON_VERSION}"
            exit 1
        fi
    else
        print_error "Python3 is not installed"
        exit 1
    fi
    
    # Check pip
    if command -v pip3 &> /dev/null; then
        print_status "pip3 detected ✓"
    else
        print_error "pip3 is not installed"
        print_status "Install with: sudo apt-get install python3-pip"
        exit 1
    fi
    
    # Check git
    if command -v git &> /dev/null; then
        print_status "git detected ✓"
    else
        print_warning "git not found, installing..."
        apt-get update -qq
        apt-get install -y git
    fi
}

# Install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    apt-get update -qq
    
    # Essential packages
    PACKAGES=(
        "python3-venv"
        "python3-dev"
        "build-essential"
        "curl"
        "wget"
        "unzip"
        "sqlite3"
        "nginx"
        "supervisor"
    )
    
    for package in "${PACKAGES[@]}"; do
        if dpkg -l | grep -q "^ii  $package "; then
            print_status "$package already installed ✓"
        else
            print_status "Installing $package..."
            apt-get install -y "$package"
        fi
    done
}

# Create system user
create_user() {
    print_status "Creating system user..."
    
    if id "$NEURAMATRIX_USER" &>/dev/null; then
        print_status "User $NEURAMATRIX_USER already exists ✓"
    else
        useradd -r -s /bin/false -m -d "$INSTALL_DIR" "$NEURAMATRIX_USER"
        print_status "User $NEURAMATRIX_USER created ✓"
    fi
}

# Install Ollama
install_ollama() {
    print_status "Installing Ollama AI runtime..."
    
    if command -v ollama &> /dev/null; then
        print_status "Ollama already installed ✓"
    else
        curl -fsSL https://ollama.ai/install.sh | sh
        print_status "Ollama installed ✓"
    fi
    
    # Start Ollama service
    systemctl enable ollama
    systemctl start ollama
    
    # Wait for Ollama to be ready
    print_status "Waiting for Ollama to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:11434/api/version &>/dev/null; then
            print_status "Ollama is ready ✓"
            break
        fi
        sleep 2
    done
    
    # Download default model
    print_status "Downloading Mistral model (this may take a while)..."
    sudo -u ollama ollama pull mistral
    print_status "Mistral model installed ✓"
}

# Setup application
setup_application() {
    print_status "Setting up NeuraMatrix application..."
    
    # Create directories
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "${INSTALL_DIR}/uploads"
    mkdir -p "${INSTALL_DIR}/backups"
    mkdir -p "${INSTALL_DIR}/plugins"
    mkdir -p "${INSTALL_DIR}/data"
    
    # Set ownership
    chown -R "$NEURAMATRIX_USER:$NEURAMATRIX_USER" "$INSTALL_DIR"
    chown -R "$NEURAMATRIX_USER:$NEURAMATRIX_USER" "$LOG_DIR"
    
    # Copy application files
    if [ -d "$(dirname "$0")" ]; then
        print_status "Copying application files..."
        cp -r . "$INSTALL_DIR/"
        chown -R "$NEURAMATRIX_USER:$NEURAMATRIX_USER" "$INSTALL_DIR"
    fi
    
    # Create Python virtual environment
    print_status "Creating Python virtual environment..."
    sudo -u "$NEURAMATRIX_USER" python3 -m venv "$INSTALL_DIR/venv"
    
    # Install Python dependencies
    print_status "Installing Python dependencies..."
    sudo -u "$NEURAMATRIX_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
    sudo -u "$NEURAMATRIX_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
}

# Configure environment
configure_environment() {
    print_status "Configuring environment..."
    
    # Create environment file
    cat > "$INSTALL_DIR/.env" << EOF
# NeuraMatrix Configuration
FLASK_ENV=production
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
SECRET_KEY=$(openssl rand -hex 32)

# Database
DATABASE_URL=sqlite:///$INSTALL_DIR/data/neuramatrix.db

# Ollama Configuration
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
DEFAULT_MODEL=mistral

# Security
ALLOWED_HOSTS=127.0.0.1,localhost
MAX_FILE_SIZE=16777216

# Logging
LOG_LEVEL=INFO
EOF
    
    chown "$NEURAMATRIX_USER:$NEURAMATRIX_USER" "$INSTALL_DIR/.env"
    chmod 600 "$INSTALL_DIR/.env"
}

# Setup systemd service
setup_systemd_service() {
    print_status "Setting up systemd service..."
    
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=NeuraMatrix Local AI Kit
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=$NEURAMATRIX_USER
Group=$NEURAMATRIX_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python run.py
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateDevices=true
ProtectHome=true
ProtectSystem=strict
ReadWritePaths=$INSTALL_DIR $LOG_DIR

# Resource limits
LimitNOFILE=4096
LimitNPROC=512

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    print_status "Systemd service configured ✓"
}

# Setup nginx reverse proxy
setup_nginx() {
    print_status "Configuring Nginx reverse proxy..."
    
    cat > "/etc/nginx/sites-available/neuramatrix" << EOF
server {
    listen 80;
    server_name localhost;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=web:10m rate=1r/s;
    
    location / {
        limit_req zone=web burst=5 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    location /api/ {
        limit_req zone=api burst=10 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_
>>>>>>> e3a3054 (NeuraMatrix v2.0 - Complete security overhaul and modernization)
