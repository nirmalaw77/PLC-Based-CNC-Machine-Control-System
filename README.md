# PLC-Based CNC Machine Control System

<p align="center">
  <h2 align="center">PLC-Based CNC Machine Control System</h2>
  <p align="center">
    Development of a multi-axis CNC machine control system using an Omron CP2E PLC
  </p>
</p>

---

## 📌 Overview

This project involved the development of a **PLC-based CNC Machine Control System** using an **Omron CP2E PLC**.

The system was initially developed as a **2-axis CNC control system** and was later upgraded to a **3-axis motion control system**.

The project involved the integration of PLC programming, motion control, CNC programming, industrial communication, and a Python-based Human Machine Interface (HMI).

---

## ⚙️ System Features

- 2-axis CNC motion control
- Upgrade to 3-axis motion control
- Stepper motor control
- Target frequency control
- Acceleration and deceleration control
- Absolute positioning
- Relative positioning
- Linear interpolation
- Homing / origin search
- Positive and negative limit monitoring
- Emergency push-button monitoring
- Automatic CNC cycle control
- G-code parsing
- Automatic CNC machining functions
- Real-time machine monitoring
- Python-based HMI
- PLC-PC communication using FINS/TCP

---

## 🧠 PLC Control

The CNC machine control system was developed using an **Omron CP2E PLC** and programmed using **Omron CX-Programmer**.

The PLC was responsible for:

- Motion control
- Positioning
- Motor control
- Homing sequences
- Limit monitoring
- Automatic machining sequences
- CNC data handling
- Machine safety and control logic

---

## 🖥️ Python HMI

A Python-based Human Machine Interface (HMI) was developed to provide a PC-based interface for controlling and monitoring the CNC machine.

The HMI was used for:

- Machine initialization
- Manual axis control
- Position control
- Sensor monitoring
- Machine status monitoring
- Communication with the PLC

---

## 🔌 PLC–PC Communication

Communication between the Python application and the Omron CP2E PLC was implemented using the **Omron FINS/TCP industrial communication protocol**.

The Python application was designed to read and write PLC memory areas and exchange control and monitoring data with the PLC.

---

## 📐 CNC Motion Control

The motion-control system supports both **absolute and relative positioning**.

**Linear interpolation** was also implemented to coordinate the movement of multiple axes during CNC operations.

Motor motion parameters such as **target frequency and acceleration/deceleration** were configured as part of the motion-control system.

---

## 🔄 Development Progression

The system was developed in stages:

### Stage 1 — 2-Axis CNC Control

Development and testing of the initial 2-axis CNC control system.

### Stage 2 — 3-Axis Upgrade

The completed 2-axis system was subsequently expanded to support **3-axis motion control**.

### Stage 3 — CNC Programming

CNC functions were developed, including positioning, motion sequences, and automatic machining functions.

### Stage 4 — Python HMI

A Python-based HMI was developed for machine control and monitoring.

### Stage 5 — G-Code Processing

G-code parsing and implementation of automatic CNC machining functions were developed and tested.

---

## 🛠️ Technologies Used

| Category | Technology |
|---|---|
| PLC | Omron CP2E |
| PLC Programming | CX-Programmer |
| Programming | Python |
| Communication | Omron FINS/TCP |
| Motion Control | Multi-axis Stepper Motor Control |
| CNC | G-code |
| HMI | Python-based HMI |

---

## 📷 Project Documentation

Project photographs, development documentation, PLC programs, and related technical material are available in the corresponding folders of this repository.

---

## 📚 Learning & Development

This project provided practical experience in integrating **mechanical systems, PLC programming, CNC motion control, industrial communication, and software development** into a single machine-control system.

It also provided an opportunity to apply concepts learned through university coursework to practical engineering problems.

---

## 👨‍💻 Project Experience

**Flexline Technologies (Pvt) Ltd**

Industrial Training / Project Experience

The project involved the development, testing, debugging, and optimization of the PLC-based CNC machine control system.

---

## ⚠️ Note

This repository is intended to document the project, technical learning, and development experience. Certain proprietary or confidential information may be omitted.
