import json
from os.path import isfile, join

from joycontrol.command_line_interface import ControllerCLI
from joycontrol.protocol import controller_protocol_factory
from joycontrol.server import create_hid_server
from joycontrol.controller import Controller
from joycontrol.memory import FlashMemory
from run_controller_cli import _register_commands_with_controller_state
from aioflask import Flask, jsonify, render_template, request
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
objectMap['repeats'] = 0
comandTimer = []
lastTime = 0
timerFlag = False
maxComandLines = 10000
comandDelay = -0.0085
readInterval = 10

amiiboFolder = None
script = None

async def get_client_transport():
    global objectMap, timerFlag, lastTime;
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
    async def sleep(*args):
        await asyncio.sleep(float(args[0]))
    cli.add_command(sleep.__name__, sleep)
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
    tasks = []
    sleeps = []
    
    lines = []
    with open(script, 'r') as f:
        try:
            lines = f.readlines()
        except Exception as e:
            print("An exception occurred" + str(e))
    
    for line in lines:
        if '{nfc}' in line:
            line = line.replace('{nfc}', nfc)
        sleeps.append('sleep' in line)
        lineTask = line.split(';')
        tasks.append(lineTask)
    execution_objects = []
    non_sleep_line=[]
    for lineIndex, line in enumerate(tasks):
        if sleeps[lineIndex]:
            execution_objects.append({
                'non_sleep_line': non_sleep_line,
                'sleep_line': line
            })
            non_sleep_line = []
        else:
            non_sleep_line.extend(line)

    if len(non_sleep_line)>0:  # Handle any remaining non-sleep lines
        execution_objects.append({
            'non_sleep_lines': non_sleep_line,
            'sleep_lines': []
        })
    
    while objectMap['repeats'] != 0:
        for execution_object in execution_objects:
            [asyncio.create_task(objectMap['cli'].run_line(subline)) for subline in execution_object['non_sleep_line']]
            await asyncio.gather(*[asyncio.create_task(objectMap['cli'].run_line(subline)) for subline in execution_object['sleep_line']])
        
        if objectMap['repeats'] > 0:
            objectMap['repeats'] -= 1


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
    if(objectMap['scriptRunning'] and not objectMap['scriptRunning'].done()):
        objectMap['scriptRunning'].cancel()
    script = content['script']
    nfc = content['nfc']
    objectMap['repeats'] = int(content['repeats'])
    objectMap['scriptRunning'] = asyncio.create_task(runScriptAsync(script, nfc))
    return jsonify({'message': 'Send'})


@app.route('/script_running', methods=['GET'])
def scriptRuning():
    global objectMap;
    scriptRunnig = False;
    if(objectMap['scriptRunning']):
        scriptRunnig = not objectMap['scriptRunning'].done()
    return jsonify({'message': scriptRunnig})


@app.route('/kill_script', methods=['GET'])
def killScript():
    global objectMap;
    if(objectMap['scriptRunning'] and not objectMap['scriptRunning'].done()):
        objectMap['scriptRunning'].cancel()
    return jsonify({'message': 'cancel'})


async def execute_line(line):
    global timerFlag, lastTime, comandTimer, maxComandLines
    timePass=0
    if timerFlag:
        timePass = (timer() - lastTime)
    lineTask = [asyncio.create_task(client_sent_line(line))]
    lastTime = timer()
    timerFlag = True
    comandTimer.append({
        "comand": line,
        "time": timePass
    })
    if(len(comandTimer) > maxComandLines):
        comandTimer.pop(0)
        comandTimer[0]['time']=0
    await asyncio.gather(* lineTask)

@app.route("/comand", methods=['POST'])
async def comand():
    content = request.get_json()
    line = content['line']
    await execute_line(line)
    return jsonify({'message': 'Send'})


@app.route("/analog", methods=['POST'])
async def analog():
    content = request.get_json()
    line = "stick "+content['key']+" v "+str(content['vertical'])+" && "+"stick "+content['key']+" h "+str(content['horizontal'])
    await execute_line(line)
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


@app.route("/last-actions", methods=['GET'])
async def getRunningScript():
    global comandTimer, comandDelay
    '''
    comandTimer.append({
        "comand": "stick "+content['key']+" v "+str(content['vertical'])+"; "+ "stick "+content['key']+" h "+str(content['horizontal']),
        "time": timePass
    })'''
    lines = []
    for comand in comandTimer:
        if comand["time"] + (comandDelay)>0:
            lines.append("sleep "+str(comand["time"]+ (comandDelay)))
        lines.append(comand["comand"])
    return jsonify({'message': '\n'.join(lines)})


@app.route("/reset-actions", methods=['GET'])
async def resetActions():
    global comandTimer, lastTime, timerFlag
    comandTimer = []
    lastTime = 0
    timerFlag = False
    return jsonify({'message': "succes"})


@app.route("/reset-actions", methods=['POST'])
async def resetActionsAndSet():
    global comandTimer, lastTime, timerFlag, maxComandLines, comandDelay
    content = request.get_json()
    maxComandLines = int(content['maxComandLines'])
    comandDelay = float(content['comandDelay'])
    comandTimer = []
    lastTime = 0
    timerFlag = False
    return jsonify({'message': "succes"})


@app.route('/disconnect')
async def disconnect():
    await close_transport()
    return jsonify({'message': 'Closed'})


@app.route('/view/<controllerName>')
async def display_view(controllerName):
    return await render_template(controllerName+'.html', amiiboFolder=amiiboFolder, script=script,  maxComandLines=maxComandLines, comandDelay=comandDelay )


@app.route('/position_objects/<controllerName>')
async def set_controller_objects(controllerName):
    # Opening JSON file
    f = open('controllers/'+controllerName+'.json')
    data = json.load(f)
    if 'readInterval' not in data.keys():
        data['readInterval'] = readInterval
    data['filename'] = controllerName
    return await render_template('set_controller_positions.html', params=json.dumps(data))


@app.route('/controller/<controllerName>')
async def display_controller(controllerName):
    global readInterval
    # Opening JSON file
    f = open('controllers/'+controllerName+'.json')
    data = json.load(f)
    if 'readInterval' not in data.keys():
        data['readInterval'] = readInterval
    return await render_template('default_controller.html', params=json.dumps(data))


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


@app.route('/delete_controller/<controllerName>')
def delete_controller(controllerName):
    path = os.path.join('controllers', controllerName+'.json')  
    os.remove(path)
    return jsonify({
        'controllerName': controllerName
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


@app.route('/delete_script/<controllerName>')
def delete_script(controllerName):
    path = os.path.join('rjctScripts', controllerName+'.txt')  
    os.remove(path)
    return jsonify({
        'controllerName': controllerName
    })


if __name__ == '__main__':
    for arg in sys.argv:
        if '-folder=' in arg:
            amiiboFolder = str(arg).split('-folder=')[-1]
    app.run(host='0.0.0.0', port=8082)
