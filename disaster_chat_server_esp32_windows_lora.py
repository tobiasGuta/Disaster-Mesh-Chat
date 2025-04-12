from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, send, emit
from datetime import datetime
import os
import random
import json
import serial

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins='*')

connected_clients = 0
MESSAGE_LOG = 'chat_log.txt'
usernames_by_ip = {}

# Initialize serial connection to ESP32
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
        a {
            color: #58a6ff;
            text-decoration: underline;
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
    </div>

    <script src="/static/js/socket.io.min.js"></script>
    <script>
        var socket = io();
        var messages = document.getElementById('messages');
        var userCount = document.getElementById('userCount');

        socket.on('message', function(msg) {
            var item = document.createElement('div');
            item.innerHTML = msg;
            messages.appendChild(item);
            messages.scrollTop = messages.scrollHeight;
        });

        socket.on('user_count', function(count) {
            userCount.textContent = count;
        });

        socket.on('chat_history', function(history) {
            history.forEach(function(msg) {
                var item = document.createElement('div');
                item.innerHTML = msg;
                messages.appendChild(item);
            });
            messages.scrollTop = messages.scrollHeight;
        });

        function sendMessage() {
            var input = document.getElementById("myMessage");
            var msg = input.value.trim();
            if (msg !== '') {
                socket.send(msg);
                input.value = '';
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

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

    # If text message
    if isinstance(data, str):
        data = data.strip()
        if data.lower().startswith('/map '):
            location = data[5:].strip()
            map_url = f"https://www.google.com/maps/search/?api=1&query={location.replace(' ', '+')}"
            formatted_msg = f'[{timestamp}] ({username}): 📍 <a href="{map_url}" target="_blank">{location}</a>'
        else:
            formatted_msg = f'[{timestamp}] ({username}): {data}'
    else:
        formatted_msg = f'[{timestamp}] ({username}): {json.dumps(data)}'

    print(f'Message: {formatted_msg}')
    with open(MESSAGE_LOG, 'a') as f:
        f.write(formatted_msg + '\n')

    if esp_serial and esp_serial.is_open:
        try:
            esp_serial.write((formatted_msg + '\n').encode())
        except Exception as e:
            print("Failed to send to ESP32:", e)

    send(formatted_msg, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
