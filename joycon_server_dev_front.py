import json
from os.path import isfile, join

from flask import Flask, send_from_directory, jsonify, render_template, request
import asyncio
import os
import sys
import zipfile

objectMap = {}
objectMap['cli'] = None
objectMap['transport'] = None
objectMap['active'] = False

amiiboFolder = 'amiibos'
script = None

app = Flask(__name__, static_folder='static')


@app.route('/connect')
def connect():
    return jsonify({'message': 'Created'})


@app.route('/connected')
def connected():
    return jsonify({'connected': False})


@app.route("/comand", methods=['POST'])
def comand():
    content = request.get_json()
    line = content['line']
    return jsonify({'message': 'Send'})


@app.route('/disconnect')
def disconnect():
    return jsonify({'message': 'Closed'})



@app.route('/view/<controllerName>')
def load_view(controllerName):
    return render_template(controllerName+'.html', amiiboFolder=amiiboFolder, script=script )


@app.route('/controller/<controllerName>')
def load_controller(controllerName):
    # Opening JSON file
    f = open('controllers/'+controllerName+'.json')
    data = json.load(f)
    return render_template('defauld_controller.html', params=json.dumps(data))



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


@app.route('/upload', methods=['POST'])
def upload():
    print('arriba')
    file = request.files['file']
    if file.filename.endswith('.bin'):
        print('processing .bin file'+file.filename)
        file.save(os.path.join(amiiboFolder, file.filename))
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
        response = {'message': 'Archivos ZIP recibidos y los archivos BIN descomprimidos fueron guardados'}
    else:
        response = {'message': 'Tipo de archivo no valido'}
    
    return jsonify(response)


if __name__ == '__main__':
    for arg in sys.argv:
        if '-folder=' in arg:
            amiiboFolder = str(arg).replace('-folder=', '')
        if '-script=' in arg:
            script = str(arg).replace('-script=', '')
    app.run(host='0.0.0.0', port=8082)
