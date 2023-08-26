#!/bin/sh
if [ -d "./server" ]
then
    echo "./server exists on your filesystem use this space to install server dependencies."
    . server/bin/activate
    sudo pip3 install pyamiibo
fi

if [ -d "./clientCtr" ]
then
    echo "./clientCtr exists on your filesystem use this space to install controller dependencies."
    . clientCtr/bin/activate
fi
