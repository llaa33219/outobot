#!/bin/bash
#
# OutObot Uninstallation Script
# Completely removes OutObot from the system
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

OUTOBOT_DIR="$HOME/.outobot"
SYSTEMD_SERVICE="$HOME/.config/systemd/user/outo.service"
NEO4J_SERVICE="$HOME/.config/systemd/user/neo4j-outobot.service"

echo -e "${RED}========================================${NC}"
echo -e "${RED}  OutObot Uninstallation${NC}"
echo -e "${RED}========================================${NC}"
echo ""

if [ ! -d "$OUTOBOT_DIR" ]; then
    echo -e "${YELLOW}OutObot is not installed. Nothing to do.${NC}"
    exit 0
fi

NON_INTERACTIVE=false
FORCE_REMOVE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -y|--yes)
            FORCE_REMOVE=true
            ;;
        -f|--force)
            FORCE_REMOVE=true
            ;;
        -n|--non-interactive)
            NON_INTERACTIVE=true
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
    shift
done

if [ "$FORCE_REMOVE" = false ] && [ "$NON_INTERACTIVE" = false ]; then
    echo -e "${YELLOW}This will remove:${NC}"
    echo "  - $OUTOBOT_DIR (all data including sessions, config, logs)"
    echo "  - $SYSTEMD_SERVICE (if exists)"
    echo "  - $NEO4J_SERVICE (if exists)"
    echo "  - Neo4j distrobox container (outobot-neo4j)"
    echo "  - Skills distrobox container (arch-outobot)"
    echo "  - Any symlinks to skills directories"
    echo ""

    read -p "Are you sure you want to uninstall OutObot? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        echo "Cancelled."
        exit 0
    fi
elif [ "$FORCE_REMOVE" = false ]; then
    echo "Cancelled (non-interactive mode without --force or --yes)."
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/6] Stopping OutObot service...${NC}"
systemctl --user stop outo.service 2>/dev/null || true
echo -e "  Service stopped."

echo -e "${YELLOW}[2/6] Stopping Neo4j service...${NC}"
systemctl --user stop neo4j-outobot.service 2>/dev/null || true
echo -e "  Neo4j service stopped."

echo -e "${YELLOW}[3/6] Removing OutObot directory...${NC}"
if [ -d "$OUTOBOT_DIR" ]; then
    rm -rf "$OUTOBOT_DIR"
    echo -e "  Removed: $OUTOBOT_DIR"
fi

echo -e "${YELLOW}[4/6] Removing systemd services...${NC}"
if [ -f "$SYSTEMD_SERVICE" ]; then
    systemctl --user disable outo.service 2>/dev/null || true
    rm -f "$SYSTEMD_SERVICE"
    echo -e "  Removed: $SYSTEMD_SERVICE"
fi
if [ -f "$NEO4J_SERVICE" ]; then
    systemctl --user disable neo4j-outobot.service 2>/dev/null || true
    rm -f "$NEO4J_SERVICE"
    echo -e "  Removed: $NEO4J_SERVICE"
fi
systemctl --user daemon-reload 2>/dev/null || true

echo -e "${YELLOW}[5/6] Removing containers...${NC}"

CONTAINER_CMD=""
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
fi

if [ -n "$CONTAINER_CMD" ]; then
    if $CONTAINER_CMD ps -a --format "{{.Names}}" 2>/dev/null | grep -q "^outobot-neo4j$"; then
        echo -e "  Stopping and removing Neo4j container..."
        $CONTAINER_CMD stop outobot-neo4j 2>/dev/null || true
        $CONTAINER_CMD rm outobot-neo4j 2>/dev/null || true
        echo -e "  Removed container: outobot-neo4j"
    else
        echo -e "  No Neo4j container found."
    fi
else
    echo -e "  Neither podman nor docker available, skipping."
fi

if command -v distrobox &> /dev/null; then
    if distrobox list 2>/dev/null | grep -q "arch-outobot"; then
        echo -e "  Stopping and removing skills container..."
        distrobox stop arch-outobot 2>/dev/null || true
        distrobox rm arch-outobot 2>/dev/null || true
        echo -e "  Removed container: arch-outobot"
    else
        echo -e "  No skills container found."
    fi
fi

echo -e "${YELLOW}[6/6] Removing skill symlinks and cleaning up...${NC}"
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
echo -e "${GREEN}  OutObot has been completely removed${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Thank you for using OutObot!"
echo ""
