# Circuit and Hardware Connection Guide

**Project:** Brain Signal Controlled Wheelchair  
**Author:** Shubham Patel (B.Tech CSE)  

---

This guide describes wiring connections between the Arduino, Motor Driver, Sensors, Buzzer, and Bluetooth Module.

---

## Pinout and Connections

### 1. Ultrasonic Distance Sensors (HC-SR04)
| Sensor | Sensor Pin | Arduino Pin | Description |
|:---|:---|:---|:---|
| **Front Sensor** | `VCC` | `5V` | Power supply |
| | `GND` | `GND` | Ground |
| | `TRIG` | `Pin 22` | Trigger output |
| | `ECHO` | `Pin 23` | Echo input |
| **Right Sensor** | `SIG / TRIG+ECHO` | `Pin 7` | Ultrasonic Single-Pin Ranger |
| **Left Sensor (Optional)** | `TRIG` | `Pin 24` | Left Trigger |
| | `ECHO` | `Pin 25` | Left Echo |

---

### 2. Motor Driver (L298N) and DC Motors
| L298N Pin | Arduino Pin | Function |
|:---|:---|:---|
| `IN1` | `Pin 13` | Forward direction |
| `IN2` | `Pin 12` | Backward direction |
| `ENA` (Speed PWM) | `Pin 11` | PWM Speed Control (0-255) |
| `+12V` | Battery `+12V` | Motor power supply |
| `GND` | Battery `GND` & Arduino `GND` | Common ground (mandatory) |
| `+5V` | Arduino `5V` | Logic power |

---

### 3. Steering Servo Motor (MG995 / MG996R / SG90)
| Servo Wire | Connection | Description |
|:---|:---|:---|
| **Signal (Yellow/Orange)** | Arduino `Pin 9` | PWM Steering Signal |
| **VCC (Red)** | `5V - 6V` (External Battery/BEC) | Power supply |
| **GND (Brown/Black)** | Arduino `GND` & Battery `GND` | Common ground |

---

### 4. Buzzer
| Component | Pin | Arduino Pin | Description |
|:---|:---|:---|:---|
| **Active 5V Buzzer** | `(+)` | `Pin 8` | Collision warning alarm |
| | `(-)` | `GND` | Common ground |

---

### 5. Bluetooth Module (HC-05 / HC-06)
| HC-05 Pin | Arduino Pin | Description |
|:---|:---|:---|
| `VCC` | `5V` | Power |
| `GND` | `GND` | Ground |
| `TXD` | Arduino `RX (Pin 0)` | Data from PC/Phone to Arduino |
| `RXD` | Arduino `TX (Pin 1)` | Data from Arduino to PC |

---

## Command Reference

| Command | Action | Description |
|:---:|:---|:---|
| `f` | Forward | Drives forward at active speed |
| `b` | Backward | Reverses at active speed |
| `l` | Turn Left | Steers left (110°) and turns |
| `r` | Turn Right | Steers right (10°) and turns |
| `s` | Stop | Halts all motors |
| `1` | Gear 1 | Slow indoor speed (PWM 120) |
| `2` | Gear 2 | Normal speed (PWM 180) |
| `3` | Gear 3 | Fast outdoor speed (PWM 255) |

---

## Safety Watchdog
- **Auto-Brake Timeout (2000 ms):** If Bluetooth communication drops while moving, the microcontroller automatically halts the motors.
- **Obstacle Alert:** Buzzer sounds when obstacle distance is less than 30 cm.
