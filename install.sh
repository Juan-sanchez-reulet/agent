#!/bin/bash
# Installs the visa monitor as a launchd background service.
# Run once after cloning: bash install.sh

set -e

INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_PATH="$(which python3)"
PYTHON_BIN_DIR="$(dirname "$PYTHON_PATH")"
HOME_DIR="$HOME"
PLIST_SRC="$INSTALL_DIR/com.visa.monitor.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.visa.monitor.plist"

# Substitute placeholders
sed \
  -e "s|INSTALL_DIR|$INSTALL_DIR|g" \
  -e "s|PYTHON_PATH|$PYTHON_PATH|g" \
  -e "s|PYTHON_BIN_DIR|$PYTHON_BIN_DIR|g" \
  -e "s|HOME_DIR|$HOME_DIR|g" \
  "$PLIST_SRC" > "$PLIST_DEST"

# Unload existing job if running
launchctl unload "$PLIST_DEST" 2>/dev/null || true

launchctl load "$PLIST_DEST"

echo "✓ Monitor installed and running."
echo "  Logs: $HOME/Library/Logs/visa-monitor.log"
echo "  Stop: launchctl unload $PLIST_DEST"
