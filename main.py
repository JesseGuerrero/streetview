import os
from flask import Flask, send_from_directory, request, Response, jsonify
from flask_sock import Sock
from flask_cors import CORS
from dotenv import load_dotenv
import math
from vllm import inferenceAddress, street_images, addresses, captions_dir, images_dir, processAddress, getCaption, repopulate_street_images

load_dotenv()
GOOGLE_3D_TILES = os.environ.get("GOOGLE_3D_TILES")
GOOGLE_STREET_VIEW = os.environ.get("GOOGLE_STREET_VIEW")
HOST = "localhost"

app = Flask(__name__, static_folder='public', static_url_path='')
sock = Sock(app)
CORS(app)


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in feet between two lat/lon points"""
    R = 20902231  # Earth's radius in feet

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def normalize_heading(heading):
    """Normalize heading to 0-360 range"""
    return heading % 360


def heading_difference(h1, h2):
    """Calculate smallest difference between two headings"""
    h1 = normalize_heading(h1)
    h2 = normalize_heading(h2)
    diff = abs(h1 - h2)
    if diff > 180:
        diff = 360 - diff
    return diff


@app.route('/')
def index():
    global HOST, UTSA_USERNAME, UTSA_PASSWORD, GOOGLE_3D_TILES, GOOGLE_STREET_VIEW
    with open(os.path.join(app.static_folder, 'index.html'), 'r') as file:
        content = file.read().replace('{{ host }}', HOST).replace('{{ google 3d tiles }}', GOOGLE_3D_TILES).replace(
            '{{ google street view }}', GOOGLE_STREET_VIEW)
    return Response(content, mimetype='text/html')


@app.route('/list-street-views', methods=['GET'])
def list_street_views():
    """Return list of saved street view images with their coordinates"""
    images_dir = 'street_images'
    saved_images = []

    if os.path.exists(images_dir):
        for filename in os.listdir(images_dir):
            if filename.endswith('.jpg'):
                # Parse filename: longitude-latitude-heading.jpg
                parts = filename.replace('.jpg', '').split('_')
                if len(parts) == 3:
                    try:
                        saved_images.append({
                            'filename': filename,
                            'longitude': float(parts[0]),
                            'latitude': float(parts[1]),
                            'heading': float(parts[2])
                        })
                    except ValueError:
                        continue

    return jsonify({'images': saved_images})

import base64
@app.route('/check-nearby-image', methods=['POST'])
def check_nearby_image():
    """Check if there's a cached image within 10 feet and 15 degrees heading"""
    data = request.json
    target_address = str(data['address'])
    target_lon = float(data.get('longitude'))
    target_lat = float(data.get('latitude'))
    target_heading = float(data.get('heading'))

    images_dir = 'street_images'
    if not os.path.exists(images_dir):
        return jsonify({'cached': False})
    for filename in os.listdir(images_dir):
        if filename.endswith('.jpg') and filename.startswith(target_address):
            parts = filename.replace('.jpg', '').split('_')
            if len(parts) == 4:
                try:
                    saved_address = str(parts[0])
                    saved_lon = float(parts[1])
                    saved_lat = float(parts[2])
                    saved_heading = float(parts[3])
                    caption = getCaption(saved_address)

                    # Check distance (within 10 feet)
                    distance = haversine_distance(target_lat, target_lon, saved_lat, saved_lon)

                    # Check heading difference (within 15 degrees)
                    heading_diff = heading_difference(target_heading, saved_heading)
                    if distance <= 15 and heading_diff <= 15:
                        image_path = f'./street_images/{filename}'
                        img_base64 = None
                        with open(image_path, 'rb') as img_file:
                            img_data = img_file.read()
                            img_base64 = base64.b64encode(img_data).decode('utf-8').replace('\n', '')
                        count = 0
                        if saved_address in street_images:
                            count = len(street_images[saved_address])
                        return jsonify({
                            'cached': True,
                            'filename': filename,
                            'distance': distance,
                            'heading_difference': heading_diff,
                            'caption': caption,
                            'image': img_base64,
                            'count': count
                        })
                except ValueError as e:
                    print(e)
                    continue

    return jsonify({'cached': False})


@app.route('/process-all-images', methods=['POST'])
def process_all_images():
    try:
        repopulate_street_images()
        for street_address in addresses:
            processAddress(street_address)
        return jsonify({'success': True})
    except Exception as e:
        print(e)
        return jsonify({'success': False})
@app.route('/process-address', methods=['POST'])
def process_street_address():
    try:
        repopulate_street_images()
        data = request.json
        processAddress(data['address'])
        return jsonify({'success': True})
    except Exception as e:
        print(e)
        return jsonify({'success': False})
@app.route('/save-street-view', methods=['POST'])
def save_street_view():
    data = request.json
    address = data['address']
    longitude = data.get('longitude')
    latitude = data.get('latitude')
    heading = data.get('heading')
    image_data = data.get('image')

    filename = f"{address}_{longitude}_{latitude}_{heading}.jpg"
    filepath = os.path.join('street_images', filename)

    # Decode base64 image and save
    import base64
    image_bytes = base64.b64decode(image_data.split(',')[1])

    with open(filepath, 'wb') as f:
        f.write(image_bytes)

    return jsonify({'success': True, 'filename': filename})


if __name__ == "__main__":
    repopulate_street_images()
    app.run(host='127.0.0.1', port=3035, debug=True)