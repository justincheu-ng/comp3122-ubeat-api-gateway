import flask

flask_app = flask.Flask(__name__)


if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', debug=True, port=15000)