import tkinter as tk
from tkinter import ttk
import time
import page_flags

from fins_comm import write_word, pulse_w_bit, read_bit

# =========================================================
# MACHINE CONSTANTS
# =========================================================
PULSES_PER_MM_X = 100
PULSES_PER_MM_Y = 200
PULSES_PER_MM_Z = 100   # ← ADDED

X_MIN = 0
X_MAX = 240
Y_MIN = 0
Y_MAX = 240
Z_MIN = 0               # ← ADDED
Z_MAX = 240             # ← ADDED

CANVAS_SIZE_PX = 260
MINOR_GRID_MM = 10
MAJOR_GRID_MM = 50

FRAME_DT = 0.02
CORRECTION_ALPHA = 0.15

# =========================================================
# BUFFER CONSTANTS
# =========================================================
STAGING_BASE = 1500      # D1500–D1559
BLOCK_STRIDE = 10
BLOCK_COUNT = 10
POS_SCALE = 10           # 0.1 mm resolution

# =========================================================
# TEST PROGRAM
# =========================================================
MOTION_BLOCKS = [
    (1,  0.0,   0.0,   0.0, 1200),
    (1, 20.0,  80.0,  20.0, 1200),
    (1, 50.0,  20.0,  80.0, 1200),
    (1,  0.0,   0.0, 0.0, 1200),
    (1,  0.0,   0.0,   0.0, 1200),
    (1, 0.0,   0.0, 0.0, 1200),
    (1,  0.0,   0.0,   0.0, 1200),
    (1,  0.0,   0.0,   0.0, 1200),
    (1,  0.0,   0.0,   0.0, 1200),
    (1,  0.0,   0.0,   0.0, 1200),

    (1,  50.0,   0.0,   0.0, 2400),
    (1,   0.0,   0.0,   0.0, 2400),
    (1,  40.0,   0.0,   0.0, 2400),
    (1,   0.0,   0.0,   0.0, 2400),
    (1,  50.0,   0.0,   0.0, 2400),
    (1,  100.0,  0.0,   0.0, 2400),
    (1,   0.0,   0.0,   0.0, 2400),

    (30,  0.0,   0.0,   0.0, 1200),  # STOP
]

# =========================================================
# HELPERS
# =========================================================
def mm_to_scaled(mm):
    return int(round(mm * POS_SCALE))


def write_staging_buffer(blocks):
    print(">>> Writing staging buffer")

    for i in range(BLOCK_COUNT):
        base = STAGING_BASE + i * BLOCK_STRIDE

        if i < len(blocks):
            instr, x, y, z, speed = blocks[i]
            write_word("D", base + 0, instr)
            write_word("D", base + 1, mm_to_scaled(x))
            write_word("D", base + 2, mm_to_scaled(y))
            write_word("D", base + 3, mm_to_scaled(z))
            write_word("D", base + 4, int(speed))
        else:
            write_word("D", base + 0, 30)
            write_word("D", base + 1, 0)
            write_word("D", base + 2, 0)
            write_word("D", base + 3, 0)
            write_word("D", base + 4, 0)


# =========================================================
# CNC TAB
# =========================================================
class CNCTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        # ================= UI =================
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", anchor="nw")

        right = ttk.Frame(main)
        right.pack(side="right", anchor="ne", padx=30, pady=30)

        self.x_var = tk.StringVar(value="X: 0.000 mm")
        self.y_var = tk.StringVar(value="Y: 0.000 mm")
        self.z_var = tk.StringVar(value="Z: 0.000 mm")   # ← ADDED

        ttk.Label(left, textvariable=self.x_var,
                  font=("Consolas", 13)).pack(anchor="w", padx=25, pady=5)
        ttk.Label(left, textvariable=self.y_var,
                  font=("Consolas", 13)).pack(anchor="w", padx=25)
        ttk.Label(left, textvariable=self.z_var,
                  font=("Consolas", 13)).pack(anchor="w", padx=25)  # ← ADDED

        self.canvas = tk.Canvas(
            left, width=CANVAS_SIZE_PX, height=CANVAS_SIZE_PX,
            bg="white", highlightthickness=1, highlightbackground="black"
        )
        self.canvas.pack(padx=25, pady=10)

        self.width_mm = X_MAX - X_MIN
        self.height_mm = Y_MAX - Y_MIN
        self.scale = CANVAS_SIZE_PX / max(self.width_mm, self.height_mm)

        self.draw_grid()
        self.draw_soft_limits()
        self.tool = self.canvas.create_oval(0, 0, 0, 0, fill="red")

        ttk.Label(right, text="SEQUENCES",
                  font=("Arial", 13, "bold")).pack(pady=10)

        ttk.Button(
            right, text="SEQUENCE 1",
            width=20,
            command=self.sequence_1
        ).pack(pady=10)

        self.disp_x = 0.0
        self.disp_y = 0.0
        self.disp_z = 0.0      # ← ADDED

        self.program_index = 0
        self.waiting_for_plc = False
        self.sequence_active = False

        self.update_position()
        self.after(50, self.check_plc_buffer)
    
    # ================= PAGE FLAGS =================
    def start_update(self):
        # Set all other page flags to False
        page_flags.cnc_active = False
        # ✅ Set this page active
        page_flags.cnc_active = True  # <-- change <this_page> to your page's flag, e.g., monitor_active

        # Optionally enable buttons/entries
        self.set_enabled(True)

    def stop_update(self):
        # ✅ Set this page inactive
        page_flags.cnc_active = False  # <-- change <this_page>
        # Optionally disable buttons/entries
        self.set_enabled(False)





    # =====================================================
    def draw_grid(self):
        for x in range(0, self.width_mm + 1, MINOR_GRID_MM):
            px = x * self.scale
            self.canvas.create_line(px, 0, px, CANVAS_SIZE_PX, fill="#e6e6e6")
        for y in range(0, self.height_mm + 1, MINOR_GRID_MM):
            py = CANVAS_SIZE_PX - (y * self.scale)
            self.canvas.create_line(0, py, CANVAS_SIZE_PX, py, fill="#e6e6e6")

    def draw_soft_limits(self):
        self.canvas.create_rectangle(
            0, 0, CANVAS_SIZE_PX, CANVAS_SIZE_PX,
            outline="black", width=2
        )

    def pulses_to_mm(self, pulses, axis):
        if axis == "A0":
            return pulses / PULSES_PER_MM_X
        if axis == "A1":
            return pulses / PULSES_PER_MM_Y
        if axis == "A2":                     # ← ADDED
            return pulses / PULSES_PER_MM_Z
        return 0.0

    # =====================================================
    def update_position(self):
        try:
            px = self.app.axis_pos["A0"]
            py = self.app.axis_pos["A1"]
            pz = self.app.axis_pos["A2"]   # ← ADDED

            x = self.pulses_to_mm(px, "A0")
            y = self.pulses_to_mm(py, "A1")
            z = self.pulses_to_mm(pz, "A2")  # ← ADDED

            self.disp_x += CORRECTION_ALPHA * (x - self.disp_x)
            self.disp_y += CORRECTION_ALPHA * (y - self.disp_y)
            self.disp_z += CORRECTION_ALPHA * (z - self.disp_z)  # ← ADDED

            self.x_var.set(f"X: {self.disp_x:.3f} mm")
            self.y_var.set(f"Y: {self.disp_y:.3f} mm")
            self.z_var.set(f"Z: {self.disp_z:.3f} mm")           # ← ADDED

            cx = self.disp_x * self.scale
            cy = CANVAS_SIZE_PX - (self.disp_y * self.scale)
            self.canvas.coords(self.tool, cx-4, cy-4, cx+4, cy+4)

        except:
            pass

        self.after(int(FRAME_DT * 1000), self.update_position)

    # =====================================================
    def sequence_1(self):
        if self.sequence_active:
            return
        if self.master.master.homing_active:
            return

        if read_bit("W", 6, 4):
            return

        write_word("D", 290, 0)

        self.sequence_active = True
        self.program_index = 0
        self.waiting_for_plc = True

        chunk = MOTION_BLOCKS[:BLOCK_COUNT]
        write_staging_buffer(chunk)

        pulse_w_bit(6, 3)
        pulse_w_bit(6, 2)
        pulse_w_bit(6, 0)

        self.program_index += len(chunk)

    # =====================================================
    def check_plc_buffer(self):
        try:
            if self.master.master.homing_active:
                return
            if self.waiting_for_plc and read_bit("W", 6, 4):

                if self.program_index < len(MOTION_BLOCKS):
                    chunk = MOTION_BLOCKS[
                        self.program_index:
                        self.program_index + BLOCK_COUNT
                    ]

                    write_staging_buffer(chunk)
                    pulse_w_bit(6, 3)

                    self.program_index += len(chunk)
                else:
                    self.waiting_for_plc = False
                    self.sequence_active = False

        except:
            pass

        self.after(50, self.check_plc_buffer)
