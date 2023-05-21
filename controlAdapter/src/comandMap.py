#!/usr/bin/env python3

import sys

import procon
import socketio
import json

def panic(msg):
    print(msg)
    sys.exit(1)

def are_close_values(val, com, err):
    return val+err>com and val-err<com


def main(sio):
    uinput_buttons_map = {
        procon.ProCon.Button.A: "a",
        procon.ProCon.Button.B: "b",
        procon.ProCon.Button.X: "x",
        procon.ProCon.Button.Y: "y",
        procon.ProCon.Button.UP: "up",
        procon.ProCon.Button.DOWN: "down",
        procon.ProCon.Button.LEFT: "left",
        procon.ProCon.Button.RIGHT: "right",
        procon.ProCon.Button.MINUS: "minus",
        procon.ProCon.Button.PLUS: "plus",
        procon.ProCon.Button.SCREENSHOT: "capture",
        procon.ProCon.Button.HOME: "home",
        procon.ProCon.Button.L: "l",
        procon.ProCon.Button.ZL: "zl",
        procon.ProCon.Button.R: "r",
        procon.ProCon.Button.ZR: "zr",
        procon.ProCon.Button.LS: "l_stick",
        procon.ProCon.Button.RS: "r_stick"
    }
    buttons_prev = {}
    l_stick_values = {
        "v": 0,
        "h": 0,
        "precision": 1000
    }
    r_stick_values = {
        "v": 0,
        "h": 0,
        "precision": 1000
    }

    def send_to_controller(buttons, l_stick, r_stick, _, __, ___):
        nonlocal buttons_prev, l_stick_values, r_stick_values, sio
        if not buttons_prev:
            buttons_prev = buttons
            return
        for k, v in buttons.items():
            if buttons_prev[k] != v:
                uinput_button = uinput_buttons_map[k]
                if not uinput_button:
                    continue
                if v:
                    #emit event on webdocket
                    #print('hold '+uinput_button)
                    message = {'type': 'comand', 'comand': 'hold '+uinput_button}
                    sio.emit('message', json.dumps(message))
                else:
                    #emit event on websocket
                    #print('release '+uinput_button)
                    message = {'type': 'comand', 'comand': 'release '+uinput_button}
                    sio.emit('message', json.dumps(message))
        buttons_prev = buttons
        analog_max_abs_value = 32767
        if((not are_close_values(l_stick_values['v'], l_stick[0], l_stick_values['precision'])) or (not are_close_values(l_stick_values['h'], -l_stick[1], l_stick_values['precision']))):
            print('l_stick ' + str(l_stick[0]) +", "+ str(-l_stick[1]))
            l_stick_values['v']=l_stick[0]
            l_stick_values['h']=-l_stick[1]
            #emit event on websocket
        if((not are_close_values(r_stick_values['v'], r_stick[0], r_stick_values['precision'])) or (not are_close_values(r_stick_values['h'], -r_stick[1], r_stick_values['precision']))):
            print('r_stick ' + str(r_stick[0]) +", "+ str(-r_stick[1]))
            r_stick_values['v']=r_stick[0]
            r_stick_values['h']=-r_stick[1]
            #emit event on websocket
    print('Initializing Nintendo Switch Pro Controller... ', end='', flush=True)
    try:
        con = procon.ProCon()
    except OSError as e:
        panic('Unable to open the controller. Make sure you have plugged in the controller and have sufficient permission to open it (either as root or with udev rules): {}'.format(e))
    print('done\nEnjoy!')
    try:
        con.start(send_to_controller)
    except KeyboardInterrupt:
        print('\rGoodbye!')
    except OSError:
        panic('IO failed. Did you just unplugged the controller?')


# Create a SocketIO client instance
sio = socketio.Client()

# SocketIO event handlers
@sio.on('connect')
def on_connect():
    message = {'type': 'testConnection'}
    # Send a message to the server
    sio.emit('message', json.dumps(message))
    print('Connected to server')
    main(sio)

@sio.on('message')
def on_message(data):
    print('Received message:', data)

@sio.on('disconnect')
def on_disconnect():
    print('Disconnected from server')

# Connect to the server
sio.connect('http://0.0.0.0:8082')

# Wait for messages and handle events
sio.wait()


