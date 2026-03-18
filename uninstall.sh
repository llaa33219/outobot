#!/bin/bash
#
# OutO Uninstallation Script
# Completely removes OutO from the system
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

OUTOBOT_DIR="$HOME/.outobot"
SYSTEMD_SERVICE="$HOME/.config/systemd/user/outo.service"

echo -e "${RED}========================================${NC}"
echo -e "${RED}  OutO Uninstallation${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Check if installed
if [ ! -d "$OUTOBOT_DIR" ]; then
    echo -e "${YELLOW}OutO is not installed. Nothing to do.${NC}"
    exit 0
fi

echo -e "${YELLOW}This will remove:${NC}"
echo "  - $OUTOBOT_DIR (all data including sessions, config, logs)"
echo "  - $SYSTEMD_SERVICE (if exists)"
echo "  - Any symlinks to skills directories"
echo ""

read -p "Are you sure you want to uninstall OutO? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/5] Stopping OutO service...${NC}"
systemctl --user stop outo.service 2>/dev/null || true
echo -e "  Service stopped."

echo -e "${YELLOW}[2/5] Removing OutO directory...${NC}"
if [ -d "$OUTOBOT_DIR" ]; then
    rm -rf "$OUTOBOT_DIR"
    echo -e "  Removed: $OUTOBOT_DIR"
fi

echo -e "${YELLOW}[3/5] Removing systemd service...${NC}"
if [ -f "$SYSTEMD_SERVICE" ]; then
    systemctl --user disable outo.service 2>/dev/null || true
    rm -f "$SYSTEMD_SERVICE"
    echo -e "  Removed: $SYSTEMD_SERVICE"
fi

echo -e "${YELLOW}[4/5] Removing distrobox container...${NC}"
CONTAINER_NAME="arch-outobot"
if command -v distrobox &> /dev/null; then
    if distrobox list 2>/dev/null | grep -q "$CONTAINER_NAME"; then
        distrobox stop "$CONTAINER_NAME" 2>/dev/null || true
        distrobox rm "$CONTAINER_NAME" 2>/dev/null || true
        echo -e "  Removed container: $CONTAINER_NAME"
    else
        echo -e "  No container found."
    fi
else
    echo -e "  distrobox not available, skipping."
fi

echo -e "${YELLOW}[5/5] Removing skill symlinks and cleaning up...${NC}"
# Remove any symlinks in ~/.claude/skills/ that point to ~/.outobot/skills
if [ -d "$HOME/.claude/skills" ]; then
    for link in "$HOME/.claude/skills"/*; do
        if [ -L "$link" ]; then
            target=$(readlink -f "$link" 2>/dev/null || true)
            if [[ "$target" == *".outobot"* ]]; then
                rm -f "$link"
                echo -e "  Removed symlink: $link"
            fi
        fi
    done
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  OutO has been completely removed${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Thank you for using OutO!"
echo ""
