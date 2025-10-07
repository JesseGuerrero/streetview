import os
from flask import Flask, send_from_directory, request, Response, jsonify
from flask_sock import Sock
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()
GOOGLE_3D_TILES = os.environ.get("GOOGLE_3D_TILES")
GOOGLE_STREET_VIEW = os.environ.get("GOOGLE_STREET_VIEW")
HOST = "localhost"

app = Flask(__name__, static_folder='public', static_url_path='')
sock = Sock(app)
CORS(app)

@app.route('/')
def index():
    global HOST, UTSA_USERNAME, UTSA_PASSWORD, GOOGLE_3D_TILES, GOOGLE_STREET_VIEW
    with open(os.path.join(app.static_folder, 'index.html'), 'r') as file:
        content = file.read().replace('{{ host }}', HOST).replace('{{ google 3d tiles }}', GOOGLE_3D_TILES).replace('{{ google street view }}', GOOGLE_STREET_VIEW)
    return Response(content, mimetype='text/html')

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=3035, debug=False)