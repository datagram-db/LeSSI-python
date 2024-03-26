import time

import flask
from flask import Flask, render_template, request
from flask_cors import CORS, cross_origin
import yaml

import main

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app, resources={r"/*": {"origins": "*"}})


@app.route('/')
def index():
    return 'hello'


@app.route('/sentences', methods=['POST'], strict_slashes=False)
# @cross_origin()
def update_sentences():
    sentences = request.json['sentences']
    config = request.json['config']

    with open('config.yaml') as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)
        for cKey, cValue in config.items():
            cfg[cKey] = cValue
            print(f"Updated {cKey} to {cValue}")

    main.start_pipeline(sentences, cfg)

    return 'Finished pipeline'


@app.route('/log', methods=['GET'])
def get_log():
    return ''


if __name__ == '__main__':
    app.run()
