#!/bin/bash

set -e # Exit on any error

# Make the run script executable
chmod +x run-wafflebot.sh

# Copy systemd files to the correct location
sudo cp systemd/homelab-run-wafflebot.service /etc/systemd/system/
sudo cp systemd/homelab-run-wafflebot.timer /etc/systemd/system/

# Reload systemd to recognize new files
sudo systemctl daemon-reload

# Enable and start the timer
sudo systemctl enable homelab-run-wafflebot.timer
sudo systemctl start homelab-run-wafflebot.timer

echo "WaffleBot systemd service and timer have been installed and started."
echo "You can check the status with: systemctl status homelab-run-wafflebot.timer"
echo "You can check the logs with: journalctl -u homelab-run-wafflebot"
