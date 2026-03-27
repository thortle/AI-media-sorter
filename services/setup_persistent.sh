#!/bin/bash
# Setup script for persistent Moondream service on macOS
# This ensures the service keeps running even when the Mac sleeps

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_FILE="$SCRIPT_DIR/com.photoserver.moondream.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
INSTALLED_PLIST="$LAUNCH_AGENTS_DIR/com.photoserver.moondream.plist"

echo "🔧 Setting up persistent Moondream service..."

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCH_AGENTS_DIR"

# Stop existing service if running
if launchctl list | grep -q com.photoserver.moondream; then
    echo "⏹  Stopping existing service..."
    launchctl unload "$INSTALLED_PLIST" 2>/dev/null || true
fi

# Copy plist to LaunchAgents
echo "📋 Installing service configuration..."
cp "$PLIST_FILE" "$INSTALLED_PLIST"

# Load the service
echo "🚀 Starting service..."
launchctl load "$INSTALLED_PLIST"

# Wait a moment and check status
sleep 2
if launchctl list | grep -q com.photoserver.moondream; then
    echo "✅ Moondream service installed and running!"
    echo ""
    echo "Service details:"
    echo "  - Will start automatically on login"
    echo "  - Will keep running when Mac sleeps"
    echo "  - Will restart automatically if it crashes"
    echo "  - Logs: $SCRIPT_DIR/moondream.log"
    echo "  - Errors: $SCRIPT_DIR/moondream.error.log"
    echo ""
    echo "Useful commands:"
    echo "  Stop:    launchctl unload $INSTALLED_PLIST"
    echo "  Start:   launchctl load $INSTALLED_PLIST"
    echo "  Status:  launchctl list | grep moondream"
    echo "  Logs:    tail -f $SCRIPT_DIR/moondream.log"
else
    echo "❌ Service failed to start. Check error log:"
    echo "   cat $SCRIPT_DIR/moondream.error.log"
    exit 1
fi
