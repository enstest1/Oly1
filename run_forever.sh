#!/bin/bash
cd "$(dirname "$0")"

echo "Starting Oyl Corp Auto Clockin with auto-restart..."
echo "This script will restart the clockin script if it crashes"
echo "Press Ctrl+C to stop"

while true; do
    echo "$(date): Starting auto_clockin.py..."
    python auto_clockin.py
    echo "$(date): Script exited with code $?. Restarting in 30 seconds..."
    sleep 30
done 