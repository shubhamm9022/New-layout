from flask import Flask, request, jsonify
import requests, json, base64, os

app = Flask(__name__)

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO = os.getenv('REPO')
FILE_PATH = 'movies.json'
BRANCH = 'main'
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

@app.route('/update', methods=['POST'])
def update_movies():
    new_data = request.json
    url = f'https://api.github.com/repos/{REPO}/contents/{FILE_PATH}?ref={BRANCH}'

    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        return jsonify({'error': 'Failed to get file'}), 400

    file_data = res.json()
    movies = json.loads(base64.b64decode(file_data['content']).decode('utf-8'))
    movies.append(new_data)

    encoded = base64.b64encode(json.dumps(movies, indent=2).encode('utf-8')).decode('utf-8')
    update_payload = {
        "message": "Updated movies.json via admin panel",
        "content": encoded,
        "sha": file_data['sha'],
        "branch": BRANCH
    }

    push = requests.put(url, headers=HEADERS, json=update_payload)
    if push.status_code == 200:
        return jsonify({'message': 'Success'})
    return jsonify({'error': 'Failed to update'}), 400

@app.route('/')
def home():
    return 'Movie Updater API is Running'
