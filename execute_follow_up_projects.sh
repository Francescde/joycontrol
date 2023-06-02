#!/bin/sh
sudo chmod -R 777 .
if [[ -d ./clientCtr ]]
then
    echo "./clientCtr exists on your filesystem."
    source /home/pi/joycontrol/clientCtr/bin/activate 
else
    echo "./clientCtr does not exist on your filesystem."
    sudo cp controlAdapter/udev/* /etc/udev/rules.d
    python3 -m venv clientCtr
    sleep 10
    source /home/pi/joycontrol/clientCtr/bin/activate
    sleep 10
    pip install hidapi==0.7.99.post21 requests
fi
sleep 10
python3 controlAdapter/src/comandMap.py &