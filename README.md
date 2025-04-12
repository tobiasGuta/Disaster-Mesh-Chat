# 🛡️ Disaster Mesh Chat

![Status](https://img.shields.io/badge/status-alpha-blueviolet)
![Built with](https://img.shields.io/badge/Python-3.10+-yellow?logo=python)
![License](https://img.shields.io/badge/license-MIT-green)
![Offline Ready](https://img.shields.io/badge/offline-mesh--compatible-critical)

![image](https://github.com/user-attachments/assets/7b27496f-40ef-473f-99e9-915dd43b9bb8)


> peer-to-peer emergency chat system with ESP32 mesh fallback  designed for when the grid goes down.

---


<img src="https://github.com/user-attachments/assets/d624d1c7-88ae-4b2a-9ac3-c1c924102b84" width="800"/>


*Demo: Chatting between two local clients over LAN + ESP32 fallback*

---

## 🌐 Features

✅ Real-time chat over local network  
✅ ESP32 serial/ Lora mesh fallback mode  
✅ Geo-tagged messages (if browser supports GPS)   
✅ Minimalistic, mobile-friendly dark UI  
✅ Stores last 50 messages for recovery  

---

## 🧠 Why?

This tool was built for disaster scenarios where:

- 📡 Internet is down
- ⚡ Power grid is unreliable
- 🛰️ Satellite or cell coverage is gone
- 👥 People still need to communicate securely and fast

Perfect for first responders, local communities.

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

### Chat GUI

![image](https://github.com/user-attachments/assets/81834e09-886f-4e30-895d-9e007c20fee2)


### 🔐 Security Warnings
This prototype does not encrypt messages. For real deployments:

- Add HTTPS (WSS) support

- Implement E2E encryption (NaCl, AES-GCM, etc.)

### 💡 Future Ideas
- Decentralized peer-to-peer mesh over ESP-NOW / LoRa

- E2E encrypted channels

- Offline-first progressive web app (PWA)


### Example

- This is a demonstration of how I want to apply this project using the ESP32 and LoRa: https://youtu.be/9azEfCQNhSA

![image](https://github.com/user-attachments/assets/db8b7834-0adf-4710-a1f5-62ceafca4f26)

In this example, Community A (Brooklyn) wants to send a message to Community D (The Bronx), but they’re too far apart for a direct LoRa connection.

However, with LoRa and mesh networking, that's not a problem. The system automatically finds intermediate nodes, like Communities B and C, to relay the message. It hops across the network until it reaches the destination.

This makes communication resilient, even if nodes are far apart, as long as there’s a path through the mesh.

### 🔌 ESP32 Integration (Optional)
Connect ESP32 via USB (adjust Serial('/dev/ttyUSB0', ...) path as needed)

Used as a fallback broadcast when Socket.IO fails

Mesh-compatible serial messages (basic demo, extendable)

### 🤝 Contributing
PRs, bug reports, and feedback welcome!
Let's make communication resilient AF ⚡
