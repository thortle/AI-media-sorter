#!/bin/bash
# Manage Moondream service
# Usage: ./manage_service.sh {start|stop|restart|status|logs}

PLIST_PATH="$HOME/Library/LaunchAgents/com.photoserver.moondream.plist"
SERVICE_NAME="com.photoserver.moondream"
LOG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$1" in
    start)
        echo "🚀 Starting Moondream service..."
        launchctl load "$PLIST_PATH"
        sleep 1
        $0 status
        ;;
    stop)
        echo "⏹  Stopping Moondream service..."
        launchctl unload "$PLIST_PATH" 2>/dev/null || echo "Service not running"
        ;;
    restart)
        echo "🔄 Restarting Moondream service..."
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        if launchctl list | grep -q "$SERVICE_NAME"; then
            echo "✅ Moondream service is RUNNING"
            echo ""
            echo "Process info:"
            launchctl list | grep "$SERVICE_NAME"
            echo ""
            echo "Recent log entries:"
            tail -5 "$LOG_DIR/moondream.log" 2>/dev/null || echo "No logs yet"
        else
            echo "❌ Moondream service is NOT RUNNING"
            echo ""
            echo "To start: $0 start"
        fi
        ;;
    logs)
        echo "📋 Moondream logs (Ctrl+C to exit):"
        tail -f "$LOG_DIR/moondream.log"
        ;;
    errors)
        echo "⚠️  Moondream errors:"
        cat "$LOG_DIR/moondream.error.log"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|errors}"
        exit 1
        ;;
esac
