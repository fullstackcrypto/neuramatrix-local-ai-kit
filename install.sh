#!/bin/bash

echo "🧠 Starting NeuraMatrix Local AI Setup..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install curl git -y

# Install Ollama (local LLM runtime)
curl -fsSL https://ollama.com/install.sh | sh

# Pull LLaMA 3 model
ollama pull llama3

# Create test chat script
cat <<EOF > chat.sh
#!/bin/bash
echo "🧠 Starting local chat (LLaMA3)..."
ollama run llama3
EOF

chmod +x chat.sh

echo "✅ Setup complete. Run './chat.sh' to start chatting with your local AI!"
