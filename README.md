# NeuroWheel: Brain Signal Controlled Wheelchair

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Arduino C++](https://img.shields.io/badge/Platform-Arduino%20C%2B%2B-00979D.svg)](https://www.arduino.cc)
[![scikit-learn](https://img.shields.io/badge/ML-scikit--learn-orange.svg)](https://scikit-learn.org)

NeuroWheel is an open-source brain-computer interface (BCI) wheelchair system. It acquires real-time EEG signals, processes them using digital signal processing (DSP) filters and machine learning classifiers, and sends motor/steering commands to an Arduino-driven wheelchair base with ultrasonic collision detection.

The repository includes firmware, signal processing scripts, an ML intent classifier, and a browser-based simulator with Web Serial API support for testing with or without physical hardware.

---

## System Overview

```
 [ EEG Source (SpikerShield / Emotiv) ]
                  │ (Raw ADC Stream / UDP)
                  ▼
 [ Python DSP: eeg_signal_processor.py ]
    ├── 50 Hz Notch Filter (Noise Rejection)
    ├── 0.5–30 Hz Butterworth Bandpass Filter
    ├── Welch PSD Band Power (Delta, Theta, Alpha, Beta)
    └── bci_ml_classifier.py (Random Forest / SVM)
                  │
                  ▼ (Serial / Bluetooth SPP @ 9600 Baud)
 [ Arduino Controller: last_one.ino ]
    ├── L298N Motor Driver ──> 2x 12V DC Motors (Drive)
    ├── MG995 Metal Gear Servo ──> Steering Angle
    ├── Dual HC-SR04 Sensors ──> Distance Check (<30 cm = Auto Stop)
    └── 5V Active Buzzer ──> Audio Alarm
                  │
                  ▲ (Web Serial API / USB)
 [ Browser Simulator / Dashboard: index.html ]
```

---

## Key Components

### 1. Signal Acquisition & Filtering
- **Input Sources:** Backyard Brains SpikerShield (10 kHz Timer1 ADC sampling via `SpikeRecorder.ino`) or Emotiv EPOC/EPOC+ headsets.
- **Mains Hum Removal:** 2nd-order IIR Notch filter centered at 50 Hz ($Q = 30$) to suppress power-line noise.
- **Bandpass Filtering:** 4th-order zero-phase Butterworth filter passing 0.5 Hz to 30 Hz to isolate relevant brain rhythms while cutting off high-frequency EMG artifacts.

### 2. Feature Extraction & Classification
- **Feature Extraction:** Computes Welch's Power Spectral Density (PSD) using 1-second sliding windows (256 samples @ 256 Hz with 50% overlap).
- **Frequency Bands Extracted:**
  - **Delta (0.5–4 Hz):** Baseline / low arousal
  - **Theta (4–7 Hz):** Drowsiness monitoring
  - **Alpha (8–13 Hz):** Relaxed state (Alpha dominance triggers stop)
  - **Beta (14–30 Hz):** Focus / mental activity (High $\beta/\alpha$ ratio triggers forward movement)
- **Time-Domain Metrics:** Mean, standard deviation, variance, RMS, kurtosis, and skewness.
- **Classifier (`bci_ml_classifier.py`):** Trains a Random Forest / SVM classifier to output one of five discrete states:
  - `REST` (`'s'`) — Idle state
  - `FORWARD` (`'f'`) — Forward driving
  - `LEFT` (`'l'`) — Left turn
  - `RIGHT` (`'r'`) — Right turn
  - `BLINK_STOP` (`'s'`) — High-amplitude ocular blink for emergency halt

### 3. Hardware & Embedded Controller
- **Microcontroller:** Arduino Mega 2560 or Arduino Uno.
- **Drive Motors:** Two 12V DC geared motors driven by an L298N dual H-Bridge.
- **Steering:** MG995 / MG996R servo attached to the front steering linkage ($10^\circ$ to $110^\circ$, center at $55^\circ$).
- **Obstacle Avoidance:** Two HC-SR04 ultrasonic sensors mounted on the front bumper. If any obstacle is closer than 30 cm, the Arduino automatically cuts motor power and sounds the buzzer.
- **Watchdog Timer:** If serial packets stop arriving for more than 2 seconds during active motion, the controller stops the motors automatically.

---

## Hardware Specifications & Wiring

| Component | Model / Part | Arduino Pin Connections |
|:---|:---|:---|
| **Microcontroller** | Arduino Mega 2560 / Uno | — |
| **Motor Driver (L298N)** | Dual H-Bridge Module | IN1 $\rightarrow$ Pin 5, IN2 $\rightarrow$ Pin 6, IN3 $\rightarrow$ Pin 9, IN4 $\rightarrow$ Pin 10 |
| **Steering Servo** | MG995 Metal Gear Servo | Signal $\rightarrow$ Pin 3 |
| **Left Ultrasonic Sensor** | HC-SR04 | Trig $\rightarrow$ Pin 2, Echo $\rightarrow$ Pin 4 |
| **Right Ultrasonic Sensor** | HC-SR04 | Trig $\rightarrow$ Pin 11, Echo $\rightarrow$ Pin 12 |
| **Alarm Buzzer** | 5V Active Buzzer | Positive $\rightarrow$ Pin 8 |
| **Bluetooth Module** | HC-05 (UART) | TX $\rightarrow$ RX (Pin 0 / Serial1), RX $\rightarrow$ TX (Pin 1 / Serial1) |
| **Power Supply** | 12V Li-ion Battery | Motor rail (logic grounded with Arduino GND) |

Detailed pinout schematics and circuit diagrams are available in [CIRCUIT_AND_HARDWARE_GUIDE.md](CIRCUIT_AND_HARDWARE_GUIDE.md).

---

## Command Reference

| Character | Command | Steering Servo | Motor State |
|:---:|:---|:---:|:---|
| `f` | Forward | $55^\circ$ (Center) | Both motors drive forward |
| `b` | Backward | $55^\circ$ (Center) | Both motors drive in reverse |
| `l` | Turn Left | $110^\circ$ (Left) | Front wheels steer left, motors drive forward |
| `r` | Turn Right | $10^\circ$ (Right) | Front wheels steer right, motors drive forward |
| `s` | Stop / Brake | $55^\circ$ (Center) | Motors turned off immediately |
| `1` | Speed Gear 1 | — | Slow indoor speed (PWM 120) |
| `2` | Speed Gear 2 | — | Normal speed (PWM 180) |
| `3` | Speed Gear 3 | — | Fast mode (PWM 255) |

---

## Getting Started

### 1. Prerequisites & Installation

Clone the repository and install the Python dependencies:

```bash
git clone https://github.com/techindro/Wheelchair-controlled-by-Brain-signals-.git
cd Wheelchair-controlled-by-Brain-signals-

# Create virtual environment (optional but recommended)
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Uploading Arduino Firmware

1. Connect your Arduino board via USB.
2. Open `arduino_codes/last_one.ino` in the Arduino IDE.
3. Select your board (`Arduino Mega 2560` or `Arduino Uno`) and COM Port.
4. Click **Upload**.

### 3. Running Signal Processing & ML Pipeline

```bash
# 1. Train and evaluate the ML classifier on calibrated EEG epochs
python socket_communication_codes/bci_ml_classifier.py

# 2. Run real-time DSP processor (auto-detects serial ports or specify flags)
python socket_communication_codes/eeg_signal_processor.py --eeg COM3 --motor COM5

# 3. Or test in simulation mode without hardware attached
python socket_communication_codes/eeg_signal_processor.py --simulate

# 4. (Optional) Run the emergency SOS telemetry supervisor
python socket_communication_codes/emergency_sos.py
```

### 4. Interactive Web Simulator & Web Serial Link

To run the browser simulator:

```bash
python -m http.server 8080
```

Open `http://localhost:8080` in Chrome or Edge:
- **Direct Hardware Control:** Click **"Connect USB Arduino"** to send commands directly to your Arduino over USB via Web Serial API.
- **Autonomous Waypoints:** Switch to *Autonomous Waypoint* mode and click anywhere on the arena to set navigation targets.
- **Collision Testing:** Drag obstacles around to test raycasted proximity detection.
- **Export Data:** Click **"Export Log"** to save telemetry session logs in JSON format.

---

## File Structure

```
Wheelchair-controlled-by-Brain-signals-/
├── arduino_codes/
│   ├── last_one.ino                  # Main Arduino firmware (motors, servo, ultrasonics)
│   ├── SpikeRecorder/                # 10 kHz ADC sampling sketch
│   ├── _2_ultrasonic/                # Ultrasonic sensor test sketch
│   └── _2ultrasonis_servo_DC-v2/     # Motor and servo calibration sketch
├── socket_communication_codes/
│   ├── bci_ml_classifier.py          # Intent classifier (PSD, Random Forest, SVM)
│   ├── eeg_signal_processor.py       # DSP notch/bandpass filters & serial streaming
│   ├── emergency_sos.py              # Collision & signal loss watcher with alert log
│   └── serial communication.py       # Serial/UDP bridge with voice recognition fallback
├── images/                           # Circuit schematics and hardware photos
├── Demo/                             # Visual GIF recordings of physical testing
├── index.html                        # Web Serial dashboard & 2D physics simulator
├── requirements.txt                  # Python dependencies
├── CIRCUIT_AND_HARDWARE_GUIDE.md     # Wiring pinout guide
├── CONTRIBUTING.md                   # Contribution instructions
├── LICENSE                           # MIT License
└── README.md                         # Project documentation
```

---

## Demos

| Forward & Reverse Drive | Steering Left & Right | Obstacle Avoidance |
|:---:|:---:|:---:|
| ![Forward/Backward](Demo/forward_backward.gif) | ![Steering](Demo/right_left.gif) | ![Avoidance](Demo/avoid.gif) |

---

## Roadmap & Future Enhancements

- [ ] Implement spatial filtering via Common Spatial Patterns (CSP) for multi-channel arrays.
- [ ] Evaluate subject-independent decoding on the PhysioNet BCI2000 benchmark dataset.
- [ ] Upgrade navigation controller to ROS 2 (Nav2) with 2D LiDAR SLAM for map-based path planning.
- [ ] Add real-time Artifact Subspace Reconstruction (ASR) to reduce movement artifacts during drive phases.

---

## Author

**Shubham Patel**  
Department of Computer Science & Engineering  
GitHub: [@techindro](https://github.com/techindro)

---

## License

This project is licensed under the [MIT License](LICENSE).
