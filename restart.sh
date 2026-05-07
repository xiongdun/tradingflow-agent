#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
"$SCRIPT_DIR/stop.sh"
sleep 1
exec "$SCRIPT_DIR/start.sh"
