"""
import tkinter as tk
import page_flags

class SettingsPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f0f0f0")
        tk.Label(self, text="SETTINGS",
                 font=("Arial", 16, "bold")).pack(pady=20)
 ##================= PAGE FLAGS =================
    def start_update(self):
        # Set all other page flags to False
        # ✅ Set this page active
        page_flags.settings= True  # <-- change <this_page> to your page's flag, e.g., monitor_active

        # Optionally enable buttons/entries
        self.set_enabled(True)

    def stop_update(self):
        # ✅ Set this page inactive
        page_flags.settings= False  # <-- change <this_page>
        # Optionally disable buttons/entries
        self.set_enabled(False)

    """
import tkinter as tk
from tkinter import messagebox

import page_flags
from fins_comm import write_word   # your real PLC function
from plc_config import MEMORY_AREAS


class SettingsPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f0f0f0")

        # ================= TITLE =================
        tk.Label(self, text="SETTINGS",
                 font=("Arial", 16, "bold")).pack(pady=10)

        # =========================================================
        # 🔴 NEGATIVE VALUE TEST SECTION (TEMP - YOU CAN DELETE LATER)
        # =========================================================

        tk.Label(self, text="Negative Value Test",
                 font=("Arial", 12, "bold"),
                 fg="red").pack(pady=10)

        # Input value
        tk.Label(self, text="Enter Value (can be negative):").pack()
        self.value_entry = tk.Entry(self, width=15)
        self.value_entry.pack(pady=5)

        # DM Address
        tk.Label(self, text="DM Address:").pack()
        self.addr_entry = tk.Entry(self, width=10)
        self.addr_entry.insert(0, "10050")  # default DM10050
        self.addr_entry.pack(pady=5)

        # Send Button
        tk.Button(self,
                  text="Send to PLC",
                  bg="lightgreen",
                  command=self.send_negative_value).pack(pady=10)

    # =========================================================
    # 🔧 FUNCTION: SEND NEGATIVE VALUE TO PLC
    # =========================================================
    def send_negative_value(self):
        try:
            # Get user inputs
            user_value = int(self.value_entry.get())
            address = int(self.addr_entry.get())

            # =================================================
            # 🔑 STEP: Convert to 16-bit (Two's Complement)
            # =================================================
            plc_value = user_value & 0xFFFF

            # =================================================
            # 🔌 SEND TO PLC
            # =================================================

            # ✅ If your function already uses D area internally:
            write_word("D",address, plc_value)

            # ❗ If your function requires memory area, use this instead:
            # write_word(MEMORY_AREAS["D"], address, plc_value)

            # =================================================
            # 📢 SHOW RESULT
            # =================================================
            messagebox.showinfo(
                "Success",
                f"Input Value : {user_value}\n"
                f"PLC Decimal : {plc_value}\n"
                f"PLC HEX     : {plc_value:04X}"
            )

        except ValueError:
            messagebox.showerror("Error", "Enter valid numbers")

    ##================= PAGE FLAGS =================
    def start_update(self):
        page_flags.settings = True
        self.set_enabled(True)

    def stop_update(self):
        page_flags.settings = False
        self.set_enabled(False)