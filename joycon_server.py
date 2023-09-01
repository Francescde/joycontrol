import json
from os.path import isfile, join

from joycontrol.command_line_interface import ControllerCLI
from joycontrol.protocol import controller_protocol_factory
from joycontrol.server import create_hid_server
from joycontrol.controller import Controller
from joycontrol.memory import FlashMemory
from run_controller_cli import _register_commands_with_controller_state
from aioflask import Flask, jsonify, render_template, request, redirect, send_file
from amiibo_cloner.amiibo_cloner import AmiiboCloner
from joycontrol.nfc_tag import NFCTag
import asyncio
import os
import subprocess
import sys
import zipfile
from timeit import default_timer as timer
import shutil

def copy_files_to_parent_folder(subfolder_path, extension):
    # Get the absolute paths of the parent and subfolder
    parent_folder = os.path.dirname(subfolder_path)
    subfolder_files = os.listdir(subfolder_path)

    for file_name in subfolder_files:
        if file_name.endswith(extension):
            subfolder_file_path = os.path.join(subfolder_path, file_name)
            parent_file_path = os.path.join(parent_folder, file_name)

            if not os.path.exists(parent_file_path):
                shutil.copy2(subfolder_file_path, parent_folder)
                print(f"File '{file_name}' copied to parent folder.")

# Example usage:
extension = ".txt"
copy_files_to_parent_folder("controllers/controllersDefauld", '.json')
copy_files_to_parent_folder("rjctScripts/rjctScriptsDefauld", '.txt')
copy_files_to_parent_folder("controllerMaps/defauld", '.json')

objectMap = {}
objectMap['cli'] = None
objectMap['transport'] = None
objectMap['active'] = False
objectMap['scriptRunning'] = None
objectMap['repeats'] = 0
amiibo_generator = None
unfixed_info_path = os.path.join('amiibo_cloner', 'unfixed-info.bin')
locked_secret_path = os.path.join('amiibo_cloner', 'locked-secret.bin')

if os.path.exists(unfixed_info_path) and os.path.exists(locked_secret_path):
    amiibo_generator = AmiiboCloner(unfixed_info_path, locked_secret_path)

comandTimer = []
lastTime = 0
timerFlag = False
def build_defauld_controller_map():
    mapControllerKeys = ["a", "b", "x", "y", "up", "down", "left", "right", "minus", "plus", "capture", "home", "l", "zl", "r", "zr", "l_stick", "r_stick"]
    dictionary = {}
    for key in mapControllerKeys:
        dictionary[key] = {"type": "button", "value": key}
    dictionary['stick']={
        'l': {
            "center": True,
            "centerRadius": 1000,
            "v": 0,
            "h": 0,
            "precision": 5000
        },
        'r': {
            "center": True,
            "centerRadius": 1000,
            "v": 0,
            "h": 0,
            "precision": 5000
        }
    }
    dictionary['autoconnect']={
        'enable': False,
        'timeout': 10
    }
    return dictionary


maxComandLines = 10000
comandDelay = -0.0085
readInterval = 10
amiiboFolder = 'amiibos'
mapControllerFile = None
mapControllerValues = build_defauld_controller_map()

CONFIG_FILE = "properties.conf.json"

def read_config():
    global maxComandLines, comandDelay, readInterval, amiiboFolder, mapControllerValues, mapControllerFile
    try:
        with open(CONFIG_FILE, "r") as file:
            config = json.load(file)
            maxComandLines = config['maxComandLines']
            comandDelay = config['comandDelay']
            readInterval = config['readInterval']
            amiiboFolder = config['amiiboFolder']
            mapControllerFile = config['mapControllerFile']
            mapControllerValues = config['mapControllerValues']
    except:
        print('file no found')

def write_config():
    global maxComandLines, comandDelay, readInterval, amiiboFolder, mapControllerValues, mapControllerFile
    with open(CONFIG_FILE, "w") as file:
        config = {
            'maxComandLines': maxComandLines,
            'comandDelay': comandDelay,
            'readInterval': readInterval,
            'amiiboFolder': amiiboFolder,
            'mapControllerFile': mapControllerFile,
            'mapControllerValues': mapControllerValues
        }
        json.dump(config, file, indent=4)


read_config()

write_config()



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
        awaitable_tasks = []
        for execution_object in execution_objects:
            await asyncio.gather(*awaitable_tasks)
            [asyncio.create_task(objectMap['cli'].run_line(subline)) for subline in execution_object['non_sleep_line']]
            awaitable_tasks = [asyncio.create_task(objectMap['cli'].run_line(subline)) for subline in execution_object['sleep_line']]
        
        await asyncio.gather(*awaitable_tasks)
        
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
    write_config()
    comandTimer = []
    lastTime = 0
    timerFlag = False
    return jsonify({'message': "succes"})


@app.route('/disconnect')
async def disconnect():
    await close_transport()
    return jsonify({'message': 'Closed'})


@app.route('/check_update')
def check_update():
    with app.app_context():
        # Get the absolute path of the current script file
        script_path = os.path.abspath(__file__)

        # Get the directory containing the script file (project directory)
        project_dir = os.path.dirname(script_path)

        try:
            # Fetch the latest changes from the remote repository
            subprocess.check_call(['git', 'fetch'], cwd=project_dir)

            # Get the last local commit hash
            local_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=project_dir).decode().strip()

            # Get the last remote commit hash associated with the current local branch
            remote_commit = subprocess.check_output(['git', 'rev-parse', '@{u}'], cwd=project_dir).decode().strip()

            if local_commit != remote_commit:
                return jsonify({'status': 'Update available', 'value': True})
            else:
                return jsonify({'status': 'Up to date', 'value': False})
        except:
            return jsonify({'status': 'Could not check', 'value': False})



@app.route('/view/<controllerName>')
async def display_view(controllerName):
    updatable = check_update().json['value']
    return await render_template(controllerName+'.html', amiiboFolder=amiiboFolder, script=script,  maxComandLines=maxComandLines, comandDelay=comandDelay, mapControllerFile=mapControllerFile, updatable=updatable, unfixed_exists = os.path.exists(unfixed_info_path), secret_exists = os.path.exists(locked_secret_path))


@app.route('/')
def redirect_to_home():
    return redirect('/view/home')


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


@app.route('/download', methods=['POST'])
def download():
    try:
        content = request.get_json()
        file_path = os.path.abspath(content['path'])
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        print(e)
        return str(e), 500


@app.route('/delete_amiibo', methods=['POST'])
def delete_amiibo():
    try:
        content = request.get_json()
        file_path = os.path.abspath(content['path'])
        os.remove(file_path)
        return jsonify({
            'filePath': file_path
        })
    except Exception as e:
        print(e)
        return str(e), 500

@app.route('/zip_folder', methods=['POST'])
def zip_folder():
    try:
        # Get the folder path from the request
        folder_path = request.json.get('folder_path')

        # Check if the folder exists
        if not os.path.exists(folder_path):
            return jsonify({'error': 'Folder does not exist'}), 404

        # Specify a fixed name for the ZIP file
        zip_file_path = 'export.zip'

        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    print('file '+file)
                    file_path = os.path.join(root, file)
                    # Add the file to the zip archive
                    zipf.write(file_path, os.path.relpath(file_path, folder_path))

        # Return the zip file as a response
        return send_file(zip_file_path, as_attachment=True)

    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/files', methods=['POST'])
def get_files():
    global amiibo_generator
    content = request.get_json()
    print('content')
    print(content)
    folderpath = content['path']
    if(folderpath and os.path.exists(folderpath)):
        resultList = [join(folderpath, f) for f in os.listdir(folderpath) if isfile(join(folderpath, f)) and f.endswith('.bin')]
        if amiibo_generator!=None:
            for amiibo_file in resultList:
                amiibo_generator.exclude_value_from(amiibo_file)
        return jsonify(resultList)
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

#os.system('sudo reboot')
@app.route('/system', methods=['POST'])
def system_functions():
    content = request.get_json()
    action = content['action']
    if 'reboot' in action:
        os.system('sudo reboot now')
    if 'shutdown' in action:
        os.system('sudo shutdown now')
    return jsonify({
        'response': 'goodby'
    })

@app.route('/delete_script/<controllerName>')
def delete_script(controllerName):
    path = os.path.join('rjctScripts', controllerName+'.txt')  
    os.remove(path)
    return jsonify({
        'controllerName': controllerName
    })


@app.route('/controller_map')
def get_controller_map():
    return jsonify(mapControllerValues)


@app.route('/controller_maps', methods=['GET'])
def get_controller_maps():
    folderpath = 'controllerMaps'
    return jsonify(
        [f for f in os.listdir(folderpath) if isfile(join(folderpath, f)) and ('.json' in f)])


@app.route('/controller_maps/get')
def get_controller_map_defaulf():
    global mapControllerValues, mapControllerFile
    # Opening JSON file
    data = build_defauld_controller_map()
    mapControllerValues = data
    mapControllerFile = None
    write_config()
    return jsonify({
        'controllerName': None,
        'jsonFile': data,
    })


@app.route('/controller_maps/get/<controllerName>')
def get_controller_map_by_name(controllerName):
    global mapControllerValues, mapControllerFile
    # Opening JSON file
    f = open('controllerMaps/'+controllerName)
    data = json.load(f)
    mapControllerValues = data
    mapControllerFile = controllerName
    write_config()
    return jsonify({
        'controllerName': controllerName,
        'jsonFile': data,
    })


@app.route('/delete_controller_map/<controllerName>')
def delete_controller_map(controllerName):
    global mapControllerValues, mapControllerFile
    path = os.path.join('controllerMaps', controllerName)  
    os.remove(path)
    # Opening JSON file
    data = build_defauld_controller_map()
    mapControllerValues = data
    mapControllerFile = None
    write_config()
    return jsonify({
        'controllerName': mapControllerFile
    })


@app.route('/controller_map_file')
def get_current_controller_map_file():
    global mapControllerFile
    # Opening JSON file
    return jsonify({
        'fileName': mapControllerFile
    })


@app.route('/controllers_maps_post', methods=['POST'])
def add_controllers_maps():
    global mapControllerValues, mapControllerFile
    content = request.get_json()
    print('content')
    print(content)
    folderpath = 'controllerMaps'
    file = content['json']
    filename = content['filename']
    mapControllerValues = file
    mapControllerFile = filename
    # Directly from dictionary
    with open(join(folderpath, filename), 'w') as outfile:
        json.dump(file, outfile)
    write_config()
    return jsonify({
        'controllerName': filename,
        'jsonFile': file,
    })


#"/writeScript/<filename>"
@app.route('/uploadcnf/<type>', methods=['POST'])
def upload_cong(type):
    global unfixed_info_path, locked_secret_path, amiibo_generator
    file = request.files['file']
    if file.filename.endswith('.bin'):
        if 'unfixed' in type:
            print('processing .bin file'+file.filename)
            file.save(unfixed_info_path)
            response = {'message': 'unfixed loaded'}
        if 'locked' in type:
            print('processing .bin file'+file.filename)
            file.save(locked_secret_path)
            response = {'message': 'locked loaded'}
        if os.path.exists(unfixed_info_path) and os.path.exists(locked_secret_path):
            amiibo_generator = AmiiboCloner(unfixed_info_path, locked_secret_path)
    else:
        response = {'message': 'Tipo de archivo no valido'}
    
    return jsonify(response)

@app.route('/upload', methods=['POST'])
def upload():
    global amiibo_generator
    print('arriba')
    file = request.files['file']
    if file.filename.endswith('.bin'):
        print('processing .bin file'+file.filename)
        file.save(os.path.join(amiiboFolder, file.filename))
        amiibo_generator.exclude_value_from(os.path.join(amiiboFolder, file.filename))
        response = {'message': 'Archivo .bin recibido'}
    elif file.filename.endswith('.zip'):
        print('processing .zip file'+file.filename)
        with zipfile.ZipFile(file, 'r') as zip_ref:
            for member in zip_ref.namelist():
                print('processing .zip file'+member)
                if member.endswith('.bin') and not os.path.basename(member).startswith('.'):
                    extracted_file_path = os.path.join(amiiboFolder, os.path.basename(member))
                    with open(extracted_file_path, 'wb') as extracted_file:
                        extracted_file.write(zip_ref.read(member))
                        amiibo_generator.exclude_value_from(extracted_file_path)
        response = {'message': 'Archivos ZIP recibidos y los archivos BIN descomprimidos fueron guardados'}
    else:
        response = {'message': 'Tipo de archivo no valido'}
    
    return jsonify(response)


@app.route('/amiiboclone', methods=['POST'])
async def amiibo_clone():
    global amiibo_generator
    content = request.get_json()
    origin_filePath = content['filePath']
    clone_filePath = 'tmp.bin'
    if('clonePath' in content):
        clone_filePath = content['clonePath']
    response = {'message': 'clonning '+origin_filePath + ' into '+clone_filePath}
    if amiibo_generator!=None:
        amiibo_generator.generate_amiibo_clone(origin_filePath, clone_filePath)
        await execute_line('nfc '+clone_filePath)
    else:
        response = {'message': 'Tipo de archivo no valido'}
    return jsonify(response)

@app.route('/update')
def update():
    update_completed = False
    with app.app_context():
        # Get the absolute path of the current script file
        script_path = os.path.abspath(__file__)

        # Get the directory containing the script file (project directory)
        project_dir = os.path.dirname(script_path)

        try:
            # Stash any local changes
            subprocess.check_call(['git', 'stash'], cwd=project_dir)

            # Pull the latest changes from Git
            subprocess.check_call(['git', 'pull'], cwd=project_dir)

            try:
                # Pop the stashed changes
                subprocess.check_call(['git', 'stash', 'pop'], cwd=project_dir)
            except subprocess.CalledProcessError:
                # Handle the case where no stash is available to pop
                pass

            # Execute the dependency installation script
            install_script_path = os.path.join(project_dir, 'install_update_dependencies.sh')
            subprocess.check_call(['bash', install_script_path], cwd=project_dir)

            # Restart the Raspberry Pi
            update_completed = True;
            subprocess.check_call(['sudo', 'reboot', 'now'])
            return redirect('/view/home')
        except subprocess.CalledProcessError:
            if not update_completed:
                return 'Update failed. An error occurred during the update process.'
            else: 
                return redirect('/view/home')


if __name__ == '__main__':
    for arg in sys.argv:
        if '-folder=' in arg:
            amiiboFolder = str(arg).split('-folder=')[-1]
            write_config()
    app.run(host='0.0.0.0', port=80)
