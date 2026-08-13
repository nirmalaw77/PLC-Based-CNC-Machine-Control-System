import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import page_flags 

from fins_comm import (
    connect_plc,
    read_bit,
    read_d_word,
    reset_machine_state,
    pulse_w_bit
)
import plc_config as cfg

from pages.manual import ManualPage
from pages.monitor import MonitorPage
from pages.cnc import CNCTab
from pages.cnc2 import CNCTab2          # ✅ CNC(2)
from pages.gcode import GCodePage       # ✅ G-code generator
from pages.settings import SettingsPage


APP_NAME = "CNC HMI"
APP_VERSION = "9.8.1"   # safety-restored version

plc_values = {}  #Data contaner dictionary
running = True
plc_generation = 0


# ================= SIGNED CONVERSION =================
def to_signed_16bit(val):
    return val - 65536 if val >= 32768 else val


class CNC_HMI(tk.Tk):   #Create Main apllication window
    def __init__(self):   #Constructor function
        super().__init__() #Create Actual 
        ##self. means=This current window/My program itself

        self.title(f"{APP_NAME} v{APP_VERSION}")  #Disply window title
        self.geometry("1100x720")  #Windwo Size
        self.configure(bg="#CFEEC9")  #Background color setup

        self.was_connected = False #Track PLC Connecrion Status
        self.comm_ready = False # PLC com Initialized Successfully??
        self.reconnect_popup = None # Pop Up window for re connect
        self.home_popup = None
        page_flags.homing_active = True

        # ---- SHARED AXIS POSITIONS ----
        self.axis_pos = {"A0": 0, "A1": 0, "A2": 0} #Difine And reset A0 A1 A2
        self.plc_values = plc_values

        # ================= TOP BAR =================
        top = tk.Frame(self, bg="#e0e0e0")
        top.pack(fill="x")
## Create plc connection status text
        self.status_lbl = tk.Label(
            top, text="PLC: CONNECTING...",
            fg="orange", bg="#e0e0e0",
            font=("Arial", 10, "bold")
        )
        self.status_lbl.pack(side="left", padx=10)

        # ================= LOG =================## Create message console area
        self.log_box = scrolledtext.ScrolledText(
            self, height=6, bg="black", fg="lime"
        )
        self.log_box.pack(fill="x")

        def log(msg):
            self.log_box.insert(tk.END, msg + "\n")
            self.log_box.see(tk.END)

        self.log = log

        # ================= NAV BAR =================
        nav = tk.Frame(self, bg="#cfcfcf")  ## Create button row
        nav.pack(fill="x")

        self.nav_buttons = {}  #Create bttn and ech have name an internal page name
        nav_items = [
            ("Manual", "manual"),
            ("Monitor", "monitor"),
            ("CNC", "cnc"),
            ("CNC(2)", "cnc2"),
            ("G-Code", "gcode"),
            ("Settings", "settings"),

        ]

        for text, key in nav_items:
            btn = tk.Button(
                nav, text=text, width=14,
                state=tk.DISABLED,
                command=lambda k=key: self.show_page(k)  ## lambda create quick function(short way to write function without giving it a name)
            )   ## K=Key - Save correct value from loop
            btn.pack(side="left", padx=4)
            self.nav_buttons[key] = btn

        # ================= PAGES =================
        self.container = tk.Frame(self, bg="#f0f0f0") ##all pages appera inside this comntainer
        self.container.pack(fill="both", expand=True)

        self.pages = {
            "manual": ManualPage(self.container),
            "monitor": MonitorPage(self.container),
            "cnc": CNCTab(self.container, self),
            "cnc2": CNCTab2(self.container),
            "gcode": GCodePage(self.container),
            "settings": SettingsPage(self.container),
        } ## PAge object creations

        for p in self.pages.values(): ## place pages in same position
            p.place(relwidth=1, relheight=1)

        
        self.show_page("monitor") 
        self.pages["monitor"].start_update()

        self.monitor_cfg = self.pages["monitor"].get_monitor_config()

        self.reset_comm_state(initial=True)  #Reset GUI satatus (dis btn,clr val,show con stts)
        ## start two parallel task
        threading.Thread(target=self.auto_connect, daemon=True).start() ## connect plc automatically
        threading.Thread(target=self.plc_reader, daemon=True).start()   ##Read plc continuously

        self.after(100, self.gui_update)  ## GUI Update loop
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ================= STATE RESET =================
    def reset_comm_state(self, initial=False):   ## Reset communications (disable -manual control,navigation button,plc values)
        self.comm_ready = False
        self.pages["manual"].set_enabled(False)

        for b in self.nav_buttons.values():
            b.config(state=tk.DISABLED)

        plc_values.clear()
        self.pages["monitor"].clear_values()

        self.status_lbl.config(
            text="PLC: CONNECTING..." if initial else "PLC: INITIALIZING...",
            fg="orange"
        )

    # ================= CONNECTION ================= ##Auto connect function
    def auto_connect(self):
        self.log("Trying to connect PLC...")
        connect_plc(self.log, self.status_lbl)

        if cfg.connected:
            self.reset_comm_state(initial=False)
            return

        self.reset_comm_state()
        self.show_reconnect_popup(
            "PLC is not responding.\n\n"
            "Please power ON the PLC\n"
            "and click Reconnect."
        )

    # ================= RECONNECT POPUP =================## Reconct pop up function
    def show_reconnect_popup(self, message):
        if self.reconnect_popup and self.reconnect_popup.winfo_exists():
            return

        popup = tk.Toplevel(self)
        popup.title("PLC Connection")
        popup.geometry("360x180")
        popup.resizable(False, False)
        popup.configure(bg="#f0f0f0")
        popup.transient(self)
        popup.lift()
        popup.attributes("-topmost", True)
        popup.protocol("WM_DELETE_WINDOW", self.on_close)


        tk.Label(
            popup, text=message,
            fg="red", bg="#f0f0f0",
            font=("Arial", 11, "bold"),
            wraplength=320, justify="center"
        ).pack(pady=20)

        tk.Button(
            popup, text="RECONNECT PLC",
            width=20, height=2,
            font=("Arial", 11, "bold"),
            command=lambda: self.popup_reconnect(popup)
        ).pack(pady=10)

        self.reconnect_popup = popup

    def popup_reconnect(self, popup):
        global plc_generation
        self.log("Reconnecting PLC...")
        self.status_lbl.config(text="PLC: RECONNECTING...", fg="orange")

        connect_plc(self.log, self.status_lbl)

        if cfg.connected:
            plc_generation += 1
            self.reset_comm_state()
            popup.destroy()
            self.reconnect_popup = None
        else:
            self.status_lbl.config(text="PLC: DISCONNECTED", fg="red")

    # ================= HOMING POPUP ================= ## Homing Pop up Funcion
    def show_home_popup(self, busy):
        if self.home_popup and self.home_popup.winfo_exists():
            return

        popup = tk.Toplevel(self)
        popup.title("HOMING REQUIRED")
        popup.geometry("360x220")
        popup.resizable(False, False)
        popup.configure(bg="#f0f0f0")
        popup.transient(self)
        popup.lift()
        popup.attributes("-topmost", True)
        popup.protocol("WM_DELETE_WINDOW", self.on_close)

        self.home_msg = tk.Label(
            popup,
            text="Machine not homed.\n\nPlease start homing to continue.",
            fg="red", bg="#f0f0f0",
            font=("Arial", 12, "bold"),
            justify="center"
        )
        self.home_msg.pack(pady=20)

        self.home_btn = tk.Button(
            popup,
            text="START HOMING",
            width=20, height=2,
            font=("Arial", 12, "bold"),
            bg="#007acc", fg="white",
            command=lambda: pulse_w_bit(0, 0)
        )
        self.home_btn.pack(pady=10)

        self.home_popup = popup
        page_flags.homing_active = True
        self.update_home_popup(busy)

    def update_home_popup(self, busy):
        if not self.home_popup:
            return

        if busy:
            self.home_msg.config(
                text="HOMING IN PROGRESS...\n\nPlease wait.",
                fg="orange"
            )
            self.home_btn.config(state=tk.DISABLED)
        else:
            self.home_msg.config(
                text="Machine not homed.\n\nPlease start homing to continue.",
                fg="red"
            )
            self.home_btn.config(state=tk.NORMAL)

    # ================= PAGE SWITCH ================= ## show paages## New variable part
    def show_page(self, name):


     # reset all flags first
     page_flags.monitor_active = False
     page_flags.manual_active = False
     page_flags.cnc_active = False
     page_flags.cnc2_active = False
     page_flags.gcode_active = False
     page_flags.settings_active = False

    # activate selected page flag
     if name == "monitor":
        page_flags.monitor_active = True

     elif name == "manual":
        page_flags.manual_active = True

     elif name == "cnc":
        page_flags.cnc_active = True

     elif name == "cnc2":
        page_flags.cnc2_active = True

     elif name == "gcode":
        page_flags.gcode_active = True

     elif name == "settings":
        page_flags.settings_active = True

    # show selected page
     self.pages[name].tkraise()

    # ================= PLC READER =================  ##PLC reader runs continuounsly
    def plc_reader(self):
        global running, plc_generation
        local_gen = plc_generation

        while running and self.winfo_exists():
            if local_gen != plc_generation:
                local_gen = plc_generation

            if cfg.connected:  ## Check plc Connected
                try:
                    for name, area, word, bit in self.monitor_cfg:  ##Read values
                        if bit is None:
                            val = read_d_word(word)  
                            if name.endswith("PRV"):
                                val = to_signed_16bit(val)
                            plc_values[(area, word, bit)] = val
                        else:
                            plc_values[(area, word, bit)] = read_bit(area, word, bit)

                    self.axis_pos["A0"] = plc_values.get(("D", 220, None), 0)  ## axis values
                    self.axis_pos["A1"] = plc_values.get(("D", 230, None), 0)
                    self.axis_pos["A2"] = plc_values.get(("D", 240, None), 0)

                    master_home = plc_values.get(("W", 8, 0), 0)
                    homing_busy = plc_values.get(("W", 5, 0), 0)   ## Variables????

                    if not self.comm_ready:
                        self.comm_ready = True
                        self.status_lbl.config(text="PLC: INITIALIZED", fg="orange")

                    if master_home:
                        page_flags.homing_active = False
                        for b in self.nav_buttons.values():
                            b.config(state=tk.NORMAL)
                        self.pages["manual"].set_enabled(True)
                        self.status_lbl.config(text="PLC: READY", fg="green")

                        if self.home_popup:
                            self.home_popup.destroy()
                            self.home_popup = None
                    else:
                        for b in self.nav_buttons.values():
                            b.config(state=tk.DISABLED)
                        self.pages["manual"].set_enabled(False)
                        self.show_home_popup(homing_busy)
                        self.update_home_popup(homing_busy)

                    self.was_connected = True

                except Exception:
                    if self.was_connected:
                        self.was_connected = False
                        cfg.connected = False
                        
                        self.reset_comm_state()

                        self.status_lbl.config(
                            text="PLC: CONNECTION LOST",
                            fg="red"
                        )

                        self.log("PLC cable lost →  waiting for reconnect")

                        self.show_reconnect_popup(
                            "PLC connection lost.\n\n"
                            "Machine has been reset.\n"
                            "Please check the Ethernet cable and reconnect."
                        )

            time.sleep(0.02)

    def on_close(self):
        global running
        running = False

        try:
            if self.home_popup:
               self.home_popup.destroy()

            if self.reconnect_popup:
               self.reconnect_popup.destroy()
        except:
              pass

        self.destroy()        

    # ================= GUI UPDATE =================  ## GUI Update function
    def gui_update(self):
        self.pages["monitor"].update_values(plc_values)
        self.after(100, self.gui_update)



def start_gui():
    CNC_HMI().mainloop()