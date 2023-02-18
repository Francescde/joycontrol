from joycontrol.command_line_interface import ControllerCLI
from joycontrol.protocol import controller_protocol_factory
from joycontrol.server import create_hid_server
from joycontrol.controller import Controller
from joycontrol.memory import FlashMemory
from run_controller_cli import _register_commands_with_controller_state
from joycontrol.nfc_tag import NFCTag
import asyncio
import os
import sys

# the type of controller to create
controller = Controller.PRO_CONTROLLER  # or JOYCON_L or JOYCON_R
spi_flash = FlashMemory()
# a callback to create the corresponding protocol once a connection is established
factory = controller_protocol_factory(controller, spi_flash=spi_flash)
ctl_psm, itr_psm = 17, 19
objectMap = {}
objectMap['cli']=None
objectMap['transport']=None
objectMap['active']= True

async def get_client_transport():
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
    objectMap['cli']=cli
    objectMap['transport']=transport
    objectMap['active']= True
    return cli, transport


async def close_transport():
    if(objectMap['active']):
        await objectMap['transport'].close()
    objectMap['cli'] = None
    objectMap['transport'] = None
    objectMap['active'] = True


async def client_sent_line(line):
    if(objectMap['active']):
        await objectMap['cli'].run_line(line)


from flask import Flask
from flask import send_from_directory

app = Flask(__name__)

@app.route('/connect')
async def index():
    await get_client_transport()
    return {'message': 'Created'}

@app.route('/connected')
async def index():
    return {'connected': objectMap['active']}

@app.route("/comand/<comand")
async def data(line):
    await client_sent_line(line)
    return {'message': 'Send'}

@app.route('/disconnect')
async def index():
    await close_transport()
    return {'message': 'Closed'}

@app.route('/controller')
def send_report():
    return send_from_directory('controller.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082)
