import tkinter as tk
import page_flags
from tkinter import messagebox
from fins_comm import pulse_w_bit, write_word

# =========================================================
# SOFT LIMITS (EDIT ONLY THESE VALUES)
# =========================================================
# Machine coordinates AFTER homing (mm)

X_MIN = 0
X_MAX = 240

Y_MIN = 0
Y_MAX = 240

Z_MIN = 0
Z_MAX = 240

# =========================================================
# =========================================================
# MOTION CONSTANTS
# =========================================================

PULSES_PER_MM_X = 100   # 10 mm pitch
PULSES_PER_MM_Y = 200   # 10 mm pitch
PULSES_PER_MM_Z = 100   # 5 mm pitch

UINT16_MAX = 65536


def to_unsigned_16bit(val: int) -> int:
    """
    Convert signed integer to unsigned 16-bit (two's complement)
    """
    if val < 0:
        return val + UINT16_MAX
    return val


class ManualPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f0f0f0")

        # ================= TITLE =================
        tk.Label(
            self,
            text="MANUAL CONTROL",
            font=("Arial", 16, "bold"),
            bg="#f0f0f0"
        ).pack(pady=10)

        body = tk.Frame(self, bg="#f0f0f0")
        body.pack(fill="both", expand=True)

        # =========================================================
        # LEFT SIDE → JOG CONTROL
        # =========================================================
        left = tk.Frame(body, bg="#f0f0f0")
        left.pack(side="left", padx=40, pady=20)

        jog = tk.LabelFrame(left, text="Jog Control", padx=40, pady=30)
        jog.pack(pady=20)

        self.btns = []

        # ---------- A0 ----------
        self.btns.append(
            tk.Button(jog, text="A0 −", width=12,
                      command=lambda: pulse_w_bit(0, 1))
        )
        self.btns.append(
            tk.Button(jog, text="A0 +", width=12,
                      command=lambda: pulse_w_bit(0, 2))
        )

        # ---------- A1 ----------
        self.btns.append(
            tk.Button(jog, text="A1 −", width=12,
                      command=lambda: pulse_w_bit(0, 3))
        )
        self.btns.append(
            tk.Button(jog, text="A1 +", width=12,
                      command=lambda: pulse_w_bit(0, 4))
        )

        # ---------- A2 (Z) ----------
        self.btns.append(
            tk.Button(jog, text="A2 −", width=12,
                      command=lambda: pulse_w_bit(0, 5))
        )
        self.btns.append(
            tk.Button(jog, text="A2 +", width=12,
                      command=lambda: pulse_w_bit(0, 6))
        )

        # ---------- Layout ----------
        self.btns[0].grid(row=0, column=0, padx=20)
        self.btns[1].grid(row=0, column=1, padx=20)

        self.btns[2].grid(row=1, column=0, pady=15)
        self.btns[3].grid(row=1, column=1, pady=15)

        self.btns[4].grid(row=2, column=0, pady=15)
        self.btns[5].grid(row=2, column=1, pady=15)

        self.estop = tk.Button(
            left,
            text="EMERGENCY STOP",
            bg="red",
            fg="white",
            font=("Arial", 14, "bold"),
            width=30,
            command=lambda: pulse_w_bit(1, 0)
        )
        self.estop.pack(pady=20)

        # =========================================================
        # RIGHT SIDE → GO TO (X, Y, Z)
        # =========================================================
        right = tk.LabelFrame(body, text="GO TO POSITION", padx=30, pady=25)
        right.pack(side="right", padx=40, pady=20, fill="y")

        tk.Label(right, text="X Position (mm)", font=("Arial", 11, "bold")) \
            .grid(row=0, column=0, sticky="w", pady=6)
        self.x_entry = tk.Entry(right, width=10, font=("Arial", 11))
        self.x_entry.grid(row=0, column=1, pady=6)

        tk.Label(right, text="Y Position (mm)", font=("Arial", 11, "bold")) \
            .grid(row=1, column=0, sticky="w", pady=6)
        self.y_entry = tk.Entry(right, width=10, font=("Arial", 11))
        self.y_entry.grid(row=1, column=1, pady=6)

        tk.Label(right, text="Z Position (mm)", font=("Arial", 11, "bold")) \
            .grid(row=2, column=0, sticky="w", pady=6)
        self.z_entry = tk.Entry(right, width=10, font=("Arial", 11))
        self.z_entry.grid(row=2, column=1, pady=6)

        self.goto_btn = tk.Button(
            right,
            text="GO TO (X, Y, Z)",
            width=18,
            height=2,
            font=("Arial", 12, "bold"),
            bg="#007acc",
            fg="white",
            command=self.goto_xyz
        )
        self.goto_btn.grid(row=3, column=0, columnspan=2, pady=20)

    # ================= PAGE FLAGS =================
    def start_update(self):
        # Set all other page flags to False, Manual active True

        page_flags.manual_active = True   # ✅ Manual active

        # Optionally enable buttons/entries
        self.set_enabled(True)

    def stop_update(self):
        page_flags.manual_active = False
        # Optionally disable buttons/entries
        self.set_enabled(False)
    
    
    # =========================================================
    # GO TO LOGIC WITH SOFT LIMIT CHECK (XYZ)
    # =========================================================
    def goto_xyz(self):
        try:
            x_mm = float(self.x_entry.get())
            y_mm = float(self.y_entry.get())
            z_mm = float(self.z_entry.get())
        except ValueError:
            messagebox.showerror(
                "Invalid Input",
                "Please enter valid numeric values for X, Y and Z."
            )
            return

        if not (X_MIN <= x_mm <= X_MAX):
            messagebox.showwarning(
                "Soft Limit Violation",
                f"X target {x_mm} mm exceeds soft limits\n"
                f"Allowed range: {X_MIN} – {X_MAX} mm"
            )
            return

        if not (Y_MIN <= y_mm <= Y_MAX):
            messagebox.showwarning(
                "Soft Limit Violation",
                f"Y target {y_mm} mm exceeds soft limits\n"
                f"Allowed range: {Y_MIN} – {Y_MAX} mm"
            )
            return

        if not (Z_MIN <= z_mm <= Z_MAX):
            messagebox.showwarning(
                "Soft Limit Violation",
                f"Z target {z_mm} mm exceeds soft limits\n"
                f"Allowed range: {Z_MIN} – {Z_MAX} mm"
            )
            return

        x_pulses = int(x_mm * PULSES_PER_MM_X)
        y_pulses = int(y_mm * PULSES_PER_MM_Y)
        z_pulses = int(z_mm * PULSES_PER_MM_Z)



        write_word("D", 86, to_unsigned_16bit(x_pulses))
        write_word("D", 88, to_unsigned_16bit(y_pulses))
        write_word("D", 90, to_unsigned_16bit(z_pulses))

        pulse_w_bit(4, 0)   # ITPL start

    # =========================================================
    # ENABLE / DISABLE
    # =========================================================
    def set_enabled(self, enable: bool):
        state = tk.NORMAL if enable else tk.DISABLED

        for b in self.btns:
            b.config(state=state)

        self.goto_btn.config(state=state)
        self.x_entry.config(state=state)
        self.y_entry.config(state=state)
        self.z_entry.config(state=state)
