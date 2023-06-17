from aioconsole import ainput
import asyncio
import os
import sys


async def load_script_for_amiibo_of_array(arrayPosition, amiiboArray, amiiboFolder, script):
    filename = amiiboArray[arrayPosition]
    file = os.path.join(amiiboFolder, filename)
    os.system('sudo python3 load_amiibos.py -nfc=' + file + ' -script=' + script)

async def load_amiibos(script, amiiboFolder):
    # wait for input to be accepted
    actual = 0
    listD = [filename for filename in os.listdir(amiiboFolder) if '.bin' in filename]
    while actual < len(listD) + 1:
        message = ""
        if (actual < len(listD)):
            message = listD[actual] + " loading write n to skip amiibo or anyting else to load (" + str(
                actual + 1) + "/" + str(len(listD)) + ")\n"
        if actual > 0:
            message += listD[actual - 1] + " previus amiibo press r to reload\n"
        instruction = await ainput(prompt=message)
        if instruction == 'r' and actual > 0:
            actual = actual - 1
        if instruction != "n" and actual < len(listD):
            await load_script_for_amiibo_of_array(actual, listD, amiiboFolder, script)
        actual += 1


if __name__ == '__main__':
    # check if root
    print(sys.argv)
    amiiboFolder = None
    script = None
    for arg in sys.argv:
        if '-folder=' in arg:
            amiiboFolder = str(arg).replace('-folder=', '')
        if '-script=' in arg:
            script = str(arg).replace('-script=', '')
    if script and amiiboFolder:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(load_amiibos(script, amiiboFolder))
    else:
        print("amiboo folder or script missing")
