#!/bin/bash

set -e # Exit on any error

# Make the run script executable
chmod +x run-wafflebot.sh

# Copy systemd files to the correct location
sudo cp systemd/homelab-run-wafflebot.service /etc/systemd/system/
sudo cp systemd/homelab-run-wafflebot.timer /etc/systemd/system/
sudo cp systemd/homelab-run-wafflebot-staging.service /etc/systemd/system/
sudo cp systemd/homelab-run-wafflebot-staging.timer /etc/systemd/system/

# Reload systemd to recognize new files
sudo systemctl daemon-reload

# Enable and start the timers
sudo systemctl enable homelab-run-wafflebot.timer
sudo systemctl start homelab-run-wafflebot.timer
sudo systemctl enable homelab-run-wafflebot-staging.timer
sudo systemctl start homelab-run-wafflebot-staging.timer

echo "WaffleBot systemd services and timers have been installed and started."
echo "Production (4am): systemctl status homelab-run-wafflebot.timer"
echo "Staging (10pm): systemctl status homelab-run-wafflebot-staging.timer"
echo "Production logs: journalctl -u homelab-run-wafflebot"
echo "Staging logs: journalctl -u homelab-run-wafflebot-staging"
