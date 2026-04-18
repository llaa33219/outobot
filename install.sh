#!/bin/bash
#
# OutObot Installation Script
# Sets up the OutObot multi-agent AI system
#

# Don't exit on error - continue through issues
# set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

OUTOBOT_DIR="$HOME/.outobot"
OUTOBOT_VENV="$OUTOBOT_DIR/venv"
OUTOBOT_BIN="$OUTOBOT_VENV/bin"

# Version tracking
VERSION_FILE="$OUTOBOT_DIR/.version"
CURRENT_VERSION="1.0.0"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  OutObot Installation${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check for required system packages
check_dependencies() {
    local missing=0
    
    echo -e "${YELLOW}[1/6] Checking system dependencies...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}ERROR: Python 3 is not installed.${NC}"
        echo "Please install Python 3.11 or higher:"
        echo "  Arch: sudo pacman -S python"
        echo "  Ubuntu/Debian: sudo apt install python3"
        echo "  macOS: brew install python3"
        missing=1
    else
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        echo -e "  Python: ${GREEN}✓${NC} ($PYTHON_VERSION)"
    fi
    
    # Check pip (optional - will be available in distrobox container)
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        echo -e "${YELLOW}  WARNING: pip not found on host. Python dependencies will be installed in distrobox container.${NC}"
    else
        echo -e "  pip: ${GREEN}✓${NC}"
    fi
    
    # Check distrobox (REQUIRED for container isolation)
    if ! command -v distrobox &> /dev/null; then
        echo -e "${RED}ERROR: distrobox is required but not installed.${NC}"
        echo ""
        echo "OutObot requires distrobox for secure container isolation."
        echo "To install:"
        echo ""
        echo "  # Arch Linux"
        echo "  sudo pacman -S podman distrobox"
        echo ""
        echo "  # Ubuntu/Debian"
        echo "  sudo apt install podman distrobox"
        echo ""
        echo "  # Fedora"
        echo "  sudo dnf install podman distrobox"
        echo ""
        echo "  See: https://distrobox.itsness.org/"
        echo ""
        missing=1
    else
        echo -e "  distrobox: ${GREEN}✓${NC}"
    fi
    
    # Check git
    if ! command -v git &> /dev/null; then
        echo -e "${YELLOW}  WARNING: git not found. Some features may not work.${NC}"
    else
        echo -e "  git: ${GREEN}✓${NC}"
    fi
    
    # npm/npx will be available in distrobox container
    
    # Check bun (optional - for skills-cli)
    if ! command -v bun &> /dev/null; then
        echo -e "${YELLOW}  WARNING: bun not found. For best skill sync experience, install from https://bun.sh${NC}"
    else
        echo -e "  bun: ${GREEN}✓${NC}"
    fi
    
    if [ $missing -eq 1 ]; then
        echo ""
        echo -e "${RED}Installation aborted. Please install missing dependencies.${NC}"
        exit 1
    fi
}

# Create OutObot directory structure
setup_directory() {
    # Check if already installed
    if [ -d "$OUTOBOT_DIR" ] && [ -f "$VERSION_FILE" ]; then
    echo -e "\n${YELLOW}[2/6] Updating existing installation...${NC}"
    echo -e "  User settings will be preserved."
else
    echo -e "\n${YELLOW}[2/6] Setting up directory structure...${NC}"
    fi
    
    # Create main directory
    mkdir -p "$OUTOBOT_DIR"
    
    # Create subdirectories (only if not exist)
    mkdir -p "$OUTOBOT_DIR/agents"
    mkdir -p "$OUTOBOT_DIR/logs"
    
    # Preserve skills directory if exists, otherwise create empty one
    if [ ! -d "$OUTOBOT_DIR/skills" ]; then
        mkdir -p "$OUTOBOT_DIR/skills"
    fi
    
    # Preserve config directory if exists
    if [ ! -d "$OUTOBOT_DIR/config" ]; then
        mkdir -p "$OUTOBOT_DIR/config"
    fi
    
    # Preserve sessions directory if exists
    if [ ! -d "$OUTOBOT_DIR/sessions" ]; then
        mkdir -p "$OUTOBOT_DIR/sessions"
    fi
    
    echo -e "  Directory structure ready (user data preserved)"
}

# Copy source files to OutObot directory
copy_source_files() {
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Check if this is an update (existing installation)
    IS_UPDATE=false
    if [ -d "$OUTOBOT_DIR" ] && [ -f "$OUTOBOT_DIR/.version" ]; then
        IS_UPDATE=true
    fi
    
    echo -e "\n${YELLOW}[2.5/6] Copying source files...${NC}"
    
    # On update: clean up old source files first for a fresh sync
    # User data directories are preserved
    if [ "$IS_UPDATE" = true ]; then
        echo -e "  Cleaning up old source files for fresh sync..."
        
        for item in "$OUTOBOT_DIR"/*; do
            [ -e "$item" ] || continue
            basename_item=$(basename "$item")
            
            case "$basename_item" in
                config|skills|sessions|venv|logs|note|.version)
                    echo -e "    Preserved: $basename_item/"
                    ;;
                run.sh|uninstall.sh)
                    rm -f "$item"
                    echo -e "    Removed: $basename_item (will be regenerated)"
                    ;;
                *)
                    if [ -d "$item" ]; then
                        rm -rf "$item"
                        echo -e "    Removed: $basename_item/"
                    else
                        rm -f "$item"
                        echo -e "    Removed: $basename_item"
                    fi
                    ;;
            esac
        done
    fi
    
    # Copy source files fresh
    SYNC_ITEMS="run.py outo LICENSE ai-docs logo.svg static uninstall.sh"
    
    for item in $SYNC_ITEMS; do
        if [ -e "$SCRIPT_DIR/$item" ]; then
            cp -r "$SCRIPT_DIR/$item" "$OUTOBOT_DIR/"
            echo -e "  Synced: $item"
        fi
    done
    
    # Clean up Python bytecode cache to prevent stale .pyc issues
    find "$OUTOBOT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$OUTOBOT_DIR" -name "*.pyc" -delete 2>/dev/null || true
    
    # Ensure note directory exists
    mkdir -p "$OUTOBOT_DIR/note"
    
    echo -e "  Source files ready"
}

# Setup Python virtual environment
setup_venv() {
    echo -e "\n${YELLOW}[3/6] Setting up Python virtual environment...${NC}"
    
    if [ -d "$OUTOBOT_VENV" ]; then
        echo -e "  Virtual environment already exists."
        
        # Check for version update
        if [ -f "$VERSION_FILE" ]; then
            INSTALLED_VERSION=$(cat "$VERSION_FILE")
            if [ "$INSTALLED_VERSION" != "$CURRENT_VERSION" ]; then
                echo -e "  ${YELLOW}Version update detected: $INSTALLED_VERSION -> $CURRENT_VERSION${NC}"
                echo -e "  Upgrading packages..."
                "$OUTOBOT_BIN/pip" install --upgrade agentouto fastapi 'uvicorn[standard]' python-multipart aiohttp pydantic wsproto websockets discord.py outowiki
            else
                echo -e "  Already up to date."
            fi
        fi
    else
        echo -e "  Creating virtual environment..."
        python3 -m venv "$OUTOBOT_VENV"
        echo -e "  Virtual environment created."
        
        # Install dependencies (venv includes pip by default in modern Python)
        echo -e "  Installing dependencies..."
        "$OUTOBOT_BIN/pip" install --upgrade pip
        "$OUTOBOT_BIN/pip" install agentouto outowiki
        "$OUTOBOT_BIN/pip" install fastapi 'uvicorn[standard]' python-multipart outowiki
        "$OUTOBOT_BIN/pip" install aiohttp pydantic outowiki
        "$OUTOBOT_BIN/pip" install wsproto websockets outowiki
        "$OUTOBOT_BIN/pip" install discord.py outowiki
    fi
    
    # Save version
    echo "$CURRENT_VERSION" > "$VERSION_FILE"
}

# Create run script
setup_run_script() {
    echo -e "\n${YELLOW}[4/6] Creating run scripts...${NC}"
    
    # Main run script
    cat > "$OUTOBOT_DIR/run.sh" << 'SCRIPT'
#!/bin/bash
# OutObot Runner Script
# Launches the OutObot server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_BIN="$SCRIPT_DIR/venv/bin"

# Activate venv and run
source "$VENV_BIN/activate"
cd "$SCRIPT_DIR"
exec python3 run.py "$@"
SCRIPT
    
    chmod +x "$OUTOBOT_DIR/run.sh"
    echo -e "  Created: $OUTOBOT_DIR/run.sh"
    
    # Create systemd service for auto-start
    mkdir -p "$HOME/.config/systemd/user"
    cat > "$HOME/.config/systemd/user/outo.service" << 'SERVICE'
[Unit]
Description=OutObot Multi-Agent AI System
After=network.target

[Service]
Type=simple
WorkingDirectory=%h/.outobot
ExecStart=%h/.outobot/run.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
SERVICE
    
    echo -e "  Created: $HOME/.config/systemd/user/outo.service"
    echo -e ""
    echo -e "  To enable auto-start: systemctl --user enable outo.service"
}

# Create sample configuration
setup_config() {
    echo -e "\n${YELLOW}[5/6] Creating sample configuration...${NC}"
    
    # Sample config.yaml
    if [ ! -f "$OUTOBOT_DIR/config/config.yaml" ]; then
        cat > "$OUTOBOT_DIR/config/config.yaml" << 'CONFIG'
# OutObot Configuration
# Edit this file to configure your agents and providers

server:
  host: "localhost"
  port: 7227
  
# Provider configurations
# Add your API keys here
providers:
  openai:
    enabled: false
    api_key: ""
    # models: gpt-5.2, gpt-5.3-codex, o3, o4-mini
    
  anthropic:
    enabled: false
    api_key: ""
    # models: claude-opus-4-6, claude-sonnet-4-6
    
  google:
    enabled: false
    api_key: ""
    # models: gemini-3.1-pro, gemini-3-flash
    
  # For local models (Ollama, vLLM, LM Studio)
  local:
    enabled: false
    base_url: "http://localhost:11434/v1"
    api_key: "not-needed"
    # models: llama3, mistral, etc.

# Agent configurations
agents:
  outo:
    model: "gpt-5.2"
    provider: "openai"
    temperature: 1.0
    
  peritus:
    model: "claude-sonnet-4-6"
    provider: "anthropic"
    temperature: 0.9
    
  inquisitor:
    model: "gpt-5.2"
    provider: "openai"
    temperature: 0.8
    
  rimor:
    model: "gpt-5.2"
    provider: "openai"
    temperature: 0.7
    
  recensor:
    model: "claude-sonnet-4-6"
    provider: "anthropic"
    temperature: 0.6
    
  cogitator:
    model: "gemini-3.1-pro"
    provider: "google"
    temperature: 1.0
    
  creativus:
    model: "gpt-5.2"
    provider: "openai"
    temperature: 1.2
    
  artifex:
    model: "gpt-5.2"
    provider: "openai"
    temperature: 1.1

# UI Settings
ui:
  theme: "neo-brutalism"
  title: "OutObot - Multi-Agent AI System"
  session_timeout: 3600
CONFIG
        echo -e "  Created: $OUTOBOT_DIR/config/config.yaml"
    fi
    
    # Create .env example
    if [ ! -f "$OUTOBOT_DIR/config/.env.example" ]; then
        cat > "$OUTOBOT_DIR/config/.env.example" << 'ENV'
# OutObot Environment Variables
# Copy this to .env and fill in your API keys

# OpenAI API Key
OPENAI_API_KEY=sk-your-openai-key-here

# Anthropic API Key  
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Google API Key
GOOGLE_API_KEY=AIza-your-google-key-here
ENV
        echo -e "  Created: $OUTOBOT_DIR/config/.env.example"
    fi
}

# Setup distrobox container for skills (npx support)
setup_distrobox() {
    echo -e "\n${YELLOW}[6/7] Setting up distrobox container for skills...${NC}"
    
    CONTAINER_NAME="arch-outobot"
    
    if command -v distrobox &> /dev/null; then
        if distrobox list 2>/dev/null | grep -q "$CONTAINER_NAME"; then
            echo -e "  Container '$CONTAINER_NAME' already exists."
        else
            echo -e "  Creating container '$CONTAINER_NAME'..."
            distrobox create --name "$CONTAINER_NAME" --image archlinux:latest --yes 2>/dev/null || \
            distrobox create --name "$CONTAINER_NAME" --image archlinux:base --yes 2>/dev/null || {
                echo -e "  ${YELLOW}Warning: Could not create distrobox container. Installing nodejs manually...${NC}"
            }
        fi
        
        if distrobox list 2>/dev/null | grep -q "$CONTAINER_NAME"; then
            echo -e "  Container ready. Installing nodejs and npm..."
            distrobox enter --name "$CONTAINER_NAME" -- sudo pacman -Sy --noconfirm nodejs npm 2>/dev/null || \
                echo -e "  ${YELLOW}Warning: Could not install nodejs in container${NC}"
            echo -e "  Distrobox container ready for skills!"
        fi
    else
        echo -e "  ${YELLOW}Warning: distrobox not available. Skipping container setup.${NC}"
    fi
}


# Auto-start the service
auto_start() {
    echo -e "\n${YELLOW}[6/6] Starting OutObot service...${NC}"
    
    if systemctl --user list-unit-files outo.service &>/dev/null; then
        systemctl --user enable outo.service
        systemctl --user start outo.service
        
        sleep 2
        
        if systemctl --user is-active --quiet outo.service; then
            echo -e "  OutObot service started successfully!"
            echo -e "  Open http://localhost:7227 in your browser"
        else
            echo -e "  ${YELLOW}Warning: Service started but may not be ready yet.${NC}"
            echo -e "  Try: systemctl --user status outo.service"
        fi
    else
        echo -e "  ${YELLOW}Warning: Could not auto-start service.${NC}"
    fi
}

# Main execution
main() {
    check_dependencies
    setup_directory
    copy_source_files
    setup_venv
    setup_run_script
    setup_config
    setup_distrobox

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Installation Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "OutObot is starting automatically..."
    echo "Open http://localhost:7227 in your browser"
    echo ""
    echo "To manage the service:"
    echo "  Status: systemctl --user status outo.service"
    echo "  Stop:   systemctl --user stop outo.service"
    echo "  Restart: systemctl --user restart outo.service"
    echo ""
    
    auto_start
}

main "$@"
