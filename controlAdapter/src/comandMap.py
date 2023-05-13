#!/usr/bin/env python3

import sys

import procon

def panic(msg):
    print(msg)
    sys.exit(1)

def main():
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
        procon.ProCon.Button.SCREENSHOT: None,
        procon.ProCon.Button.HOME: "home",
        procon.ProCon.Button.L: "l",
        procon.ProCon.Button.ZL: "zl",
        procon.ProCon.Button.R: "r",
        procon.ProCon.Button.ZR: "zr",
        procon.ProCon.Button.LS: "l_stick",
        procon.ProCon.Button.RS: "r_stick"
    }
    buttons_prev = {}
    def send_to_controller(buttons, l_stick, r_stick, _, __, ___):
        nonlocal buttons_prev
        if not buttons_prev:
            buttons_prev = buttons
            return
        for k, v in buttons.items():
            if buttons_prev[k] != v:
                uinput_button = uinput_buttons_map[k]
                if not uinput_button:
                    continue
                if v:
                    print('hold')
                else:
                    #uinput_dev.emit(uinput_button, 0)
                    print('release')
        buttons_prev = buttons
        print('l_stick')
        print(l_stick[0])
        print(-l_stick[1])
        print('r_stick')
        print(r_stick[0])
        print(-r_stick[1])
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
