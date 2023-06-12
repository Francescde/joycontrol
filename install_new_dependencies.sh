#!/bin/sh
sudo chmod -R 777 .
if [ -d "./server" ]
then
    echo "./server exists on your filesystem."
    . server/bin/activate 
else
    echo "./server does not exist on your filesystem."
    python3 -m venv server
    sleep 10
    . server/bin/activate 
    sleep 10
    sudo pip3 install aioconsole hid crc8
    sudo pip3 install aioflask
    sudo pip3 install Flask==2
    # Assign the attributes to a variable
    attributes="-C -P sap,input,avrcp"

    # Find the ExecStart line in the bluetooth.service file and append the attributes
    sudo sed -i "s/^ExecStart.*/& $attributes/g" /lib/systemd/system/bluetooth.service
    sudo systemctl daemon-reload
    sudo systemctl restart bluetooth.service
    # Define the line to be appended
    line_to_append="sudo /home/pi/joycontrol/startup_server.sh &"

    # Check if the line already exists in the file
    if grep -Fxq "$line_to_append" /etc/rc.local; then
        echo "Line already exists in /etc/rc.local. No changes made."
    else
        # Append the line before the 'exit' line
        sudo sed -i "/^exit/i $line_to_append" /etc/rc.local
        echo "Line appended to /etc/rc.local."
    fi
fi
