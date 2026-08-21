# 🧠 Brain Signal Controlled Wheelchair (NeuroWheel)

An end-to-end **Brain-Computer Interface (BCI)** assistive mobility system. The project acquires neuro-signals (EEG), processes and classifies brain wave frequency bands in real-time using Digital Signal Processing (DSP) & Machine Learning (ML), and navigates a motorized wheelchair with ultrasonic collision avoidance and emergency safety fail-safes.

---

## 📌 Features & Highlights

- **🧠 Multi-Source EEG Signal Acquisition:** Support for Emotiv EPOC/EPOC+ headsets as well as high-speed raw ADC acquisition via Backyard Brains SpikerShield (`SpikeRecorder.ino`).
- **📊 Real-Time DSP Signal Processing:** 50 Hz IIR Notch filter (mains noise removal) and 0.5–30 Hz Butterworth Bandpass filter with Power Spectral Density (PSD) analysis (`eeg_signal_processor.py`).
- **🤖 BCI Intent Machine Learning Classifier:** Supervised ML classifier (Random Forest & SVM) with Common Spatial Pattern (CSP) / Band Power feature extraction for motor imagery decoding (`bci_ml_classifier.py`).
- **⚡ Brainwave Band Power Extraction:** Real-time extraction of **Delta (0.5–4Hz)**, **Theta (4–7Hz)**, **Alpha (8–13Hz)**, and **Beta (14–30Hz)** ratios for mental focus/intent navigation.
- **🛡️ Autonomous Collision Avoidance:** Dual ultrasonic sensors measure clearance and trigger automatic course correction and acoustic buzzer alarms if obstacles are closer than 30 cm.
- **🚨 Assistive Emergency SOS & GPS Telemetry:** Automatic emergency alert dispatcher for collisions, signal dropouts, and panic triggers with simulated GPS telemetry dispatch (`emergency_sos.py`).
- **🌐 Interactive Web Dashboard & Simulator:** Complete browser-based simulator (`index.html`) featuring:
  - **Direct Web Serial API Link:** Control physical Arduino over USB directly from Google Chrome/Edge!
  - **Autonomous Waypoint Navigation:** Click anywhere on the arena to deploy a target beacon; the wheelchair plans collision-free paths.
  - **Multi-Environment Maps:** Testing Ground, Hospital Corridors, and Slalom Obstacle Track.
  - **Dark / Light Theme Switcher & Telemetry JSON Exporter.**

![System Diagram](images/bci.png)

---

## 🔬 Physical Hardware & Device Specifications

| Component | Real Physical Device / Model | Specifications & Role |
|:---|:---|:---|
| **EEG Headset** | **Emotiv EPOC / EPOC+** | 14-channel neuro-signal sensor (AF3, F7, F3, FC5, T7, P7, O1, O2, P8, T8, FC6, F4, F8, AF4) with wireless receiver |
| **EEG Acquisition Shield** | **Backyard Brains SpikerShield** | 10 kHz high-speed ADC sampling via Timer1 interrupts (`SpikeRecorder.ino`) |
| **Microcontroller** | **Arduino Mega 2560 / Uno** | ATmega-based real-time controller running motor, servo, and safety loops |
| **Motor Driver** | **L298N Dual H-Bridge** | Dual DC motor driver module supporting up to 2A per channel with PWM speed control |
| **Drive Motors** | **12V DC Geared Motors** | High-torque geared motors driving rear wheels for forward/backward movement |
| **Steering Actuator** | **MG995 / MG996R / SG90 Servo** | Metal-gear servo motor controlling front steering wheel angle (10° to 110°) |
| **Obstacle Sensors** | **2x HC-SR04 Ultrasonic** | 40 kHz acoustic transducers measuring distance from 2 cm to 400 cm |
| **Alarm Indicator** | **5V Active Buzzer** | Audio collision alert buzzer connected to Arduino digital Pin 8 |
| **Wireless Module** | **HC-05 Bluetooth Module** | Serial UART Bluetooth SPP module for wireless telemetry communication |
| **Power Supply** | **12V Rechargeable Battery** | 12V Li-ion / Lead-Acid battery powering motors and Arduino logic |

<div align="center">
  <img src="images/emotiv.png" width="380" alt="Emotiv EEG Headset" />
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="images/3d_model.jpg" width="380" alt="Wheelchair 3D CAD Model" />
</div>

---

## 🛠️ Tech Stack & Protocols

- **Firmware & Embedded:** C/C++ (Arduino IDE, AVR Timer Interrupts)
- **Signal Processing & Machine Learning:** Python 3 (`numpy`, `scipy`, `scikit-learn`, `pyserial`, `SpeechRecognition`)
- **Web Simulation & Hardware Bridge:** HTML5, Web Serial API, Canvas 2D API, Web Audio API, Web Speech API
- **Communication Protocols:** 
  - Web Serial (Browser-to-Arduino USB)
  - UDP Sockets (`127.0.0.1:6868`)
  - Serial UART (9600 / 230400 Baud)
  - Bluetooth SPP (HC-05)

---

## 🏛️ System Architecture

```
[ Real Emotiv EEG / SpikerShield ]
               │
               ▼  (Raw Signals / UDP Stream)
[ Python Signal Processor & ML Classifier ]
   ├── 50 Hz Notch + 0.5–30 Hz Bandpass Filtering
   ├── PSD Feature Extraction (Delta / Theta / Alpha / Beta)
   ├── Random Forest / SVM Intent Classifier
   └── Emergency SOS & Safety Dispatcher
               │
               ▼  (Web Serial / HC-05 Bluetooth / Serial 9600 Baud)
[ Physical Arduino Controller ] ──> [ L298N Driver + 12V DC Motors + Servo ]
               ▲
               │  (Echo Ranging Signals & Collision Avoidance)
[ HC-SR04 Ultrasonic Sensors ]
```

---

## 🕹️ Command Reference

| Command | Action | Steering Angle | Speed / Description |
|:---:|:---|:---:|:---|
| `f` | Forward | 55° (Center) | Drives forward at active speed gear |
| `b` | Backward | 55° (Center) | Drives in reverse at active speed gear |
| `l` | Turn Left | 110° (Left) | Steers left and moves forward |
| `r` | Turn Right | 10° (Right) | Steers right and moves forward |
| `s` | Stop / Brake | 55° (Center) | Halts all motor outputs immediately |
| `1` | Gear 1 | — | Slow indoor speed (PWM 120) |
| `2` | Gear 2 | — | Normal standard speed (PWM 180) |
| `3` | Gear 3 | — | High-speed outdoor mode (PWM 255) |

---

## 🎥 Live Demonstrations

### 1. Moving Forward & Backward
![Forward and Backward](Demo/forward_backward.gif)

### 2. Steering Left & Right
![Right and Left](Demo/right_left.gif)

### 3. Autonomous Obstacle Avoidance
![Obstacle Avoidance](Demo/avoid.gif)

---

## 🚀 How to Run

### Option A: Running with Physical Hardware

1. **Hardware Wiring:** Connect components according to [CIRCUIT_AND_HARDWARE_GUIDE.md](CIRCUIT_AND_HARDWARE_GUIDE.md) and [EEG Circuit Diagram](images/eeg_circuit_diagram.png).
2. **Flash Arduino Controller:**
   - Open `arduino_codes/last_one.ino` in Arduino IDE, select your COM port, and upload.
   - *(Optional for Raw ADC)*: Open `arduino_codes/SpikeRecorder/SpikeRecorder.ino` for 10 kHz raw signal streaming.
3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Start Python Signal Processor & ML Classifier:**
   ```bash
   # Run ML intent classification pipeline:
   python socket_communication_codes/bci_ml_classifier.py

   # Run DSP signal filtering & classification:
   python "socket_communication_codes/eeg_signal_processor.py" --eeg COM3 --motor COM5

   # Or run standard serial/UDP bridge:
   python "socket_communication_codes/serial communication.py"
   ```

---

### Option B: Running the Web Simulator & Direct Web Serial Control

Test the entire system in your browser with interactive 2D physics, autonomous waypoint navigation, and live EEG waveforms:

```bash
# Start local web server
python -m http.server 8080
```

Open **`http://localhost:8080`** in your browser:
- **Direct USB Hardware Connection:** Click **"Connect USB Arduino"** to send commands directly to your physical wheelchair over Web Serial API.
- **Autonomous Navigation:** Switch mode to **"🎯 Autonomous Waypoint"** and click anywhere on the arena to set navigation targets.
- **Controls:** `W` / `A` / `S` / `D` or **Arrow Keys**
- **Emergency Brake:** `Spacebar`
- **Gears:** Keys `1`, `2`, `3`
- **Obstacle Radar:** Drag obstacle boxes anywhere to test collision avoidance radar.
- **Telemetry Export:** Click **"Export Log"** to download JSON telemetry session records.

---

## 📂 Repository Structure

```
Wheelchair-controlled-by-Brain-signals-/
├── .github/workflows/
│   └── deploy.yml                         # CI pipeline & GitHub Pages auto-deploy
├── arduino_codes/
│   ├── last_one.ino                       # Main Arduino controller (motors + servo + ultrasonic)
│   ├── SpikeRecorder/
│   │   └── SpikeRecorder.ino              # 10kHz ADC raw EEG acquisition firmware
│   ├── _2_ultrasonic/                     # Ultrasonic test routines
│   └── _2ultrasonis_servo_DC-v2/          # Motor & servo calibration sketches
├── socket_communication_codes/
│   ├── bci_ml_classifier.py               # Supervised ML motor imagery intent classifier
│   ├── eeg_signal_processor.py            # Notch/Bandpass filtering & PSD classification
│   ├── emergency_sos.py                   # Safety monitoring & GPS emergency SOS dispatcher
│   └── serial communication.py            # Serial-to-UDP socket bridge with voice listener
├── images/
│   ├── bci.png                            # BCI system flowchart
│   ├── emotiv.png                         # Emotiv headset reference
│   ├── 3d_model.jpg                       # 3D CAD wheelchair model
│   ├── eeg_circuit_diagram.png            # Detailed circuit wiring diagram
│   ├── wheelchair_topdown.jpg             # High-res wheelchair sprite
│   └── obstacle_topdown.jpg               # Traffic cone obstacle sprite
├── Demo/
│   ├── forward_backward.gif               # Drive test demo
│   ├── right_left.gif                     # Steering test demo
│   └── avoid.gif                          # Collision avoidance demo
├── index.html                             # NeuroWheel interactive Web Simulator & Dashboard
├── requirements.txt                       # Python dependencies list
├── CIRCUIT_AND_HARDWARE_GUIDE.md          # Pinout & connection documentation
├── CONTRIBUTING.md                        # Contribution guidelines
├── LICENSE                                # MIT License
└── README.md                              # Project documentation
```

---

## 🛡️ Safety Systems

- **Watchdog Auto-Brake (2000 ms):** Automatically stops motors if Bluetooth/Serial telemetry drops while in motion.
- **Acoustic Warning Alarm:** 5V active buzzer sounds continuously when front obstacles are within 30 cm.
- **Autonomous Evasion:** Arduino automatically overrides steering to navigate around detected barriers.
- **Emergency SOS Dispatcher:** Real-time collision impact and signal loss detection with automated GPS telemetry broadcasting.

---

## 👤 Author

**Shubham Patel**  
B.Tech Computer Science & Engineering  
GitHub: [@techindro](https://github.com/techindro)

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
