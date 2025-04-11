from flask import Flask, render_template_string, request, send_from_directory
from flask_socketio import SocketIO, send, emit
from datetime import datetime
import os
import random
import json
import serial

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

connected_sessions = set()
MESSAGE_LOG = 'chat_log.txt'
usernames_by_sid = {}
user_ips = {}

# Optional: Initialize serial communication with ESP32
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
        if (!localStorage.getItem("nickname")) {
            const nick = prompt("Enter your nickname:");
            localStorage.setItem("nickname", nick);
        }

        var socket = io('http://IP:5000', {
            transports: ['polling'],
            withCredentials: true
        });

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
            var nick = localStorage.getItem("nickname") || "Anon";

            if (msg !== '') {
                if (msg.startsWith("/map")) {
                    navigator.geolocation.getCurrentPosition(function(position) {
                        const data = {
                            text: msg,
                            location: {
                                lat: position.coords.latitude,
                                lon: position.coords.longitude
                            },
                            nickname: nick
                        };
                        socket.send(JSON.stringify(data));
                    }, function() {
                        socket.send(JSON.stringify({ text: msg, nickname: nick }));
                    });
                } else {
                    socket.send(JSON.stringify({ text: msg, nickname: nick }));
                }

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

@app.route('/static/js/socket.io.min.js')
def server_static_js():
    return send_from_directory('static/js/', 'socket.io.min.js')

@socketio.on('connect')
def handle_connect():
    connected_sessions.add(request.sid)
    user_ip = request.remote_addr

    if user_ip not in user_ips:
        user_ips[user_ip] = f"User_{random.randint(1000, 9999)}"

    usernames_by_sid[request.sid] = user_ips[user_ip]

    if os.path.exists(MESSAGE_LOG):
        with open(MESSAGE_LOG, 'r') as f:
            history = [line.strip() for line in f.readlines()[-50:]]
        emit('chat_history', history)

    emit('user_count', len(connected_sessions), broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    connected_sessions.discard(request.sid)
    usernames_by_sid.pop(request.sid, None)
    emit('user_count', len(connected_sessions), broadcast=True)

@socketio.on('message')
def handle_message(data):
    timestamp = datetime.now().strftime('%H:%M')

    try:
        msg_data = json.loads(data)
        text = msg_data.get('text', '')
        nickname = msg_data.get('nickname', 'Unknown')
        location = msg_data.get('location')

        if text.startswith('/map') and location:
            lat = location['lat']
            lon = location['lon']
            map_link = f'https://maps.google.com/?q={lat},{lon}'
            formatted_msg = f'[{timestamp}] <b>{nickname}</b>: <a href="{map_link}" target="_blank">📍 View My Location</a>'
        else:
            formatted_msg = f'[{timestamp}] <b>{nickname}</b>: {text}'

    except Exception as e:
        print("JSON parse error:", e)
        formatted_msg = f'[{timestamp}] <b>Unknown</b>: {data}'

    with open(MESSAGE_LOG, 'a') as f:
        f.write(formatted_msg + '\n')

    if esp_serial and esp_serial.is_open:
        try:
            esp_serial.write((formatted_msg + '\n').encode())
        except Exception as e:
            print("ESP32 error:", e)

    send(formatted_msg, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='IP', port=5000)
