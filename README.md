# PLC-Based CNC Machine Control System

<p align="center">
  <img src="YOUR_MAIN_CNC_IMAGE_HERE" width="650">
</p>

## About the Project

This project was developed during my time at **Flexline Technologies (Pvt) Ltd**, where I had the opportunity to work on a PLC-based CNC machine control system.

I started by developing a **2-axis CNC control system** and, after completing and testing it, upgraded the system to support **3-axis motion control**.

What made this project particularly interesting for me was that it brought together several areas I had been learning as a Mechanical Engineering student — mechanical motion, PLC programming, CNC control, programming, and industrial communication — into one working system.

---

## What I Worked On

My work on the project involved several stages of developing and improving the CNC controller.

### ⚙️ Motion Control

I worked on controlling the stepper motors and implementing the required motion-control functions, including:

* Target frequency / speed control
* Acceleration and deceleration
* Absolute positioning
* Relative positioning
* Linear interpolation
* Homing / origin search
* Positive and negative limit monitoring

The system was first developed for **2-axis motion** and was later expanded to **3-axis motion**.

### 🧠 PLC Programming

The machine-control logic was developed using an **Omron CP2E PLC** and **CX-Programmer**.

The PLC handled functions such as:

* Axis motion
* Positioning
* Homing
* Limit monitoring
* Automatic sequences
* CNC data handling
* Machine-control logic

### 💻 Python HMI

I also developed a **Python-based HMI** to provide a PC interface for controlling and monitoring the machine.

The interface allowed communication with the PLC and provided functions such as:

* Machine initialization
* Manual axis movement
* Position control
* Sensor monitoring
* Machine status monitoring

### 🔌 PLC–PC Communication

The Python application communicated with the Omron CP2E PLC using the **FINS/TCP protocol**.

This allowed the PC application to read and write PLC data and interact with the machine-control system in real time.

### 📄 CNC & G-Code

Another part of the project involved developing CNC-related functions, including **G-code parsing** and automatic machining sequences.

This allowed the controller to interpret CNC instructions and translate them into the required machine movements.

---

## Development Journey

One of the most rewarding parts of the project was seeing the system grow step by step.

**2-Axis CNC → 3-Axis CNC → Motion Control → Python HMI → G-Code Processing**

Each stage required testing, troubleshooting, and making improvements before moving on to the next stage.

This process helped me understand that developing a machine-control system isn't just about writing code — it also involves understanding the machine, identifying problems, testing solutions, and making sure the different parts of the system work together reliably.

---

## System Overview

The overall system can be viewed as:

**Python HMI → FINS/TCP → Omron CP2E PLC → Motion Control → Stepper Motors → CNC Machine**

More detailed documentation and development material can be found in the folders in this repository.

---

## Technologies & Tools

* **Omron CP2E PLC**
* **Omron CX-Programmer**
* **Python**
* **FINS/TCP**
* **Stepper Motors**
* **CNC Motion Control**
* **G-code**
* **Python-based HMI**

---

## University Knowledge Applied

One of the interesting aspects of this experience was seeing how concepts learned at university could become useful in practical engineering work.

For example, the **indirect addressing concepts I had learned in C++** during the previous semester came in handy while working on the CNC programming within the PLC.

It was a good reminder that concepts learned in one area can sometimes become useful in completely different engineering applications.


---

## About My Contribution

My involvement focused on the development and implementation of the CNC control system, including PLC programming, motion control, CNC functionality, Python-based machine interfacing, and PLC–PC communication.

Working on this project gave me valuable practical experience in **industrial automation, CNC systems, motion control, PLC programming, and software integration**.

---

## Acknowledgement

I would like to thank **Flexline Technologies (Pvt) Ltd** for giving me the opportunity to work on this project and gain practical experience in industrial automation and machine-control systems.
