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

connected_clients = {}
MESSAGE_LOG = 'chat_log.txt'
usernames_by_id = {}

try:
    esp_serial = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
except Exception as e:
    esp_serial = None
    print("ESP32 not connected or not found:", e)

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Emergency Mesh Chat</title>
  <style>
    body { background-color: #0d1117; color: #c9d1d9; font-family: monospace; margin: 0; padding: 0; height: 100vh; display: flex; flex-direction: column; }
    header, #status, #inputArea { background-color: #161b22; border-bottom: 1px solid #30363d; padding: 1rem; text-align: center; }
    #messages { flex: 1; overflow-y: auto; padding: 1rem; }
    input[type="text"] { flex: 1; padding: 0.5rem; background: #0d1117; color: #c9d1d9; border: 1px solid #30363d; border-radius: 5px; }
    button { padding: 0.5rem 1rem; background: #238636; color: white; border: none; border-radius: 5px; cursor: pointer; }
    .map-link { color: #58a6ff; text-decoration: underline; cursor: pointer; }
  </style>
</head>
<body>
  <header><h1>🛡️ Disaster NYC Plan</h1></header>
  <div id="status">Connected Users: <span id="userCount">0</span></div>
  <div id="messages"></div>
  <div id="inputArea">
    <input id="myMessage" type="text" placeholder="Type your message..." autocomplete="off" />
    <button onclick="sendMessage()">Send</button>
  </div>

  <script src="/static/js/socket.io.min.js"></script>
  <script>
    if (!localStorage.getItem("nickname")) {
        const nick = prompt("Enter your nickname:");
        localStorage.setItem("nickname", nick);
    }
    if (!localStorage.getItem("clientId")) {
        localStorage.setItem("clientId", crypto.randomUUID());
    }

    const socket = io('http://IP:5000', {
        transports: ['polling'],
        withCredentials: true,
        query: {
            clientId: localStorage.getItem("clientId"),
            nickname: localStorage.getItem("nickname")
        }
    });

    const messages = document.getElementById('messages');
    const userCount = document.getElementById('userCount');

    socket.on('message', function(msg) {
        const item = document.createElement('div');
        if (msg.includes('/map')) {
            const coords = msg.match(/\/map\s+([-+]?[0-9]*\.?[0-9]+),\s*([-+]?[0-9]*\.?[0-9]+)/);
            if (coords) {
                const link = document.createElement('a');
                link.href = `https://www.google.com/maps?q=${coords[1]},${coords[2]}`;
                link.target = '_blank';
                link.className = 'map-link';
                link.innerText = `📍 View Map (${coords[1]}, ${coords[2]})`;
                item.appendChild(link);
            } else {
                item.textContent = msg;
            }
        } else {
            item.textContent = msg;
        }
        messages.appendChild(item);
        messages.scrollTop = messages.scrollHeight;
    });

    socket.on('user_count', count => userCount.textContent = count);
    socket.on('chat_history', history => {
        history.forEach(msg => {
            const div = document.createElement('div');
            div.textContent = msg;
            messages.appendChild(div);
        });
        messages.scrollTop = messages.scrollHeight;
    });

    function sendMessage() {
        const input = document.getElementById("myMessage");
        const msg = input.value.trim();
        if (!msg) return;
        if (msg.startsWith("/map")) {
            socket.send(JSON.stringify({ text: msg }));
        } else {
            navigator.geolocation.getCurrentPosition(pos => {
                socket.send(JSON.stringify({
                    text: msg,
                    location: { lat: pos.coords.latitude, lon: pos.coords.longitude }
                }));
            }, () => socket.send(JSON.stringify({ text: msg })));
        }
        input.value = '';
    }
  </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/static/js/socket.io.min.js')
def socketio_js():
    return send_from_directory('static/js/', 'socket.io.min.js')

@socketio.on('connect')
def connect():
    client_id = request.args.get('clientId')
    nickname = request.args.get('nickname', f"User_{random.randint(1000,9999)}")

    if client_id not in connected_clients:
        connected_clients[client_id] = request.sid
        usernames_by_id[client_id] = nickname

    emit('user_count', len(connected_clients), broadcast=True)

    if os.path.exists(MESSAGE_LOG):
        with open(MESSAGE_LOG, 'r') as f:
            history = [line.strip() for line in f.readlines()[-50:]]
        emit('chat_history', history)

@socketio.on('disconnect')
def disconnect():
    sid = request.sid
    for cid, session in list(connected_clients.items()):
        if session == sid:
            connected_clients.pop(cid, None)
            usernames_by_id.pop(cid, None)
            break
    emit('user_count', len(connected_clients), broadcast=True)

@socketio.on('message')
def message(data):
    client_id = request.args.get('clientId')
    username = usernames_by_id.get(client_id, "Unknown")
    timestamp = datetime.now().strftime('%H:%M')

    try:
        msg_data = json.loads(data)
        msg = msg_data.get('text', '')
        loc = msg_data.get('location')
        if loc:
            final = f'[{timestamp}] ({username} @ {loc["lat"]:.4f},{loc["lon"]:.4f}): {msg}'
        else:
            final = f'[{timestamp}] ({username}): {msg}'
    except:
        final = f'[{timestamp}] ({username}): {data}'

    with open(MESSAGE_LOG, 'a') as f:
        f.write(final + '\n')

    if esp_serial and esp_serial.is_open:
        try:
            esp_serial.write((final + '\n').encode())
        except Exception as e:
            print("ESP32 Write Error:", e)

    send(final, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='IP', port=5000)
