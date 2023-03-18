import json
from os.path import isfile, join

from flask import Flask, send_from_directory, jsonify, render_template, request
import asyncio
import os
import sys

objectMap = {}
objectMap['cli'] = None
objectMap['transport'] = None
objectMap['active'] = False

amiiboFolder = None
script = None

app = Flask(__name__, static_folder='static')


@app.route('/connect')
def connect():
    return {'message': 'Created'}


@app.route('/connected')
def connected():
    return {'connected': False}


@app.route("/comand", methods=['POST'])
def comand():
    content = request.get_json()
    line = content['line']
    return {'message': 'Send'}


@app.route('/disconnect')
def disconnect():
    return {'message': 'Closed'}


@app.route('/controller/<controllerName>')
def send_report(controllerName):
    return render_template(controllerName+'.html', amiiboFolder=amiiboFolder, script=script )


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
