#!/bin/bash

SERVICE_NAME="my_joycon_server"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

# Determine the username dynamically
USERNAME=$(logname)
WORKING_DIRECTORY="/home/$USERNAME/joycontrol"

# Create the systemd service file
cat <<EOF | sudo tee $SERVICE_FILE
[Unit]
Description=My Startup Service

[Service]
WorkingDirectory=$WORKING_DIRECTORY
ExecStart=sudo python3 /home/$USERNAME/joycontrol/joycon_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Set permissions for the service file
sudo chmod 644 $SERVICE_FILE

# Enable and start the systemd service
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo "Systemd service created and enabled."
