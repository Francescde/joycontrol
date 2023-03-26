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


async def load_amiibos(script, nfc):
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
    try:

        f = open(script, 'r+')
        lines = []
        try:
            lines = f.readlines()
        except Exception as e:
            print("An exception occurred" + str(e))
        f.close()

        async def sleep(*args):
            time = float(args[0])-0.025
            await asyncio.sleep(time)
        cli.add_command(sleep.__name__, sleep)


        await controller_state.connect()

        for i in range(len(lines)):
            line = lines[i]
            if '{nfc}' in line:
                line = line.replace('{nfc}', nfc)
            lineTask = []
            if ';' in line:
                for subline in line.split(';'):
                    lineTask.append(asyncio.create_task(cli.run_line(subline)))
                await asyncio.gather(* lineTask)
            else:
                await cli.run_line(line)
            
    finally:
        await transport.close()


if __name__ == '__main__':
    # check if root
    print(sys.argv)
    nfc = None
    script = None
    for arg in sys.argv:
        if '-nfc=' in arg:
            nfc = str(arg).replace('-nfc=', '')
        if '-script=' in arg:
            script = str(arg).replace('-script=', '')
    if script:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(load_amiibos(script, nfc))
