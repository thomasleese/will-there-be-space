from flask import Flask

app = Flask(__name__)


@app.route('/')
def hello():
    return 'Will there be a space?'


@app.route('/in/<place_name>')
def place(place_name):
    return 'I doubt it.'