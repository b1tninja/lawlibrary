import os
from multiprocessing import Process

from flask import Flask, request, jsonify

data_dir = os.getenv('MOUNT_DIRECTORY', 'data')

application = Flask(__name__)


@application.route("/")
def index():
    return "Hello World"


# @application.before_first_request
@application.route("/setup")
def setup():
    from ca import download_pubinfos
    Process(target=download_pubinfos, args=(data_dir,)).start()
    return "Downloading..."


@application.route("/headers")
def headers():
    return dict(request.headers)


@application.route("/ls")
def ls():
    return jsonify(os.listdir(data_dir))


@application.route("/env")
def env():
    return dict(os.environ)


if __name__ == "__main__":
    application.debug = True
    application.run()
