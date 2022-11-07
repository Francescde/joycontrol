from aioconsole import ainput
import asyncio
import os


async def load_amiibos():
    # wait for input to be accepted
    directory = '/home/pi/joycontrol/Zelda'
    actual = 0
    listD = [filename for filename in os.listdir(directory) if '.bin' in filename]
    while actual < len(listD):
        message = listD[actual] + " loading write n to skip amiibo or anyting else to load (" + str(actual + 1) + "/" + str(
            len(listD)) + ")\n"
        if actual > 0:
            message += listD[actual-1] + " previus amiibo press r to reload\n"

        instruction = await ainput(prompt=message)
        if instruction == 'r' and actual > 0:
            actual = actual - 1
        if instruction != "n":
            filename = listD[actual]
            file = os.path.join(directory, filename)
            os.system('sudo python3 load_amiibos.py PRO_CONTROLLER --nfc ' + file)
        actual += 1


loop = asyncio.get_event_loop()
loop.run_until_complete(load_amiibos())
