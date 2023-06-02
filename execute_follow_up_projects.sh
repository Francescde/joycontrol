if [[ -d ./clientCtr ]]
then
    echo "./clientCtr exists on your filesystem."
    source clientCtr/bin/activate 
else
    echo "./clientCtr does not exist on your filesystem."
    sudo cp controlAdapter/udev/* /etc/udev/rules.d
    python3 -m venv clientCtr
    source clientCtr/bin/activate
    pip install hidapi==0.7.99.post21 requests
fi
python3 controlAdapter/src/comandMap.py &