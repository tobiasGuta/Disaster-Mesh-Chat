# 🛡️ Disaster Mesh Chat

![Status](https://img.shields.io/badge/status-alpha-blueviolet)
![Built with](https://img.shields.io/badge/Python-3.10+-yellow?logo=python)
![License](https://img.shields.io/badge/license-MIT-green)
![Offline Ready](https://img.shields.io/badge/offline-mesh--compatible-critical)

![image](https://github.com/user-attachments/assets/7b27496f-40ef-473f-99e9-915dd43b9bb8)


> peer-to-peer emergency chat system with ESP32 + LoRa mesh fallback  designed for when the grid goes down.

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


### 💡 Future Ideas

🧠 Your Ideal Setup (3-Part Architecture)
✅ 1. Raspberry Pi (the Brain):
- Runs the Flask-SocketIO chat server.

- Handles user connections, message routing, and basic message logging.

- Interfaces with the ESP32 over serial (UART) to send/receive LoRa messages.

- Optional: Can act as a Wi-Fi access point too (but ESP32 is better for power).

✅ 2. ESP32 (the Bridge):
- Acts as the middleware between Raspberry Pi and LoRa.

- Connected to LoRa via UART (e.g., RYLR998).

- Can also be configured as a Wi-Fi access point for local clients if no Pi is present.

- Converts JSON commands from Pi to LoRa packets and vice versa.

✅ 3. LoRa (the Network):
- The mesh transport layer — RYLR998 modules relay messages between nodes.

- Set to the same frequency (868 or 915 MHz depending on region).

- Uses message-forwarding logic to hop across nodes to reach the target.

### ⚙️ How a Message Flows:

```
[User's Phone/Laptop]
       |
     Wi-Fi
       ↓
[Flask Chat on Raspberry Pi]
       |
     Serial
       ↓
   [ESP32]
       |
     UART
       ↓
 [LoRa Module]
       |
     Airwaves 🌍
       ↓
[Next Node → Another ESP32+LoRa]
       ↓
     Repeat
       ↓
[Target Node Receives & Displays Message]
```

🔥 Why This Setup Works Best:
```
Component	                     Role	                            Benefit
Raspberry Pi	                   Server & brain	           Full control, logs, real-time chat, Python libraries
ESP32	                          Bridge & AP	           Low power, great at UART + Wi-Fi combo
LoRa (RYLR998)	               Mesh network	            Long range, offline, multi-hop
```

### Example

- This is a demonstration of how I want to apply this project using the ESP32 and LoRa: https://youtu.be/9azEfCQNhSA

![image](https://github.com/user-attachments/assets/db8b7834-0adf-4710-a1f5-62ceafca4f26)

In this example, Community A (Brooklyn) wants to send a message to Community D (The Bronx), but they’re too far apart for a direct LoRa connection.

However, with LoRa and mesh networking, that's not a problem. The system automatically finds intermediate nodes, like Communities B and C, to relay the message. It hops across the network until it reaches the destination.

This makes communication resilient, even if nodes are far apart, as long as there’s a path through the mesh.

![image](https://github.com/user-attachments/assets/2054137c-ac0a-420d-aa09-644f82d1f359)

Let’s say “E” represents city-owned LoRa nodes, and “R” represents individual residents or community members who’ve set up their own LoRa nodes.

Together, they form a mesh network, where messages can travel from node to node, no matter who owns them, as long as they’re connected.

This decentralized model empowers both cities and people to build a resilient communication system that stays up even when everything else goes down.


### 🔐 Security Warnings
This prototype does not encrypt messages. For real deployments:

- Add HTTPS (WSS) support

- Implement E2E encryption (NaCl, AES-GCM, etc.)

### 🤝 Contributing
PRs, bug reports, and feedback welcome!
Let's make communication resilient AF ⚡
