#!/bin/sh
if [ -d "./server" ]
then
    echo "./server exists on your filesystem."
    . server/bin/activate 
else
    sudo apt install python3-dbus libhidapi-hidraw0 libbluetooth-dev bluez python3-pip python3-venv
    sudo apt-get install rustc
    echo "./server does not exist on your filesystem."
    python3 -m venv server
    sleep 10
    . server/bin/activate 
    sleep 10
    sudo pip3 install aioconsole hid crc8
    sudo pip3 install aioflask
    sudo pip3 install Flask==2
    sudo pip3 install cryptography==3.3.2
    sudo pip3 install pyamiibo
    # Assign the attributes to a variable
    attributes="-C -P sap,input,avrcp"

    # Check if the attributes are already added to the ExecStart line
    if grep -q "ExecStart.*$attributes" /lib/systemd/system/bluetooth.service; then
        echo "Attributes already added to ExecStart line."
    else
        # Find the ExecStart line in the bluetooth.service file and append the attributes
        sudo sed -i "s/^ExecStart.*/& $attributes/g" /lib/systemd/system/bluetooth.service
        sudo systemctl daemon-reload
        sudo systemctl restart bluetooth.service
        echo "Attributes added to ExecStart line."
    fi
fi
