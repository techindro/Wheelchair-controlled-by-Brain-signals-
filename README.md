# NeuroWheel: Brain Signal Controlled Wheelchair

NeuroWheel is an open-source closed-loop Brain-Computer Interface (BCI) wheelchair navigation system. It acquires real-time electroencephalogram (EEG) signals, applies digital signal processing (DSP) filters and machine learning classifiers to decode user intent, and translates mental states into motor and steering commands on an Arduino-driven motorized wheelchair with ultrasonic collision avoidance.

The repository includes embedded C++ firmware, Python signal processing and ML scripts, an emergency watchdog supervisor, and an interactive browser-based simulator with direct Web Serial API hardware control.

![System Architecture](images/bci.png)

---

## System Overview

```
 [ EEG Source (SpikerShield / Emotiv) ]
                  │ (Raw ADC Stream / UDP)
                  ▼
 [ Python DSP: eeg_signal_processor.py ]
    ├── 50 Hz Notch Filter (Mains Hum Removal)
    ├── 0.5–30 Hz Butterworth Bandpass Filter
    ├── Welch PSD Band Power (Delta, Theta, Alpha, Beta)
    └── bci_ml_classifier.py (Random Forest / SVM)
                  │
                  ▼ (Serial / Bluetooth SPP @ 9600 Baud)
 [ Arduino Controller: last_one.ino ]
    ├── L298N Motor Driver ──> 2x 12V DC Motors (Drive)
    ├── MG995 Metal Gear Servo ──> Steering Angle (10° to 110°)
    ├── Dual HC-SR04 Sensors ──> Distance Check (<30 cm = Auto Stop)
    └── 5V Active Buzzer ──> Audio Alarm
                  │
                  ▲ (Web Serial API / USB)
 [ Browser Simulator & Dashboard: index.html ]
```

---

## Signal Processing & Mathematical Formulation

### 1. Digital IIR Filtering (Noise & Artifact Rejection)
Raw EEG signals have low amplitude ($\mu\text{V}$ range) and are susceptible to $50\text{ Hz}$ power-line interference, DC baseline wander, and high-frequency electromyographic (EMG) muscle noise.

- **50 Hz Power-Line IIR Notch Filter:** A second-order notch filter centered at $f_0 = 50\text{ Hz}$ ($Q = 30$) implemented via `scipy.signal.iirnotch`:
  $$H_{\text{notch}}(z) = b_0 \frac{1 - 2\cos(\omega_0)z^{-1} + z^{-2}}{1 - 2r\cos(\omega_0)z^{-1} + r^2 z^{-2}}$$
  where $\omega_0 = \frac{2\pi f_0}{f_s}$ and $r = 1 - \frac{\pi \cdot \text{BW}}{f_s}$.

- **0.5 – 30 Hz Bandpass Filter:** A $4^{\text{th}}$-order zero-phase Butterworth filter implemented via `scipy.signal.butter` and `scipy.signal.filtfilt`:
  $$|H(j\omega)|^2 = \frac{1}{1 + \left(\frac{\omega^2 - \omega_0^2}{\omega \cdot \text{BW}}\right)^{2n}}$$

### 2. Spectral Feature Extraction (Welch's PSD)
Continuous EEG data is processed in sliding windows of $N = 256$ samples ($1.0\text{ s}$ at $f_s = 256\text{ Hz}$, $50\%$ overlap). Power Spectral Density (PSD) is calculated using Welch's method with a Hann window taper $w[n]$:

$$P_{xx}(f) = \frac{1}{K L U} \sum_{k=1}^K \left| \sum_{n=0}^{L-1} x_k[n] w[n] e^{-j 2\pi f n / f_s} \right|^2$$

where $U = \frac{1}{L} \sum_{n=0}^{L-1} |w[n]|^2$ is the window normalization constant.

#### Frequency Band Decomposition & Power Ratios
The absolute band power $E_{\text{band}}$ and relative spectral power $R_{\text{band}}$ are calculated across four canonical bands:

$$E_{\text{band}} = \int_{f_{\text{low}}}^{f_{\text{high}}} P_{xx}(f) df, \quad R_{\text{band}} = \frac{E_{\text{band}}}{\sum_{\text{all bands}} E_i}$$

| Frequency Band | Range (Hz) | Neurological State | Control Mapping |
|:---|:---:|:---|:---|
| **Delta ($\delta$)** | $0.5 - 4.0$ | Deep sleep / baseline rest | Total energy normalizer |
| **Theta ($\theta$)** | $4.0 - 7.0$ | Drowsiness / deep relaxation | High theta triggers drowsiness auto-brake |
| **Alpha ($\alpha$)** | $8.0 - 13.0$ | Relaxed wakefulness (closed eyes) | Alpha dominance ($>60\%$) triggers `STOP` |
| **Beta ($\beta$)** | $14.0 - 30.0$ | Active focus / mental calculation | High $\beta/\alpha$ ratio ($>1.5$) triggers `FORWARD` |

Time-domain statistics (Mean, Standard Deviation, Variance, RMS, Kurtosis, Skewness) are combined with spectral band powers to form a 14-dimensional feature vector $\mathbf{x} \in \mathbb{R}^{14}$.

### 3. Machine Learning Classification
`bci_ml_classifier.py` trains a **Random Forest Classifier** ($100$ estimators, max depth $10$) or **Support Vector Machine (SVM)** to decode 5 discrete states:
- `Class 0 (REST)` $\rightarrow$ Command `'s'` (Idle)
- `Class 1 (FORWARD)` $\rightarrow$ Command `'f'` (Forward drive)
- `Class 2 (LEFT)` $\rightarrow$ Command `'l'` (Steer left)
- `Class 3 (RIGHT)` $\rightarrow$ Command `'r'` (Steer right)
- `Class 4 (BLINK_STOP)` $\rightarrow$ Command `'s'` (Ocular blink spike emergency brake)

---

## Shared Autonomy & Safety Arbitration

To prevent collisions caused by classification errors or delayed user reaction, the firmware applies **Shared Control Arbitration**:

$$\mathbf{u}_{\text{final}} = \alpha \cdot \mathbf{u}_{\text{BCI}} + (1 - \alpha) \cdot \mathbf{u}_{\text{ObstacleAvoidance}}$$

* **Clear Path ($d_{\text{obstacle}} > 60\text{ cm}$):** $\alpha = 1.0$ (Full BCI intent execution).
* **Warning Zone ($30\text{ cm} < d_{\text{obstacle}} \le 60\text{ cm}$):** $\alpha = 0.5$ (Speed clamped to Gear 1, acoustic buzzer sounds).
* **Hazard Zone ($d_{\text{obstacle}} \le 30\text{ cm}$):** $\alpha = 0.0$ (Instant autonomous emergency stop, motors cut off).
* **Watchdog Timeout (2000 ms):** Automatic brake engaged if wireless packets cease while driving.

### Information Transfer Rate (ITR)
System communication throughput is calculated via Wolpaw's Information Transfer Rate:

$$B = \log_2 N + P \log_2 P + (1 - P) \log_2 \left( \frac{1 - P}{N - 1} \right) \quad [\text{bits/trial}]$$

$$\text{ITR} = B \cdot \left(\frac{60}{T}\right) \quad [\text{bits/min}]$$

where $N = 5$ classes, $P = \text{Classification Accuracy}$, and $T = \text{Trial Duration (seconds)}$.

---

## Hardware Specifications & Wiring

<div align="center">
  <img src="images/emotiv.png" width="370" alt="Emotiv EEG Headset" />
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="images/3d_model.jpg" width="370" alt="Wheelchair 3D CAD Assembly" />
</div>

| Component | Model / Part | Arduino Pin Connections & Role |
|:---|:---|:---|
| **EEG Headset** | Emotiv EPOC+ / SpikerShield | 14-channel sensor / 10 kHz ADC sampling via Timer1 interrupts |
| **Microcontroller** | Arduino Mega 2560 / Uno | Master controller running PWM and sensor polling loops |
| **Motor Driver** | L298N Dual H-Bridge | IN1 $\rightarrow$ Pin 5, IN2 $\rightarrow$ Pin 6, IN3 $\rightarrow$ Pin 9, IN4 $\rightarrow$ Pin 10 |
| **Steering Servo** | MG995 Metal Gear Servo | Signal $\rightarrow$ Pin 3 ($10^\circ$ right, $55^\circ$ center, $110^\circ$ left) |
| **Left Ultrasonic** | HC-SR04 | Trig $\rightarrow$ Pin 2, Echo $\rightarrow$ Pin 4 |
| **Right Ultrasonic** | HC-SR04 | Trig $\rightarrow$ Pin 11, Echo $\rightarrow$ Pin 12 |
| **Warning Alarm** | 5V Active Buzzer | Positive $\rightarrow$ Pin 8 |
| **Wireless Module** | HC-05 Bluetooth / USB UART | TX $\rightarrow$ Pin 0, RX $\rightarrow$ Pin 1 (9600 Baud) |
| **Power Supply** | 12V Li-ion Battery | Motor rail (logic grounded with Arduino GND) |

Detailed electrical schematics and pin connection tables are in [CIRCUIT_AND_HARDWARE_GUIDE.md](CIRCUIT_AND_HARDWARE_GUIDE.md).

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
| `2` | Speed Gear 2 | — | Normal standard speed (PWM 180) |
| `3` | Speed Gear 3 | — | Fast outdoor mode (PWM 255) |

---

## Demonstration Media

| Forward & Reverse Drive | Steering Left & Right | Obstacle Avoidance |
|:---:|:---:|:---:|
| ![Forward/Backward](Demo/forward_backward.gif) | ![Steering](Demo/right_left.gif) | ![Avoidance](Demo/avoid.gif) |

---

## Getting Started

### 1. Installation

```bash
git clone https://github.com/techindro/Wheelchair-controlled-by-Brain-signals-.git
cd Wheelchair-controlled-by-Brain-signals-

# Create virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Uploading Arduino Firmware

1. Open `arduino_codes/last_one.ino` in the Arduino IDE.
2. Select your board (**Arduino Mega 2560** or **Arduino Uno**) and COM Port.
3. Click **Upload**.
4. *(Optional for raw EEG ADC streaming)*: Flash `arduino_codes/SpikeRecorder/SpikeRecorder.ino`.

### 3. Running Signal Processing & ML Pipeline

```bash
# 1. Train and evaluate the ML classifier on calibrated EEG epochs:
python socket_communication_codes/bci_ml_classifier.py

# 2. Run real-time DSP processor (auto-detects serial ports or specify flags):
python socket_communication_codes/eeg_signal_processor.py --eeg COM3 --motor COM5

# 3. Or test in simulation mode without hardware attached:
python socket_communication_codes/eeg_signal_processor.py --simulate

# 4. Run emergency SOS telemetry supervisor:
python socket_communication_codes/emergency_sos.py
```

### 4. Interactive Web Simulator & Web Serial Link

To launch the browser simulator:

```bash
python -m http.server 8080
```

Open `http://localhost:8080` in Google Chrome or Microsoft Edge:
- **Direct USB Hardware Control:** Click **"Connect USB Arduino"** to send commands directly to your Arduino over USB via Web Serial API.
- **Autonomous Waypoint Navigation:** Switch to *Autonomous Waypoint* mode and click anywhere on the arena to set navigation targets.
- **Obstacle Radar:** Drag obstacle boxes to test proximity radar in real time.
- **Export Telemetry:** Click **"Export Log"** to save telemetry session records as JSON.

---

## Repository Structure

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
├── images/                           # Circuit schematics, CAD models & hardware photos
├── Demo/                             # Visual GIF recordings of physical testing
├── index.html                        # Web Serial dashboard & 2D physics simulator
├── requirements.txt                  # Python dependencies
├── CIRCUIT_AND_HARDWARE_GUIDE.md     # Wiring pinout guide
├── CONTRIBUTING.md                   # Contribution instructions
├── LICENSE                           # MIT License
└── README.md                         # Project documentation
```

---

## Academic Citation

If you use this system, codebase, or simulator in your research or project, please cite:

```bibtex
@software{patel2026neurowheel,
  author       = {Shubham Patel},
  title        = {NeuroWheel: Closed-Loop Brain-Computer Interface (BCI) Assistive Mobility System},
  year         = {2026},
  publisher    = {GitHub},
  journal      = {GitHub repository},
  howpublished = {\url{https://github.com/techindro/Wheelchair-controlled-by-Brain-signals-}}
}
```

---

## Author

**Shubham Patel**  
Department of Computer Science & Engineering  
GitHub: [@techindro](https://github.com/techindro)

---

## License

This project is licensed under the [MIT License](LICENSE).
