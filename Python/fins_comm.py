import socket
import struct
import time
import plc_config as cfg
import page_flags

# ================= LOW LEVEL =================
def recv_exact(n, timeout=2.0):
    start = time.time()
    data = b""
    while len(data) < n:
        if time.time() - start > timeout:
            raise TimeoutError("PLC communication timed out")
        try:
            part = cfg.sock.recv(n - len(data))
        except socket.timeout:
            continue
        if not part:
            raise ConnectionError("PLC disconnected")
        data += part
    return data

def send_fins_header(length):
    cfg.sock.sendall(
        b"FINS" +
        struct.pack(">I", length) +
        b"\x00\x00\x00\x02" +
        b"\x00\x00\x00\x00"
    )

# ================= CONNECT =================
def connect_plc(log, status_lbl):
    try:
        try:
            if cfg.sock:
                cfg.sock.close()
        except:
            pass

        cfg.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cfg.sock.settimeout(5)
        cfg.sock.connect((cfg.PLC_IP, cfg.PLC_PORT))

        frame = b"FINS" + struct.pack(">I", 12) + b"\x00" * 12
        cfg.sock.sendall(frame)
        resp = recv_exact(16)

        cfg.CLIENT_NODE = resp[12]
        cfg.SERVER_NODE = resp[15]
        cfg.connected = True

        log(f"[✓] Connected | Client={cfg.CLIENT_NODE} PLC={cfg.SERVER_NODE}")
        status_lbl.config(text="PLC: CONNECTED", fg="green")
    except Exception as e:
        cfg.connected = False
        log(f"[!] Connect failed: {e}")
        status_lbl.config(text="PLC: DISCONNECTED", fg="red")

# ================= READ =================
def read_word(area, addr):
    with cfg.plc_lock:
        send_fins_header(26)
        body = bytes([
            0x80,0x00,0x02,0x00,
            cfg.SERVER_NODE,0x00,
            0x00,cfg.CLIENT_NODE,0x00,
            cfg.SID,
            0x01,0x01,
            cfg.MEMORY_AREAS[area],
            (addr>>8)&0xFF, addr&0xFF,
            0x00,
            0x00,0x01
        ])
        cfg.sock.sendall(body)
        hdr = recv_exact(8)
        length = struct.unpack(">I", hdr[4:8])[0]
        payload = recv_exact(length)
        return struct.unpack(">H", payload[22:24])[0]

def read_d_word(addr):
    return read_word("D", addr)

def read_bit(area, word, bit):
    return (read_word(area, word) >> bit) & 1

# ================= UNIFIED WRITE =================
def write_word(area, addr, values):

    # Allow HOMING START (W0.00) even if homing not completed
    if page_flags.homing_active:

        if area == "W" and addr == 0:
           pass  # allow homing start

        # allow emergency stop
        elif area == "W" and addr == 1:
           pass

        else:
           print("Write blocked: homing not completed")
           return
    """
    Unified FINS write:
    - values: int -> single word
    - values: list[int] -> multi-word
    """
    
    if isinstance(values, int):
        values = [values]

    word_count = len(values)

    with cfg.plc_lock:
        send_fins_header(26 + word_count*2)

        body = bytes([
            0x80,0x00,0x02,0x00,
            cfg.SERVER_NODE,0x00,
            0x00,cfg.CLIENT_NODE,0x00,
            cfg.SID,
            0x01,0x02,
            cfg.MEMORY_AREAS[area],
            (addr>>8)&0xFF,
            addr&0xFF,
            0x00,
            (word_count>>8)&0xFF,
            word_count&0xFF
        ])

        data = b''
        for v in values:
            data += bytes([(v>>8)&0xFF, v&0xFF])

        cfg.sock.sendall(body + data)
        hdr = recv_exact(8)
        length = struct.unpack(">I", hdr[4:8])[0]
        recv_exact(length)

# ================= BIT CONTROL =================
def set_w_bit(word, bit, state):
    current = read_word("W", word)
    new = current | (1<<bit) if state else current & ~(1<<bit)
    write_word("W", word, new)

def pulse_w_bit(word, bit, pulse_ms=100):

    if not cfg.connected:
        return
    
    # Allow HOMING START always
    if word == 0 and bit == 0:
        set_w_bit(word, bit, True)
        time.sleep(pulse_ms/1000)
        set_w_bit(word, bit, False)
        return

    # Allow emergency stop always
    if word == 1 and bit == 0:
        set_w_bit(word, bit, True)
        time.sleep(pulse_ms/1000)
        set_w_bit(word, bit, False)
        return

    # Block motion commands if homing active
    if page_flags.homing_active:
        print("Motion blocked: homing not completed")
        return

    set_w_bit(word, bit, True)
    time.sleep(pulse_ms/1000)
    set_w_bit(word, bit, False)

# ================= SAFETY RESET =================
def reset_machine_state():
    try:
        write_word("W",0,0)
        write_word("W",1,0)
        write_word("D",300,0)
        write_word("D",301,0)
    except:
        pass