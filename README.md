# 🛡️ Disaster Mesh Chat

![Status](https://img.shields.io/badge/status-alpha-blueviolet)
![Built with](https://img.shields.io/badge/Python-3.10+-yellow?logo=python)
![License](https://img.shields.io/badge/license-MIT-green)
![Offline Ready](https://img.shields.io/badge/offline-mesh--compatible-critical)

![image](https://github.com/user-attachments/assets/7b27496f-40ef-473f-99e9-915dd43b9bb8)


> Offline-first, peer-to-peer emergency chat system with ESP32 mesh fallback — designed for when the grid goes down.

---

![Disaster Mesh Chat Demo](demo.gif)  
*Demo: Chatting between two local clients over LAN + ESP32 fallback*

---

## 🌐 Features

✅ Real-time chat over local network  
✅ ESP32 serial/mesh fallback mode  
✅ Geo-tagged messages (if browser supports GPS)  
✅ Image upload + rendering  
✅ Minimalistic, mobile-friendly dark UI  
✅ Stores last 50 messages for recovery  

---

## 🧠 Why?

This tool was built for disaster scenarios where:

- 📡 Internet is down
- ⚡ Power grid is unreliable
- 🛰️ Satellite or cell coverage is gone
- 👥 People still need to communicate securely and fast

Perfect for first responders, local communities, off-grid projects, or tech demos.

---

## ⚙️ Setup

### 🔧 Requirements

- Python 3.10+
- Flask
- Flask-SocketIO
- pyserial (if using ESP32)

### 💾 Installation

```bash
git clone https://github.com/yourusername/disaster-mesh-chat.git
cd disaster-mesh-chat
pip install -r requirements.txt
```

📁 Directory Structure
```
├── static/
│   └── js/
│       └── socket.io.min.js  # Required client-side script
├── uploads/                  # Image uploads go here
├── chat_log.txt              # Chat history (optional)
└── disaster_chat_server_esp32.py
```

### ▶️ Running the Server
```
python disaster_chat_server_esp32.py
```

### 🔌 ESP32 Integration (Optional)
Connect ESP32 via USB (adjust Serial('/dev/ttyUSB0', ...) path as needed)

Used as a fallback broadcast when Socket.IO fails

Mesh-compatible serial messages (basic demo, extendable)

### 🔐 Security Warnings
This prototype does not encrypt messages. For real deployments:

- Add HTTPS (WSS) support

- Use authentication tokens

- Implement E2E encryption (NaCl, AES-GCM, etc.)

### 💡 Future Ideas
- Decentralized peer-to-peer mesh over ESP-NOW / LoRa

- E2E encrypted channels

- Offline-first progressive web app (PWA)

- Voice messages over ESP32

- BLE fallback or QR-code pairing

### 🤝 Contributing
PRs, bug reports, and feedback welcome!
Let's make communication resilient AF ⚡
