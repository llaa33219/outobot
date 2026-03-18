#!/bin/bash
#
# OutObot Dev Reinstall Script
# Completely removes and reinstalls OutObot for testing
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  OutObot Dev Reinstall${NC}"
echo -e "${GREEN}  (For testing purposes)${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

echo -e "${YELLOW}[1/2] Uninstalling...${NC}"
bash "$SCRIPT_DIR/uninstall.sh"

echo ""
echo -e "${YELLOW}[2/2] Installing fresh...${NC}"
bash "$SCRIPT_DIR/install.sh"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Dev Reinstall Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "OutObot has been reset to fresh installation state."
echo ""
