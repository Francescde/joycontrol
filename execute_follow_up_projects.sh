#!/bin/sh
sudo chmod -R 777 .
if [ -d "./clientCtr" ]
then
    echo "./clientCtr exists on your filesystem."
    source clientCtr/bin/activate 
    pip install hidapi==0.7.99.post21 requests
    python3 controlAdapter/src/comandMap.py &
else
    echo "./clientCtr does not exist on your filesystem."
    sudo cp controlAdapter/udev/* /etc/udev/rules.d
    python3 -m venv clientCtr
    sleep 10
fi