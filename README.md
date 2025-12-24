# Traction-Control-System-Simulation-Python-OPC-UA-PLCNext-Engineer-Phoenix-Contact
PLC &amp; Python Digital Twin: Traction Control System (TCS)  Secure Digital Twin simulation connecting PLCnext (OT) and Python (IT) via OPC UA. Features a real-time Traction Control System (TCS) that monitors wheel slip on simulated icy roads, using Newtonian physics and encrypted industrial communication.


🚀 Project Overview

The system consists of two main components:

PLC (The Brain): A PLCnext controller programmed in Structured Text (ST). It handles the control logic, monitors wheel slip, and manages the TCS intervention.

Python (The Physics Engine): A simulation script that acts as the physical vehicle and environment. It calculates real-world physics like air drag, inertia, and road friction.

The two systems communicate in real-time over a secure OPC UA bridge.



🛠️ Tech Stack

Hardware/PLC: Phoenix Contact PLCnext (or PLCnext Engineer Simulator)

Language (PLC): IEC 61131-3 Structured Text (ST)

Language (Simulation): Python 3.9+

Communication: OPC UA (Binary Protocol)

Security: X.509 Certificates (OpenSSL), Sign & Encrypt (Basic256Sha256)

Tools: UaExpert (Monitoring), PLCnext Engineer (IDE)



🏗️ System Architecture

Driver Input: User sets Gas, Brake, and Road Conditions (Dry/Wet/Ice) via the HMI.

Control Loop: PLC calculates the target torque.

Python receives torque via OPC UA, applies physics (Drag, Friction, Inertia), and calculates speeds.

Python writes Vehicle Speed and Wheel Speed back to the PLC.

TCS Intervention: If the PLC detects a significant difference between wheel and vehicle speed (Slip), it automatically reduces motor torque to restore grip.



💻 Code Explanations


PLC Logic (Structured Text)

The PLC code manages the Latching Start/Stop logic and the TCS Algorithm:

Slip Detection: SlipError := WheelSpeed - VehicleSpeed;

Proportional Control: Uses a Gain factor (Kp) to determine the intensity of torque reduction.

Safety: Ensures motor torque never drops below zero or exceeds driver demand.


Python Simulation

The Python script is the "Physical World":

Aerodynamic Drag: Resistance increases with the square of the speed ($v^2$).

Friction Model: Simulates "spinning wheels" on ice by decoupling wheel speed from vehicle speed based on a friction coefficient.

Secure Client: Implements a secure OPC UA client that handles encrypted handshakes with the PLC.



🔑 Security Setup

Industrial systems require high security. This project uses:

Sign & Encrypt: All data packets are digitally signed and encrypted.

Certificates: Requires .der and .pem certificates generated via OpenSSL to establish trust between the Python Client and PLC Server.



⚙️ Installation & Setup


PLC Side:

Import the project into PLCnext Engineer.

Enable the OPC UA Server and mark tags (Gas, Brake, Speed, etc.) with the OPC flag.

Set up a user with "Initial Trust" or upload the Python client certificate.


Python Side:

Install dependencies: pip install opcua cryptography

Generate your certificates using OpenSSL.

Update PLC_URL in plc.py if necessary.

Run: python plc.py



📊 Results

Dry Road: Perfect grip, wheel speed equals vehicle speed.

Icy Road: High wheel spin detected; PLC reduces torque until speeds align.

High Speed: Air drag naturally limits the vehicle's top speed to 180 km/h, simulating realistic engine load.


<img width="841" height="630" alt="Ekran görüntüsü 2025-12-23 162723" src="https://github.com/user-attachments/assets/dc7c44cd-5495-4aa9-b615-9950f50256cd" />


Developed for Educational & Simulation Purposes.
