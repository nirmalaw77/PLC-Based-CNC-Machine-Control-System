import tkinter as tk
import page_flags   # ✅ add this


# ================== SINGLE SOURCE OF TRUTH ==================

SENSOR_GROUPS = {
    "AXIS A0": [
        ("NEL",  ("CIO", 0, 5)),
        ("HOME", ("CIO", 0, 6)),
        ("PEL",  ("CIO", 0, 3)),
    ],
    "AXIS A1": [
        ("NEL",  ("CIO", 0, 9)),
        ("HOME", ("CIO", 0, 7)),
        ("PEL",  ("CIO", 0, 8)),
    ]
}

MONITOR_CONFIG = [
    ("D146",     "D",   146, None),
    ("D600",     "D",   601, None),
    ("D601",     "D",   602, None),

    ("D148",     "D",   148, None),
    ("A0 PRV",   "D",   220, None),
    ("A1 PRV",   "D",   230, None),
    ("MASTER HOME", "W", 8, 0),
    ("A0 HOMED", "W", 100, 0),
    ("A1 HOMED", "W", 101, 0),
    ("A2 HOMED", "W", 102, 0)
]

SMOOTHING_ALPHA = 0.2


class MonitorPage(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg="#f0f0f0")

        tk.Label(
            self,
            text="I/O MONITOR",
            font=("Arial", 16, "bold"),
            bg="#f0f0f0"
        ).pack(pady=10)

        body = tk.Frame(self, bg="#f0f0f0")
        body.pack(fill="both", expand=True, padx=10)


        # ---------- SENSOR LAMPS ----------
        left = tk.LabelFrame(body, text="Sensors", padx=20, pady=20)
        left.pack(side="left", fill="y", padx=10)

        self.lamps = {}

        for axis, sensors in SENSOR_GROUPS.items():

            af = tk.LabelFrame(left, text=axis, padx=15, pady=10)
            af.pack(pady=10)

            for name, key in sensors:

                row = tk.Frame(af)
                row.pack(pady=4)

                c = tk.Canvas(row, width=18, height=18)

                o = c.create_oval(2, 2, 16, 16, fill="red")

                c.pack(side="left", padx=6)

                tk.Label(row, text=name, width=6).pack(side="left")

                self.lamps[key] = (c, o)


        # ---------- MEMORY VALUES ----------
        right = tk.LabelFrame(body, text="Memory", padx=20, pady=20)
        right.pack(side="left", fill="both", expand=True, padx=10)

        self.labels = {}

        for name, area, word, bit in MONITOR_CONFIG:

            row = tk.Frame(right)
            row.pack(fill="x", pady=2)

            tk.Label(row, text=name, width=20).pack(side="left")
            tk.Label(row, text=f"{area}{word}", width=10).pack(side="left")

            v = tk.Label(row, text="---", width=10)

            v.pack(side="left")

            self.labels[(area, word, bit)] = v


        # ---------- HOMED STATUS ----------
        homed = tk.LabelFrame(body, text="Homed Status", padx=25, pady=25)
        homed.pack(side="right", fill="y", padx=15)

        self.homed_lamps = {}

        for axis, key in [

            ("A0", ("W", 100, 0)),
            ("A1", ("W", 101, 0)),
            ("A2", ("W", 102, 0))

        ]:

            row = tk.Frame(homed)
            row.pack(pady=15)

            c = tk.Canvas(row, width=28, height=28)

            o = c.create_oval(4, 4, 24, 24, fill="red")

            c.pack(side="left", padx=10)

            lbl = tk.Label(
                row,
                text=f"{axis} NOT HOMED",
                font=("Arial", 11, "bold")
            )

            lbl.pack(side="left")

            self.homed_lamps[key] = (c, o, lbl)


        self.smoothed = {}


    # ================= PAGE FLAGS =================

    def start_update(self):

        page_flags.monitor_active = True


    def stop_update(self):

        page_flags.monitor_active = False


    def get_monitor_config(self):

        return MONITOR_CONFIG


    def update_values(self, plc_values):

        if not page_flags.monitor_active:
            return


        for key, (c, o) in self.lamps.items():

            if plc_values.get(key, 0):

                c.itemconfig(o, fill="green")

            else:

                c.itemconfig(o, fill="red")


        for k, lbl in self.labels.items():

            if k in plc_values:

                value = plc_values[k]


                if k == ("D", 220, None) or k == ("D", 230, None):

                    old = self.smoothed.get(k, value)

                    new = old + SMOOTHING_ALPHA * (value - old)

                    self.smoothed[k] = new

                    lbl.config(text=str(int(new)))

                else:

                    lbl.config(text=str(value))


        for key, (c, o, lbl) in self.homed_lamps.items():

            if plc_values.get(key, 0):

                c.itemconfig(o, fill="green")

                lbl.config(text=f"{lbl.cget('text').split()[0]} HOMED")

            else:

                c.itemconfig(o, fill="red")

                lbl.config(text=f"{lbl.cget('text').split()[0]} NOT HOMED")


    def clear_values(self):

        for lbl in self.labels.values():

            lbl.config(text="---")

        for c, o in self.lamps.values():

            c.itemconfig(o, fill="red")

        for c, o, lbl in self.homed_lamps.values():

            c.itemconfig(o, fill="red")

            lbl.config(text=lbl.cget("text").split()[0] + " NOT HOMED")