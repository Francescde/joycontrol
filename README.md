# joycontrol

Branch: master->amiibo_edits

Emulate Nintendo Switch Controllers over Bluetooth.

Tested on Raspberry Zero w, Raspberry 4B Raspbian, should work on 3B+ too and anything that can do the setup.

Chack out https://www.youtube.com/channel/UCE3sSyM4Ng1SrWQdWBFw-nA where we will explain the project in detail

## Features
#### Emulation of JOYCON_R, JOYCON_L and PRO_CONTROLLER. Able to send:
- button commands
- stick state
- nfc for amiibo read & owner registration

#### Tactile controller served over flask
- view/home allows to create controller configs, navegate to the controller result, create scripts(executable on the controllers), and view and load amiboos stored on the raspberry
- controller/{controllerConfigFileName}: shows the controller configurated on /view/home

## Installation
- Install dependencies  
  Raspbian:
```bash
sudo apt install python3-dbus libhidapi-hidraw0 libbluetooth-dev bluez python3-pip python3-venv
sudo python3 -m venv server
source server/bin/activate
```
  Python: (a setup.py is present but not yet up to date)  
  Note that pip here _has_ to be run as root, as otherwise the packages are not available to the root user.
```bash
sudo pip3 install aioconsole hid crc8 aioflask Flask flask[async] Flask-SocketIO eventlet
```
 If you are unsure if the packages are properly installed, try running `sudo python3` and import each using `import package_name`.

- setup bluetooth
  - [I shouldn't have to say this, but] make sure you have a working Bluetooth adapter\
  If you are running inside a VM, the PC might but not the VM. Check for a controller using `bluetoothctl show` or `bluetoothctl list`. Also a good indicator it the actual os reporting to not have bluetooth anymore.
  - disable SDP [only necessary when pairing]\
  change the `ExecStart` parameter in `/lib/systemd/system/bluetooth.service` to `ExecStart=/usr/lib/bluetooth/bluetoothd -C -P sap,input,avrcp`.\
  This is to remove the additional reported features as the switch only looks for a controller.\
  This also breaks all other Bluetooth gadgets, as this also disabled the needed drivers.
  - disable input plugin [experimental alternative to above when not pairing]\
  When not pairing, you can get away with only disabling the `input` plugin, only breaking bluetooth-input devices on your PC. Do so by changing `ExecStart` to `ExecStart=/usr/lib/bluetooth/bluetoothd -C -P input` instead.
  - Restart bluetooth-deamon to apply the changes:
  ```bash
    sudo systemctl daemon-reload
    sudo systemctl restart bluetooth.service
  ```
  - see [Issue #4](https://github.com/Poohl/joycontrol/issues/4) if despite that the switch doesn't connect or disconnects randomly.

```bash
pip install websockets hidapi==0.7.99.post21
```

## joycon_server.py
Serves web controllers ussing flask that allow you to send comands 

- joycon_server: serves a webside with configurable controllers
```bash
sudo python3 joycon_server.py --folder=<amiiboFolderPath>
```

the main view /view/home has three parts

#### Controller

Allows the user to edit and create, configurate and navigate to controllers.

The controller config uses three arrays substitute, add, and remove these three arrays interact with the defauld array, adding new items to display, or removing or deleting the object that matches the text attribute

It also allow to set a background Image(backgroundImage), set some images and resize them(images), the color to draw the items(drawColor), the background Color(backgroundColor), the items Fill Color(itemsFillColor) and the analog Limits Color(analogLimitsColor)

You can also change the frequency with the comands are send (readInterval), and the max time a call can take (readInterval), use this two parameters if you find performance issues.

example of controller
```json
{
   "add": [
      {
         "actionType": 5,
         "borderColor": "#FF0000",
         "center": {
            "h": 85,
            "w": 84
         },
         "fillColor": "#000000",
         "radius": 21.90625,
         "repeats": -1,
         "script": "snow 2",
         "selectedColor": "#FFFFFF",
         "text": "script",
         "textFont": "32px Brush Script MT",
         "writeColor": "#00FF00"
      }
   ],
   "analogLimitsColor": "#4CDA64",
   "backgroundColor": "#DDE4EC",
   "drawColor": "#007AFF",
   "filename": "someScript2",
   "images": [
      {
         "height": 102.4,
         "name": "raspberry",
         "pos": {
            "h": 47,
            "w": 281
         },
         "url": "/static/raspberry.png",
         "width": 68.2
      },
      {
         "height": 76.4,
         "name": "joy con left",
         "pos": {
            "h": 83,
            "w": 173
         },
         "url": "/static/joy-con-left.png",
         "width": 102.4
      },
      {
         "height": 76.4,
         "name": "joy con right",
         "pos": {
            "h": 71,
            "w": 490
         },
         "url": "/static/joy-con-right.png",
         "width": 76.4
      },
      {
         "height": 40,
         "name": "trol",
         "pos": {
            "h": 189,
            "w": 308
         },
         "url": "/static/trol.png",
         "width": 33
      }
   ],
   "itemsFillColor": "#E3EDE5",
   "readInterval": 10,
   "remove": [
      "HLZ",
      "LZ",
      "HL",
      "L",
      "R",
      "HR",
      "RZ",
      "HRZ",
      "JL",
      "JLP",
      "X",
      "B",
      "Y",
      "A",
      "↑",
      "↓",
      "←",
      "→",
      "JR",
      "JRP",
      "-",
      "+",
      "H"
   ],
   "substitute": [
      {
         "actionType": 4,
         "center": {
            "h": 67,
            "w": 301
         },
         "link": "/view/home",
         "radius": 18.4375,
         "selectedColor": "#FF0000",
         "text": "#"
      }
   ],
   "texts": [
      {
         "font": "32px Brush Script MT",
         "pos": {
            "h": 44,
            "w": 297
         },
         "text": "Raspi"
      },
      {
         "pos": {
            "h": 81,
            "w": 223
         },
         "text": "Joy"
      },
      {
         "pos": {
            "h": 79,
            "w": 361
         },
         "text": "Con"
      },
      {
         "pos": {
            "h": 108,
            "w": 289
         },
         "text": "Trol"
      }
   ]
}
```
example of a defauld array on an iphone mini
```json
[{center: {w: 59.333333333333336, h: 24.333333333333332}, radius: 24.333333333333332, text: "HLZ", actionType: 2, action: "ZL"},
{center: {w: 118.66666666666667, h: 24.333333333333332}, radius: 24.333333333333332, text: "LZ", actionType: 0, action: "ZL"},
{center: {w: 178, h: 24.333333333333332}, radius: 24.333333333333332, text: "HL", actionType: 2, action: "L"},
{center: {w: 237.33333333333334, h: 24.333333333333332}, radius: 24.333333333333332, text: "L", actionType: 0},
{center: {w: 474.66666666666663, h: 24.333333333333332}, radius: 24.333333333333332, text: "R", actionType: 0},
{center: {w: 534, h: 24.333333333333332}, radius: 24.333333333333332, text: "HR", actionType: 2, action: "R"},
{center: {w: 593.3333333333334, h: 24.333333333333332}, radius: 24.333333333333332, text: "RZ", actionType: 0, action: "ZR"},
{center: {w: 652.6666666666666, h: 24.333333333333332}, radius: 24.333333333333332, text: "HRZ", actionType: 2, action: "ZR"},
{center: {w: 101.71428571428571, h: 146}, radius: 60.833333333333336, text: "JL", actionType: 1, analog: "L", reverseW: false, reverseH: true},
{center: {w: 101.71428571428571, h: 247.11111111111111}, radius: 20.27777777777778, text: "JLP", actionType: 0, action: "l_stick"},
{center: {w: 623, h: 79.08333333333333}, radius: 20.27777777777778, text: "X", actionType: 0},
{center: {w: 623, h: 190.61111111111111}, radius: 20.27777777777778, text: "B", actionType: 0},
{center: {w: 574.3333333333334, h: 136.53703703703704}, radius: 20.27777777777778, text: "Y", actionType: 0},
{center: {w: 671.6666666666666, h: 136.53703703703704}, radius: 20.27777777777778, text: "A", actionType: 0},
{center: {w: 237.33333333333334, h: 190.6111111111111}, radius: 20.27777777777778, text: "↑", actionType: 0, action: "Up"},
{center: {w: 237.33333333333334, h: 261.5833333333333}, radius: 20.27777777777778, text: "↓", actionType: 0, action: "Down"},
{center: {w: 196.77777777777777, h: 223.5625}, radius: 20.27777777777778, text: "←", actionType: 0, action: "Left"},
{center: {w: 277.8888888888889, h: 223.5625}, radius: 20.27777777777778, text: "→", actionType: 0, action: "Right"},
{center: {w: 474.6666666666667, h: 231.16666666666666}, radius: 48.66666666666667, text: "JR", actionType: 1, analog: "R", reverseW: false, reverseH: true},
{center: {w: 563.6111111111112, h: 231.16666666666666}, radius: 20.27777777777778, text: "JRP", actionType: 0, action: "r_stick"},
{center: {w: 284.8, h: 118.1904761904762}, radius: 20.27777777777778, text: "-", actionType: 0, action: "minus"},
{center: {w: 427.2, h: 118.1904761904762}, radius: 20.27777777777778, text: "+", actionType: 0, action: "plus"},
{center: {w: 356, h: 89.22222222222223}, radius: 20.27777777777778, text: "H", actionType: 0, action: "home"},
{center: {w: 356, h: 24.333333333333332}, radius: 12.166666666666666, text: "#", actionType: 4, selectedColor: "#FF0000"}]
```
Each element of the atribute defines the position of the button and the action it will perform. The action it will perfrom is defined by actionType:
- holder: actionType value 2. On press it holds the button to release you have to press the button again. Required field action
```json
{
  "center": {
    "w": 59.333333333333336,
    "h": 24.333333333333332
  },
  "radius": 24.333333333333332,
  "text": "HLZ",
  "actionType": 2,
  "action": "ZL"
}
```
- analog: actionType value 1. It sends an action for one of the joystics. Required field analog. Optional fields reverseW, reverseH, scalePrecisionSquare
```json
{
  "center": {
    "w": 474.6666666666667,
    "h": 231.16666666666666
  },
  "radius": 48.66666666666667,
  "text": "JR",
  "actionType": 1,
  "analog": "R",
  "reverseW": false,
  "reverseH": true
}
```
- defauld: actionType value 0. On press it holds the button to release you have to unpress the button like any button. Required field action
```json
{
  "center":{
    "w": 563.6111111111112,
    "h": 231.16666666666666
  },
  "radius": 20.27777777777778,
  "text": "JRP",
  "actionType": 0,
  "action": "r_stick"
}
```
- connecter: actionType value 3. On press it will try to connect the raspberry to the nintendo swich if it fails restart the script.
```json
{
  "center": {
    "w": 356,
    "h": 24.333333333333332
  },
  "radius": 12.166666666666666,
  "text": "#",
  "actionType": 4,
  "selectedColor": "#FF0000"
}
```
- link: actionType value 4. On press it will change the view to another one. Can be ussed to link controllers or to navigate to home for example. Required field link
```json
  {
      "center": {
          "w": 91.90625,
          "h": 46.09375
      },
      "text": "#",
      "actionType": 4,
      "link": "/view/home"
  }
```
script: actionType value 5. On press it execute an script repeats times(-1 forever). To stop it you can press the button again. Required field script. Optional field repeats
```json
 {
      "center": {
          "w": 21.90625,
          "h": 112.09375
      },
      "radius": 21.90625,
      "text": "script",
      "actionType": 5,
      "script": "try",
      "repeats": -1
  }
```

## load amiibos ussing an script

As it will require a diferent script for each game. The idea is to simplify the writing of the scripts and its execution. 

To archive that this versions has two new scripts to load amiibos.

- load_amiibos: load an amiibo
```bash
sudo python3 load_amiibos.py -nfc=<amiiboPath>
```

- load_all_amiibos: load all amiibos from a folder (the idea is to not keep the connection alive as the picking of the amiibo at least on botw is not automatizable)
```bash
sudo python3 load_all_amiibos.py -folder=<folderPath> -script=<scriptPath>
```

Next is an example of a script to load amiibos on zelda botw.

The only new comand in this version is sleep, it is ussed to not send to much comands at once or to wait before releasing a button or changing directions.

The other thing to have in mind is to write {nfc} on the place the amiibo path should go. The script will replace it for the path

Enjoy
```bash
sleep 1
a
sleep 1
b
sleep 0.5
hold up
sleep 0.5
stick r right
sleep 3
stick r center
sleep 0.5
release up
sleep 0.5
l
sleep 0.5
nfc {nfc}
sleep 3
b
sleep 0.5
```


## Command line interface example
There is a simple CLI (`sudo python3 run_controller_cli.py`) provided with this app. Startup-options are:
```
usage: run_controller_cli.py [-h] [-l LOG] [-d DEVICE_ID]
                             [--spi_flash SPI_FLASH] [-r RECONNECT_BT_ADDR]
                             [--nfc NFC]
                             controller

positional arguments:
  controller            JOYCON_R, JOYCON_L or PRO_CONTROLLER

optional arguments:
  -h, --help            show this help message and exit
  -l LOG, --log LOG     BT-communication logfile output
  -d DEVICE_ID, --device_id DEVICE_ID
                        not fully working yet, the BT-adapter to use
  --spi_flash SPI_FLASH
                        controller SPI-memory dump to use
  -r RECONNECT_BT_ADDR, --reconnect_bt_addr RECONNECT_BT_ADDR
                        The Switch console Bluetooth address (or "auto" for
                        automatic detection), for reconnecting as an already
                        paired controller.
  --nfc NFC             amiibo dump placed on the controller. Equivalent to
                        the nfc command.

```

To use the script:
- start it (this is a minimal example)
```bash
sudo python3 run_controller_cli.py PRO_CONTROLLER
```
- The cli does sanity checks on startup, you might get promps telling you they failed. Check the command-line options and your setup in this case. (Note: not the logging messages). You can however still try to proceed, sometimes it works despite the warnings.

- Afterwards a PRO_CONTROLLER instance waiting for the Switch to connect is created.

- If you didn't pass the `-r` option, Open the "Change Grip/Order" menu of the Switch and wait for it to pair.

- If you already connected the emulated controller once, you can use the reconnect option of the script (`-r <Switch Bluetooth Mac address>`). Don't open the "Change Grip/Order" menu in this case, just make sure the switch is turned on. You can find out a paired mac address using the `bluetoothctl paired-devices` system command or pass `-r auto` as address for automatic detection.

- After connecting, a command line interface is opened.  
  Note: Press \<enter> if you don't see a prompt.

  Call "help" to see a list of available commands.

## API

See the `run_controller_cli.py` for an example how to use the API. A minimal example:

```python
from joycontrol.protocol import controller_protocol_factory
from joycontrol.server import create_hid_server
from joycontrol.controller import Controller

# the type of controller to create
controller = Controller.PRO_CONTROLLER # or JOYCON_L or JOYCON_R
# a callback to create the corresponding protocol once a connection is established
factory = controller_protocol_factory(controller)
# start the emulated controller
transport, protocol = await create_hid_server(factory)
# get a reference to the state beeing emulated.
controller_state = protocol.get_controller_state()
# wait for input to be accepted
await controller_state.connect()
# some sample input
controller_state.button_state.set_button('a', True)
# wait for it to be sent at least once
await controller_state.send()
```

## Issues
- Some bluetooth adapters seem to cause disconnects for reasons unknown, try to use an usb adapter or a raspi instead.
- Incompatibility with Bluetooth "input" plugin requires it to be disabled (along with the others), see [Issue #8](https://github.com/mart1nro/joycontrol/issues/8)
- The reconnect doesn't ever connect, `bluetoothctl` shows the connection constantly turning on and off. This means the switch tries initial pairing, you have to unpair the switch and try without the `-r` option again.
- ...

## Thanks
- Special thanks to https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering for reverse engineering of the joycon protocol
- Thanks to the growing number of contributers and users

## Resources

[Nintendo_Switch_Reverse_Engineering](https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering)

[console_pairing_session](https://github.com/timmeh87/switchnotes/blob/master/console_pairing_session)

[Hardware Issues thread](https://github.com/Poohl/joycontrol/issues/4)
