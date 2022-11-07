from joycontrol.command_line_interface import ControllerCLI
from joycontrol.protocol import controller_protocol_factory
from joycontrol.server import create_hid_server
from joycontrol.controller import Controller
from joycontrol.memory import FlashMemory
from joycontrol.nfc_tag import NFCTag
import asyncio
import os
import sys


async def load_amiibos(script, nfc):
    # the type of controller to create
    controller = Controller.PRO_CONTROLLER  # or JOYCON_L or JOYCON_R
    spi_flash = FlashMemory()
    # a callback to create the corresponding protocol once a connection is established
    factory = controller_protocol_factory(controller, spi_flash=spi_flash, auto_unpair=True)
    ctl_psm, itr_psm = 17, 19
    # start the emulated controller
    transport, protocol = await create_hid_server(factory,
                                                  ctl_psm=ctl_psm,
                                                  itr_psm=itr_psm,
                                                  interactive=True)
    # get a reference to the state beeing emulated.
    controller_state = protocol.get_controller_state()
    # wait for input to be accepted
    try:
        await controller_state.connect()

        controller_state.button_state.set_button('a', True)
        await controller_state.send()
        await asyncio.sleep(1)
        controller_state.button_state.set_button('a', False)
        await controller_state.send()

        controller_state.button_state.set_button('b', True)
        await controller_state.send()
        await asyncio.sleep(1)
        controller_state.button_state.set_button('b', False)
        await controller_state.send()
        await asyncio.sleep(0.5)

        controller_state.button_state.set_button('up', True)
        await controller_state.send()
        await asyncio.sleep(0.5)
        stick = controller_state.r_stick_state
        ControllerCLI._set_stick(stick, "right", None)
        await controller_state.send()
        await asyncio.sleep(3)
        ControllerCLI._set_stick(stick, "center", None)
        await controller_state.send()
        await asyncio.sleep(0.5)
        controller_state.button_state.set_button('up', False)
        await controller_state.send()
        await asyncio.sleep(0.5)

        controller_state.button_state.set_button('l', True)
        await controller_state.send()
        await asyncio.sleep(1)
        controller_state.button_state.set_button('l', False)
        await controller_state.send()
        await asyncio.sleep(0.5)

        controller_state.set_nfc(NFCTag.load_amiibo(nfc))
        await controller_state.send()
        await asyncio.sleep(3)

        controller_state.button_state.set_button('b', True)
        await controller_state.send()
        await asyncio.sleep(1)
        controller_state.button_state.set_button('b', False)
        await controller_state.send()

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

    if script and nfc:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(load_amiibos(script, nfc))
