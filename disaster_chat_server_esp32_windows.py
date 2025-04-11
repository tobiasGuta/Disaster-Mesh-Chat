from flask import Flask, render_template_string, request, send_from_directory
from flask_socketio import SocketIO, send, emit
from datetime import datetime
import os
import random
import json
from werkzeug.utils import secure_filename
import serial  # Add for ESP32 integration (Bluetooth/Serial)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

connected_clients = 0
MESSAGE_LOG = 'chat_log.txt'
usernames_by_ip = {}
locations_by_ip = {}

# Optional: Initialize serial communication with ESP32 for mesh fallback
try:
    esp_serial = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
except Exception as e:
    esp_serial = None
    print("ESP32 not connected or not found:", e)

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Emergency Mesh Chat</title>
    <style>
        body {
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: 'Courier New', Courier, monospace;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            height: 100vh;
        }
        header {
            padding: 1rem;
            background-color: #161b22;
            border-bottom: 1px solid #30363d;
            text-align: center;
        }
        header h1 {
            margin: 0;
            font-size: 1.5rem;
        }
        #status {
            padding: 0.5rem;
            background-color: #161b22;
            text-align: center;
            border-bottom: 1px solid #30363d;
        }
        #messages {
            flex: 1;
            padding: 1rem;
            overflow-y: auto;
            background-color: #0d1117;
        }
        #inputArea {
            display: flex;
            flex-direction: column;
            padding: 1rem;
            background-color: #161b22;
            border-top: 1px solid #30363d;
        }
        .row {
            display: flex;
            margin-top: 0.5rem;
        }
        input[type="text"] {
            flex: 1;
            padding: 0.5rem;
            background-color: #0d1117;
            color: #c9d1d9;
            border: 1px solid #30363d;
            border-radius: 5px;
            margin-right: 0.5rem;
        }
        input[type="file"] {
            margin-right: 0.5rem;
        }
        button {
            padding: 0.5rem 1rem;
            background-color: #238636;
            color: #fff;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background-color: #2ea043;
        }
    </style>
</head>
<body>
    <header>
        <h1>🛡️ Disaster NYC Plan</h1>
    </header>
    <div id="status">Connected Users: <span id="userCount">0</span></div>
    <div id="messages"></div>
    <div id="inputArea">
        <div class="row">
            <input id="myMessage" autocomplete="off" placeholder="Type your message..." type="text" />
            <button onclick="sendMessage()">Send</button>
        </div>
        <div class="row">
            <input type="file" id="imageUpload" />
            <button onclick="uploadImage()">Upload Image</button>
        </div>
    </div>

    <script src="/static/js/socket.io.min.js"></script>
    <script>
        var socket = io('http://IP:5000', {
            transports: ['polling'],
            withCredentials: true
        });
        var messages = document.getElementById('messages');
        var userCount = document.getElementById('userCount');

        socket.on('message', function(msg) {
            var item = document.createElement('div');
            if (msg.includes('<img')) {
                item.innerHTML = msg;
            } else {
                item.textContent = msg;
            }
            messages.appendChild(item);
            messages.scrollTop = messages.scrollHeight;
        });

        socket.on('user_count', function(count) {
            userCount.textContent = count;
        });

        socket.on('chat_history', function(history) {
            history.forEach(function(msg) {
                var item = document.createElement('div');
                if (msg.includes('<img')) {
                    item.innerHTML = msg;
                } else {
                    item.textContent = msg;
                }
                messages.appendChild(item);
            });
            messages.scrollTop = messages.scrollHeight;
        });

        function sendMessage() {
            var input = document.getElementById("myMessage");
            var msg = input.value.trim();
            if (msg !== '') {
                navigator.geolocation.getCurrentPosition(function(position) {
                    const data = {
                        text: msg,
                        location: {
                            lat: position.coords.latitude,
                            lon: position.coords.longitude
                        }
                    };
                    socket.send(JSON.stringify(data));
                }, function() {
                    socket.send(JSON.stringify({ text: msg }));
                });
                input.value = '';
            }
        }

        function uploadImage() {
            var fileInput = document.getElementById('imageUpload');
            var file = fileInput.files[0];
            if (!file) return;

            var formData = new FormData();
            formData.append('image', file);

            fetch('/upload', {
                method: 'POST',
                body: formData
            }).then(res => res.json()).then(data => {
                if (data.success) {
                    socket.send(`<img src="${data.url}" style="max-width: 200px;" />`);
                }
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['image']
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return {"success": True, "url": f"/uploads/{filename}"}
    return {"success": False}, 400

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/static/js/socket.io.min.js')
def server_static_js():
    return send_from_directory('static/js/', 'socket.io.min.js')

@socketio.on('connect')
def handle_connect():
    global connected_clients
    connected_clients += 1
    emit('user_count', connected_clients, broadcast=True)

    user_ip = request.remote_addr
    if user_ip not in usernames_by_ip:
        usernames_by_ip[user_ip] = f"User_{random.randint(1000, 9999)}"

    if os.path.exists(MESSAGE_LOG):
        with open(MESSAGE_LOG, 'r') as f:
            history = [line.strip() for line in f.readlines()[-50:]]
        emit('chat_history', history)

@socketio.on('disconnect')
def handle_disconnect():
    global connected_clients
    connected_clients = max(0, connected_clients - 1)
    emit('user_count', connected_clients, broadcast=True)

@socketio.on('message')
def handle_message(data):
    user_ip = request.remote_addr
    username = usernames_by_ip.get(user_ip, "Unknown")
    timestamp = datetime.now().strftime('%H:%M')

    try:
        msg_data = json.loads(data)
        msg_text = msg_data.get('text', '')
        location = msg_data.get('location')
        if location:
            formatted_msg = f'[{timestamp}] ({username} @ {location["lat"]:.4f},{location["lon"]:.4f}): {msg_text}'
        else:
            formatted_msg = f'[{timestamp}] ({username}): {msg_text}'
    except json.JSONDecodeError:
        formatted_msg = f'[{timestamp}] ({username}): {data}'

    print(f'Message: {formatted_msg}')
    with open(MESSAGE_LOG, 'a') as f:
        f.write(formatted_msg + '\n')

    # Attempt to forward to ESP32 (mesh fallback)
    if esp_serial and esp_serial.is_open:
        try:
            esp_serial.write((formatted_msg + '\n').encode())
        except Exception as e:
            print("Failed to send to ESP32:", e)

    send(formatted_msg, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='IP', port=5000)
