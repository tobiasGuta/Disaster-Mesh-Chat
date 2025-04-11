from flask import Flask, render_template_string, request, send_from_directory
from flask_socketio import SocketIO, send, emit
from datetime import datetime, timedelta
import os
import random
import json
import serial
import socket

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# SSL certificate generator
def generate_self_signed_cert(cert_file="cert.pem", key_file="key.pem"):
    if os.path.exists(cert_file) and os.path.exists(key_file):
        return cert_file, key_file

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Offline"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "DisasterMesh"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MeshComm"),
        x509.NameAttribute(NameOID.COMMON_NAME, "mesh.local"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
        .sign(key, hashes.SHA256())
    )

    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    with open(key_file, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    return cert_file, key_file


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

connected_clients = 0
MESSAGE_LOG = 'chat_log.txt'
usernames_by_ip = {}

# Optional: Serial connection to ESP32
try:
    esp_serial = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
except Exception as e:
    esp_serial = None
    print("ESP32 not connected or not found:", e)

HTML = '''...'''  # Keep your full HTML string here (unchanged)

@app.route('/')
def index():
    return render_template_string(HTML)

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
        formatted_msg = f'[{timestamp}] ({username}): {msg_text}'
    except json.JSONDecodeError:
        formatted_msg = f'[{timestamp}] ({username}): {data}'

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
    cert_file, key_file = generate_self_signed_cert()
    ip_addr = socket.gethostbyname(socket.gethostname())
    print(f"🔐 HTTPS server running at: https://{ip_addr}:5000")
    socketio.run(app, host='0.0.0.0', port=5000, ssl_context=(cert_file, key_file))
