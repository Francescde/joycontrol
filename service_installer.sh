#!/bin/bash

SERVICE_NAME="my_startup"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
SCRIPT_PATH="/home/pi/joycontrol/startup_server.sh"

# Determine the username dynamically
USERNAME=$(logname)

# Create the systemd service file
cat <<EOF | sudo tee $SERVICE_FILE
[Unit]
Description=My Startup Service

[Service]
ExecStart=/bin/bash -c "sudo -u $USERNAME cd $PWD && sudo $SCRIPT_PATH"
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
