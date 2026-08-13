import threading

PLC_IP = "192.168.250.10"
PLC_PORT = 9600   # Omron CP2E FINS/TCP port

CLIENT_NODE = None
SERVER_NODE = None
SID = 0x01

sock = None
connected = False

# 🔐 PLC communication lock (CRITICAL)
plc_lock = threading.Lock()
# Only ONE thread talks to PLC at a time → prevents broken FINS packets

MEMORY_AREAS = {
    "CIO": 0xB0,
    "W":   0xB1,
    "D":   0x82,
    "A":   0x80,
}
