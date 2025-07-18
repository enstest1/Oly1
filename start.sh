#!/bin/bash
set -e

# Install Oyl CLI globally
npm install -g @oyl/sdk

# Optionally, print the Oyl version to logs for verification
oyl --version

# Start the clock-in script
python auto_clockin.py 