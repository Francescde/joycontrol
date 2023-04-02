import json
from os.path import isfile, join

from joycontrol.command_line_interface import ControllerCLI
from joycontrol.protocol import controller_protocol_factory
from joycontrol.server import create_hid_server
from joycontrol.controller import Controller
from joycontrol.memory import FlashMemory
from run_controller_cli import _register_commands_with_controller_state
from aioflask import Flask, send_from_directory, jsonify, render_template, request
from joycontrol.nfc_tag import NFCTag
import asyncio
import os
import sys
from timeit import default_timer as timer

objectMap = {}
objectMap['cli'] = None
objectMap['transport'] = None
objectMap['active'] = False
objectMap['scriptRunning'] = None
comandTimer = []
lastTime = 0
timerFlag = False

amiiboFolder = None
script = None

async def get_client_transport():
    global objectMap;
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
    button_list = controller_state.button_state.get_available_buttons()
    for but in button_list:
        print(but)
    cli = ControllerCLI(controller_state)
    _register_commands_with_controller_state(controller_state, cli)
    # wait for input to be accepted

    await controller_state.connect()
    objectMap['cli'] = cli
    objectMap['transport'] = transport
    objectMap['active'] = True
    timerFlag = False
    lastTime = 0
    return cli, transport


async def close_transport():
    global objectMap;
    if (objectMap['active']):
        await objectMap['transport'].close()
    objectMap['cli'] = None
    objectMap['transport'] = None
    objectMap['active'] = False


async def client_sent_line(line):
    global objectMap;
    if (objectMap['active']):
        await objectMap['cli'].run_line(line)


async def runScriptAsync(script, nfc):
    global objectMap
    f = open(script, 'r+')
    lines = []
    try:
        lines = f.readlines()
    except Exception as e:
        print("An exception occurred" + str(e))
    f.close()
    tasks = []
    for line in lines:
        if '{nfc}' in line:
            line = line.replace('{nfc}', nfc)
        lineTask = []
        if ';' in line:
            for subline in line.split(';'):
                lineTask.append(subline)
        else:
            lineTask = [line]
        tasks.append(lineTask)
        for line in tasks:
            lineTask = []
            for subline in line:
                lineTask.append(asyncio.create_task(objectMap['cli'].run_line(subline)))
            await asyncio.gather(* lineTask)


app = Flask(__name__, static_folder='static')


@app.route('/connect')
async def connect():
    await get_client_transport()
    return jsonify({'message': 'Created'})


@app.route('/connected')
async def connected():
    global objectMap;
    return jsonify({'connected': objectMap['active']})


@app.route('/execute_script', methods=['POST'])
def executeScript():
    global objectMap;
    content = request.get_json()
    script = content['script']
    nfc = content['nfc']
    objectMap['scriptRunning'] = asyncio.create_task(runScriptAsync(script, nfc))
    return jsonify({'message': 'Send'})


@app.route('/script_running', methods=['GET'])
def executeScript():
    global objectMap;
    scriptRunnig = False;
    if(objectMap['scriptRunning']):
        scriptRunnig = not objectMap['scriptRunning'].done()
    return jsonify({'message': scriptRunnig})


@app.route('/kill_script', methods=['GET'])
def executeScript():
    global objectMap;
    if(objectMap['scriptRunning'] and not objectMap['scriptRunning'].done()):
        objectMap['scriptRunning'].cancel()
    return jsonify({'message': 'cancel'})


@app.route("/comand", methods=['POST'])
async def comand():
    global timerFlag, lastTime, comandTimer
    content = request.get_json()
    line = content['line']
    timePass=0
    if timerFlag:
        timePass = timer() - lastTime
    timerFlag = True
    await client_sent_line(line)
    lastTime = timer()
    comandTimer.append({
        "comand": line,
        "time": timePass
    })
    if(len(comandTimer)>100):
        comandTimer.pop(0)
        comandTimer[0]['time']=0
    return jsonify({'message': 'Send'})


@app.route("/analog", methods=['POST'])
async def analog():
    global timerFlag, lastTime, comandTimer
    content = request.get_json()
    timePass=0
    if timerFlag:
        timePass = timer() - lastTime
    timerFlag = True
    await asyncio.gather(*[client_sent_line("stick "+content['key']+" v "+str(content['vertical'])), client_sent_line("stick "+content['key']+" h "+str(content['horizontal']))])
    lastTime = timer()
    comandTimer.append({
        "comand": "stick "+content['key']+" v "+str(content['vertical'])+"; "+ "stick "+content['key']+" h "+str(content['horizontal']),
        "time": timePass
    })
    if(len(comandTimer)>100):
        comandTimer.pop(0)
        comandTimer[0]['time']=0
    return jsonify({'message': 'Send'})


@app.route("/writeScript/<filename>", methods=['GET'])
async def writeScript(filename):
    global comandTimer
    '''
    comandTimer.append({
        "comand": "stick "+content['key']+" v "+str(content['vertical'])+"; "+ "stick "+content['key']+" h "+str(content['horizontal']),
        "time": timePass
    })'''
    lines = []
    for comand in comandTimer:
        if comand["time"]>0:
            lines.append("sleep "+str(comand["time"]))
        lines.append(comand["comand"])
    with open(filename+".txt", "w") as file:
        # write to file
        file.write('\n'.join(lines))
    return jsonify({'message': "\""+'\n'.join(lines)+"\""})


@app.route('/disconnect')
async def disconnect():
    await close_transport()
    return jsonify({'message': 'Closed'})


@app.route('/view/<controllerName>')
async def send_report(controllerName):
    return await render_template(controllerName+'.html', amiiboFolder=amiiboFolder, script=script )


@app.route('/controller/<controllerName>')
async def send_report(controllerName):
    # Opening JSON file
    f = open('controllers/'+controllerName+'.json')
    data = json.load(f)
    return await render_template('defauld_controller.html', params=json.dumps(data))


@app.route('/files', methods=['POST'])
def get_files():
    content = request.get_json()
    print('content')
    print(content)
    folderpath = content['path']
    if(folderpath and os.path.exists(folderpath)):
        return jsonify(
            [join(folderpath, f) for f in os.listdir(folderpath) if isfile(join(folderpath, f)) and ('.bin' in f)])
    return jsonify([])

@app.route('/controllers', methods=['GET'])
def get_controllers():
    folderpath = 'controllers'
    return jsonify(
        [f for f in os.listdir(folderpath) if isfile(join(folderpath, f)) and ('.json' in f)])


@app.route('/controllers/<controllerName>')
def get_controller(controllerName):
    # Opening JSON file
    f = open('controllers/'+controllerName+'.json')
    data = json.load(f)
    return jsonify({
        'controllerName': controllerName,
        'jsonFile': data,
    })


@app.route('/controllers', methods=['POST'])
def add_controllers():
    content = request.get_json()
    print('content')
    print(content)
    folderpath = 'controllers'
    file = content['json']
    filename = content['filename']
    # Directly from dictionary
    with open(join(folderpath, filename), 'w') as outfile:
        json.dump(file, outfile)
    return jsonify({'message': 'Created'})


@app.route('/scripts', methods=['GET'])
def get_scripts():
    folderpath = 'rjctScripts'
    return jsonify(
        [f for f in os.listdir(folderpath) if isfile(join(folderpath, f)) and ('.txt' in f)])


@app.route('/scripts/<controllerName>')
def get_script(controllerName):
    # Opening JSON file
    f = open('rjctScripts/'+controllerName+'.txt')
    data = f.read()
    return jsonify({
        'controllerName': controllerName,
        'jsonFile': data,
    })


@app.route('/scripts', methods=['POST'])
def add_scripts():
    content = request.get_json()
    print('content')
    print(content)
    folderpath = 'rjctScripts'
    file = content['data']
    filename = content['filename']
    # Directly from dictionary
    with open(join(folderpath, filename), 'w') as outfile:
        outfile.write(file)
    return jsonify({'message': 'Created'})


if __name__ == '__main__':
    for arg in sys.argv:
        if '-folder=' in arg:
            amiiboFolder = str(arg).replace('-folder=', '')
        if '-script=' in arg:
            script = str(arg).replace('-script=', '')
    app.run(host='0.0.0.0', port=8082)
