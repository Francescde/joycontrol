#!/usr/bin/env python3

import sys

import procon
import requests
import math
import time

def panic(msg):
    print(msg)
    sys.exit(1)

def are_close_values(val, com, err):
    return val+err>com and val-err<com

def rule_of_three(val):
    maxAnalog = 4096
    analog_max_abs_value = 32767
    return math.floor(((val + analog_max_abs_value)/(analog_max_abs_value*2))*maxAnalog)

def calculate_distance(x1, y1, x2, y2):
    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return distance

def main():
    map = requests.get('http://localhost:8082/controller_map')
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
    l_stick_values = map['stick']['l']
    r_stick_values = map['stick']['r']
    buttons_prev = {}
    def send_to_controller(buttons, l_stick, r_stick, _, __, ___):
        nonlocal buttons_prev, l_stick_values, r_stick_values, map
        if not buttons_prev:
            buttons_prev = buttons
            return
        comands_to_send = []
        for k, v in buttons.items():
            if buttons_prev[k] != v:
                uinput_button = map[uinput_buttons_map[k]]
                if not uinput_button:
                    continue
                if v:
                    #emit event on webdocket
                    #print('hold '+uinput_button)
                    if 'button' in uinput_button['type']:
                        comands_to_send.append('hold '+uinput_button['value'])
                    elif 'script' in uinput_button['type']:
                        requests.post('http://localhost:8082/execute_script', json = {'script': "rjctScripts/"+uinput_button['value']+".txt", 'nfc':"", 'repeats': 1})
                    #response = requests.post('http://localhost:8082/comand', json = {'line':'hold '+uinput_button})
                    #print(response)
                else:
                    #emit event on websocket
                    #print('release '+uinput_button)
                    if 'button' in uinput_button['type']:
                        comands_to_send.append('release '+uinput_button['value'])
                    #response = requests.post('http://localhost:8082/comand', json = {'line':'release '+uinput_button})
                    #print(response)
        buttons_prev = buttons
        if( calculate_distance(0, 0, l_stick[1], l_stick[0]) < l_stick_values['centerRadius']):
            if not l_stick_values['center']:
                comands_to_send.append('stick l center')
                #response = requests.post('http://localhost:8082/comand', json = {'line':'stick l center'})
                l_stick_values['h']= 0
                l_stick_values['v']= 0
                l_stick_values['center'] = True
        elif((not are_close_values(l_stick_values['v'], l_stick[1], l_stick_values['precision'])) or (not are_close_values(l_stick_values['h'], l_stick[0], l_stick_values['precision']))):
            #print('l_stick ' + str(l_stick[0]) +", "+ str(-l_stick[1]))
            l_stick_values['h']=l_stick[0]
            l_stick_values['v']=l_stick[1]
            l_stick_values['center'] = False
            line = "stick l v "+str(rule_of_three(l_stick_values['v']))+" && "+"stick l h "+str(rule_of_three(l_stick_values['h']))
            comands_to_send.append(line)
            #response = requests.post('http://localhost:8082/analog', json = { 'key': 'l','vertical': rule_of_three(l_stick_values['v']),'horizontal': rule_of_three(l_stick_values['h'])})
            #print(response)
            #emit event on websocket
        if( calculate_distance(0, 0, r_stick[1], r_stick[0]) < r_stick_values['centerRadius']):
            if not r_stick_values['center']:
                comands_to_send.append('stick r center')
                #response = requests.post('http://localhost:8082/comand', json = {'line':'stick r center'})
                r_stick_values['h']= 0
                r_stick_values['v']= 0
                r_stick_values['center'] = True
        elif((not are_close_values(r_stick_values['v'], r_stick[1], r_stick_values['precision'])) or (not are_close_values(r_stick_values['h'], r_stick[0], r_stick_values['precision']))):
            #print('r_stick ' + str(r_stick[0]) +", "+ str(-r_stick[1]))
            r_stick_values['center'] = False
            r_stick_values['h']=r_stick[0]
            r_stick_values['v']=r_stick[1]
            line = "stick r v "+str(rule_of_three(r_stick_values['v']))+" && "+"stick r h "+str(rule_of_three(r_stick_values['h']))
            comands_to_send.append(line)
            #response = requests.post('http://localhost:8082/analog', json = { 'key': 'r', 'vertical': rule_of_three(r_stick_values['v']), 'horizontal': rule_of_three(r_stick_values['h'])})
            #print(response)
            #emit event on websocket
        if len(comands_to_send)>0:
            response = requests.post('http://localhost:8082/comand', json = {'line':" && ".join(comands_to_send)})

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

if __name__ == '__main__':
    main()
