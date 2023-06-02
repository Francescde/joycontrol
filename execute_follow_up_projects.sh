#!/bin/sh
sudo chmod -R 777 .
if [ -d "./clientCtr" ]
then
    echo "./clientCtr exists on your filesystem."
    . clientCtr/bin/activate 
    pip install hidapi==0.7.99.post21 requests
else
    echo "./clientCtr does not exist on your filesystem."
    sudo cp controlAdapter/udev/* /etc/udev/rules.d
    python3 -m venv clientCtr
    sleep 10
    . clientCtr/bin/activate 
    sleep 10
    pip uninstall hidapi==0.7.99.post21 requests
fi
python3 controlAdapter/src/comandMap.py &