import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import time
import re

from fins_comm import write_word, pulse_w_bit, read_bit, read_word, set_w_bit
import page_flags


# =========================================================
# PLC BUFFER CONFIG
# =========================================================
BLOCK_COUNT = 20
STAGING_BASE = 1500
BLOCK_STRIDE = 10

POS_RESOLUTION = 0.1


def q(val):
    return round(val / POS_RESOLUTION) * POS_RESOLUTION


# =========================================================
# FORMAT PREVIEW
# =========================================================
def format_motion_blocks(blocks):
    lines = ["MOTION_BLOCKS = ["]
    for instr, x, y, z, feed in blocks:
        lines.append(f"    ({instr}, {x:7.1f}, {y:7.1f}, {z:7.1f}, {feed}),")
    lines.append("]")
    return "\n".join(lines)


# =========================================================
# GCODE PARSER
# =========================================================
def parse_gcode(lines):

    blocks = []

    x = y = z = 0.0
    feed = 1200

    for raw in lines:

        line = raw.strip().upper()

        if not line or line.startswith(";") or line.startswith("("):
            continue

        if "M30" in line:
            blocks.append((30, 0.0, 0.0, 0.0, feed))
            break

        if line.startswith(("G0", "G1")):

            if "F" in line:
                try:
                    feed = int(float(re.findall(r"F([\d.]+)", line)[0]))
                except:
                    pass

            if "X" in line:
                x = float(re.findall(r"X([-.\d]+)", line)[0])

            if "Y" in line:
                y = float(re.findall(r"Y([-.\d]+)", line)[0])

            if "Z" in line:
                z = abs(float(re.findall(r"Z([-.\d]+)", line)[0]))

            blocks.append((1, q(x), q(y), q(z), feed))

    if not blocks or blocks[-1][0] != 30:
        blocks.append((30, 0.0, 0.0, 0.0, feed))

    return blocks


# =========================================================
# WRITE BUFFER TO PLC
# =========================================================
def write_staging(blocks):

    buffer = []

    for i in range(BLOCK_COUNT):

        if i < len(blocks):

            instr, x, y, z, feed = blocks[i]

            buffer.extend([
                instr,
                int(round(x * 10)),
                int(round(y * 10)),
                int(round(z * 10)),
                int(feed),
                0, 0, 0, 0, 0
            ])

        else:

            buffer.extend([30, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    write_word("D", STAGING_BASE, buffer)


# =========================================================
# CNC2 PAGE
# =========================================================
class CNCTab2(tk.Frame):

    def __init__(self, parent):

        super().__init__(parent, bg="#f0f0f0")

        self.blocks = []
        self.index = 0
        self.active = False
        self.running = True

        self.executed_count = 0
        self.start_line_offset = 0
        self.request_flag = False

        self.force_active = False
        self.auto_follow = True
        self.user_scrolled = False
        self.last_highlight = -1

        self.follow_mode = True
        self.last_user_scroll_time = time.time()
        self.pack(fill="both", expand=True)

        tk.Label(
            self,
            text="CNC (G-CODE EXECUTION)",
            font=("Arial", 16, "bold"),
            bg="#f0f0f0"
        ).pack(pady=10)


        # ================= BUTTON ROW =================

        btns = tk.Frame(self, bg="#f0f0f0")
        btns.pack(pady=10)


        tk.Button(
            btns,
            text="OPEN G-CODE",
            width=18,
            command=self.load_gcode
        ).pack(side="left", padx=10)


        tk.Button(
            btns,
            text="TRANSFER TO PLC",
            width=18,
            bg="#009688",
            fg="white",
            command=self.transfer_to_plc
        ).pack(side="left", padx=10)


        tk.Button(
            btns,
            text="START EXECUTION",
            width=18,
            bg="#007acc",
            fg="white",
            command=self.start
        ).pack(side="left", padx=10)


        tk.Label(btns, text="Start Line:", bg="#f0f0f0").pack(side="left")

        self.start_line_entry = tk.Entry(btns, width=6)
        self.start_line_entry.pack(side="left", padx=5)


        # ================= PAUSE BUTTON =================

        self.force_btn = tk.Button(
            btns,
            text="PAUSE",
            width=14,
            bg="gray",
            fg="white",
            command=self.toggle_force
        )

        self.force_btn.pack(side="left", padx=10)


        # ================= STOP BUTTON =================

        tk.Button(
            btns,
            text="STOP",
            width=14,
            bg="red",
            fg="white",
            command=self.stop_execution
        ).pack(side="left", padx=10)


        # ================= STATUS =================

        self.status = tk.Label(
            self,
            text="No file loaded",
            font=("Arial", 11),
            bg="#f0f0f0"
        )

        self.status.pack(pady=5)


        self.line_tracker = tk.Label(
            self,
            text="G-code Line count: -",
            font=("Arial", 11),
            bg="#f0f0f0"
        )

        self.line_tracker.pack(pady=5)


        self.executed_line_label = tk.Label(
            self,
            text="Executed Line Count: -",
            font=("Arial", 11),
            bg="#f0f0f0"
        )

        self.executed_line_label.pack(pady=5)


        # ================= MOTION BLOCK VIEWER (LEFT PANEL WITH SCROLLBAR) =================

        motion_frame = tk.Frame(self, bg="#f0f0f0", width=350)
        motion_frame.pack(side="left", fill= "y", padx=10, pady=10)
        motion_frame.pack_propagate(False)  

        # container layout stability
        motion_frame.grid_rowconfigure(0, weight=1)
        motion_frame.grid_columnconfigure(0, weight=1)

        self.motion_text = tk.Text(
            motion_frame,
            width=38,
            font=("#0B0C0C", 11),
            bg="#A6C4D3",
            fg="#FFFFFF",
            wrap="none"
        )

        scrollbar = tk.Scrollbar(
        motion_frame,
          orient="vertical",
          command=self.motion_text.yview
        )

        # layout (stable CNC-style)
        self.motion_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.motion_text.configure(yscrollcommand=scrollbar.set)


        # highlight style
        self.motion_text.tag_config(
           "running",
           background="#CFF3D9"
        )
        # disable auto-follow when user scrolls
        self.motion_text.bind("<MouseWheel>", self.on_user_scroll)
        self.motion_text.bind("<Button-4>", self.on_user_scroll)
        self.motion_text.bind("<Button-5>", self.on_user_scroll)


        threading.Thread(target=self.poll_plc_loop, daemon=True).start()

        self.after(50, self.update_gui)


    # =========================================================
    # LOAD FILE
    # =========================================================

    def load_gcode(self):

        self.user_scrolled = False

        path = filedialog.askopenfilename(
            filetypes=[("G-code Files", "*.nc *.gcode *.txt")]
        )

        if not path:
            return

        try:

            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                self.blocks = parse_gcode(f.readlines())

            self.index = 0
            self.active = False

            # ================= LOAD INTO MOTION VIEWER =================

            self.motion_text.delete("1.0", tk.END)
            self.auto_follow = True

            for i, block in enumerate(self.blocks, start=1):

                self.motion_text.insert(
                   tk.END,
                   f"{i:04}  {block}\n"
                ) 

            self.status.config(
                text=f"Loaded {len(self.blocks)} motion blocks"
            )

            self.line_tracker.config(
                text=f"G-code Line count: {len(self.blocks)-1}"
            )

        except Exception as e:
            messagebox.showerror("Error", str(e))


    # =========================================================
    # TRANSFER BUFFER (supports restart-from-line)
    # =========================================================

    def transfer_to_plc(self):

        if not self.blocks:

            messagebox.showwarning(
                "No Data",
                "Load G-code first"
            )

            return


        start_line = self.start_line_entry.get().strip()


        if start_line:

            try:

                start_line = int(start_line)

                if start_line < 0 or start_line >= len(self.blocks):

                    messagebox.showwarning(
                        "Invalid Line",
                        "Entered line number out of range"
                    )

                    return


                confirm = messagebox.askyesno(
                    "Restart From Line",
                    f"Transfer starting from selected line {start_line}?"
                )

                if not confirm:
                    return


                self.index = start_line
                self.start_line_offset = start_line


            except:

                messagebox.showwarning(
                    "Invalid Input",
                    "Enter valid numeric line"
                )

                return

        else:

            self.index = 0
            self.start_line_offset = 0


        chunk = self.blocks[self.index:self.index + BLOCK_COUNT]

        write_staging(chunk)

        self.index += len(chunk)

        self.status.config(
            text=f"Transferred from line {self.index-len(chunk)}"
        )


    # =========================================================
    # START EXECUTION
    # =========================================================

    def start(self):

        if self.force_active:

            messagebox.showwarning(
                "Pause Active",
                "Resume before starting execution."
            )

            return


        if not self.blocks:

            messagebox.showwarning(
                "No Data",
                "Load G-code first"
            )

            return


        self.active = True

        
        pulse_w_bit(6, 2)
        pulse_w_bit(6, 0)

        self.status.config(text="Running...")

    def on_user_scroll(self, event):
        self.follow_mode = False
        self.last_user_scroll_time = time.time()
    
    def disable_autofollow(self, event):
        self.auto_follow = False



    def highlight_line(self, line_no):

        

           self.motion_text.tag_remove("running", "1.0", tk.END)

           self.motion_text.tag_add(
              "running",
              f"{line_no}.0",
              f"{line_no}.end"
            )

            



    # =========================================================
    # PAUSE / RESUME
    # =========================================================

    def toggle_force(self):

        try:

            self.force_active = not self.force_active

            set_w_bit(14, 0, self.force_active)

            if self.force_active:

                self.force_btn.config(text="RESUME", bg="orange")

                self.status.config(text="Pause Activated")

            else:

                self.force_btn.config(text="PAUSE", bg="gray")

                self.status.config(text="Pause Released")

        except Exception as e:

            print("FORCE TOGGLE ERROR:", e)


    # =========================================================
    # STOP
    # =========================================================

    def stop_execution(self):

        try:

            set_w_bit(1, 2, True)
            time.sleep(0.02)
            set_w_bit(1, 2, False)

            set_w_bit(9, 0, True)
            time.sleep(0.02)
            set_w_bit(9, 0, False)

            self.active = False
            self.index = 0

            if self.force_active:

                self.force_active = False

                set_w_bit(14, 0, False)

                self.force_btn.config(text="PAUSE", bg="gray")

            self.status.config(
                text="Execution stopped by operator"
            )

        except Exception as e:

            print("STOP BUTTON ERROR:", e)


    # =========================================================
    # PLC POLL THREAD
    # =========================================================

    def poll_plc_loop(self):

        while self.running:

            if page_flags.cnc2_active:

                try:

                    self.executed_count = read_word("D", 296)

                    self.request_flag = read_bit("W", 11, 0)

                except:

                    pass

            time.sleep(0.012)


    # =========================================================
    # STREAM NEXT BLOCKS
    # =========================================================

    def update_gui(self):

        if page_flags.cnc2_active:

            try:

                if self.blocks:

                    self.line_tracker.config(
                        text=f"G-code Line count: {len(self.blocks)-1}"
                    )

                else:

                    self.line_tracker.config(
                        text="G-code Line count: -"
                    )


                display_line = self.start_line_offset + self.executed_count
                # auto re-enable follow after 3 seconds of no scrolling
                if time.time() - self.last_user_scroll_time > 3:
                   self.follow_mode = True

                # 🔥 ONLY update highlight if line changed
                if display_line != self.last_highlight:
                   self.highlight_line(display_line)
                   self.last_highlight = display_line

                # ONLY auto scroll if user is NOT scrolling
                if self.follow_mode:
                   self.motion_text.after_idle(
                     lambda: self.motion_text.see(f"{display_line}.0")
                    )

                self.executed_line_label.config(
                  text=f"Executed Line Count: {display_line}"
  
                )


                if self.request_flag and self.index < len(self.blocks):

                    chunk = self.blocks[
                        self.index:self.index + BLOCK_COUNT
                    ]

                    write_staging(chunk)

                    self.index += len(chunk)

                    pulse_w_bit(11, 1)

                    self.status.config(
                        text="Sent next block set to PLC"
                    )


                elif self.index >= len(self.blocks):

                    self.status.config(
                        text="Final blocks sent to PLC"
                    )

            except:

                pass

        self.after(20, self.update_gui)