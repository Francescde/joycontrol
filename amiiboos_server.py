import json
from os.path import isfile, join

from flask import request

from joycontrol.command_line_interface import ControllerCLI
from joycontrol.protocol import controller_protocol_factory
from joycontrol.server import create_hid_server
from joycontrol.controller import Controller
from joycontrol.memory import FlashMemory
from run_controller_cli import _register_commands_with_controller_state
from aioflask import Flask, send_from_directory, jsonify, render_template
from joycontrol.nfc_tag import NFCTag
import asyncio
import os
import sys

objectMap = {}
objectMap['cli'] = None
objectMap['transport'] = None
objectMap['active'] = False

amiiboFolder = None
script = None


async def get_client_transport():
    # the type of controller to create
    controller = Controller.PRO_CONTROLLER  # or JOYCON_L or JOYCON_R
    spi_flash = FlashMemory()
    # a callback to create the corresponding protocol once a connection is established
    factory = controller_protocol_factory(controller, spi_flash=spi_flash)
    ctl_psm, itr_psm = 17, 19
    # start the emulated controller
    transport, protocol = await create_hid_server(factory,
                                                  ctl_psm=ctl_psm,
                                                  itr_psm=itr_psm,
                                                  interactive=True, auto_unpair=True)
    # get a reference to the state beeing emulated.
    controller_state = protocol.get_controller_state()
    cli = ControllerCLI(controller_state)
    _register_commands_with_controller_state(controller_state, cli)
    # wait for input to be accepted

    await controller_state.connect()
    objectMap['cli'] = cli
    objectMap['transport'] = transport
    objectMap['active'] = True
    return cli, transport


async def close_transport():
    if (objectMap['active']):
        await objectMap['transport'].close()
    objectMap['cli'] = None
    objectMap['transport'] = None
    objectMap['active'] = False


async def client_sent_line(line):
    if (objectMap['active']):
        await objectMap['cli'].run_line(line)


app = Flask(__name__, static_folder='static')


@app.route('/connect')
async def connect():
    await get_client_transport()
    return {'message': 'Created'}


@app.route('/connected')
async def connected():
    return {'connected': objectMap['active']}


@app.route("/comand", methods=['POST'])
async def comand():
    content = request.get_json()
    line = content['line']
    await client_sent_line(line)
    return {'message': 'Send'}


@app.route('/disconnect')
async def disconnect():
    await close_transport()
    return {'message': 'Closed'}


@app.route('/controller')
async def send_report():
    return await render_template('controller.html', amiiboFolder=amiiboFolder, script=script )


@app.route('/files', methods=['POST'])
def get_files():
    content = request.get_json()
    print('content')
    print(content)
    folderpath = content['path']
    return jsonify(
        [join(folderpath, f) for f in os.listdir(folderpath) if isfile(join(folderpath, f)) and ('.bin' in f)])


if __name__ == '__main__':
    for arg in sys.argv:
        if '-folder=' in arg:
            amiiboFolder = str(arg).replace('-folder=', '')
        if '-script=' in arg:
            script = str(arg).replace('-script=', '')
    app.run(host='0.0.0.0', port=8082)
