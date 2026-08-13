import tkinter as tk
import page_flags
from tkinter import messagebox, filedialog

# =========================================================
# FEED CONFIGURATION (mm/min)
# =========================================================
PLUNGE_FEED = 100
CUT_FEED = 1200
SAFE_Z = 5.0
RESOLUTION = 0.1


def q(val):
    return round(val / RESOLUTION) * RESOLUTION


# =========================================================
# G-CODE PAGE (FRAME, NOT Tk)
# =========================================================
class GCodePage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f0f0f0")

        tk.Label(
            self,
            text="G-CODE GENERATOR",
            font=("Arial", 16, "bold"),
            bg="#f0f0f0"
        ).pack(pady=10)

        self.build_ui()


# ================= PAGE FLAGS =================
    def start_update(self):
        # Set all other page flags to False
        # ✅ Set this page active
        page_flags.gcode_active = True  # <-- change <this_page> to your page's flag, e.g., monitor_active

        # Optionally enable buttons/entries
        self.set_enabled(True)

    def stop_update(self):
        # ✅ Set this page inactive
        page_flags.gcode_active = False  # <-- change <this_page>
        # Optionally disable buttons/entries
        self.set_enabled(False)
    # -----------------------------------------------------
    def build_ui(self):
        form = tk.Frame(self, bg="#f0f0f0")
        form.pack(side="left", padx=10, pady=10)

        def add(label, row):
            tk.Label(form, text=label, bg="#f0f0f0").grid(row=row, column=0, sticky="w")
            e = tk.Entry(form, width=10)
            e.grid(row=row, column=1)
            return e

        self.e_x = add("X Length (mm)", 0)
        self.e_y = add("Y Length (mm)", 1)
        self.e_z = add("Total Depth (mm)", 2)

        self.e_tool = add("Tool Dia (mm)", 3)
        self.e_step = add("Step Down (mm)", 4)
        self.e_stepover = add("Stepover (mm)", 5)

        self.e_wx = add("Work Zero X", 6)
        self.e_wy = add("Work Zero Y", 7)
        self.e_wz = add("Work Zero Z", 8)

        self.e_spindle = add("Spindle RPM", 9)

        tk.Button(
            form,
            text="Generate G-Code",
            width=20,
            command=self.generate_gcode
        ).grid(row=10, column=0, columnspan=2, pady=10)

        # Preview canvas
        self.canvas = tk.Canvas(self, width=500, height=350, bg="white")
        self.canvas.pack(side="right", padx=10, pady=10)

    # -----------------------------------------------------
    def generate_gcode(self):
        try:
            x_len = float(self.e_x.get())
            y_len = float(self.e_y.get())
            depth = float(self.e_z.get())

            tool = float(self.e_tool.get())
            step = float(self.e_step.get())
            stepover = float(self.e_stepover.get())

            wx = float(self.e_wx.get())
            wy = float(self.e_wy.get())
            wz = float(self.e_wz.get())

            rpm = int(float(self.e_spindle.get()))

            if stepover > tool:
                raise ValueError("Stepover must be ≤ tool diameter")

            g = [
                "G21",
                "G90",
                "G17",
                f"G0 Z{SAFE_Z:.1f}",
                f"M3 S{rpm}"
            ]

            depth_now = 0.0
            tool_r = tool / 2

            while depth_now < depth:
                depth_now = min(depth_now + step, depth)
                g.append(f"\n; Depth {depth_now:.2f}")

                sx = q(tool_r + wx)
                sy = q(tool_r + wy)
                g.append(f"G0 X{sx:.1f} Y{sy:.1f}")

                sz = q(-depth_now + wz)
                g.append(f"G1 Z{sz:.1f} F{PLUNGE_FEED}")

                y = tool_r
                direction = 1

                while y <= (y_len - tool_r):
                    if direction == 1:
                        x = x_len - tool_r
                    else:
                        x = tool_r

                    mx = q(x + wx)
                    my = q(y + wy)
                    g.append(f"G1 X{mx:.1f} Y{my:.1f} F{CUT_FEED}")

                    y += stepover
                    direction *= -1

                g.append(f"G0 Z{SAFE_Z:.1f}")

            g += ["M5", "M30"]

            path = filedialog.asksaveasfilename(
                defaultextension=".nc",
                filetypes=[("G-code Files", "*.nc")]
            )

            if path:
                with open(path, "w") as f:
                    f.write("\n".join(g))

                messagebox.showinfo(
                    "Success",
                    "G-code generated successfully\n(mm & mm/min)"
                )

        except Exception as e:
            messagebox.showerror("Error", str(e))