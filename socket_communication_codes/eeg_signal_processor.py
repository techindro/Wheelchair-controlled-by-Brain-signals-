"""
EEG Signal Processor & Command Classifier
==========================================
Adapted from megazron/eeg-operated-wheelchair (raspberry-pi-prog.py)
Original processing by Backyard Brains, https://backyardbrains.com/

This script:
  1. Reads raw EEG data from a serial port (Backyard Brains SpikerShield / SpikeRecorder)
  2. Applies 50 Hz notch filter (power line noise removal)
  3. Applies 0.5-30 Hz bandpass filter (isolate EEG bands)
  4. Extracts PSD features for Alpha, Beta, Theta, Delta bands
  5. Classifies mental state -> wheelchair command
  6. Sends command to Arduino over Serial / Bluetooth

Usage:
  python eeg_signal_processor.py                           # Auto-detect ports
  python eeg_signal_processor.py --eeg COM3 --motor COM5   # Specify ports
  python eeg_signal_processor.py --simulate                # Simulation mode (no hardware)
"""

import serial
import serial.tools.list_ports
import numpy as np
from scipy import signal as sig
import time
import argparse
import sys
from collections import deque

# ──────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────
SAMPLING_RATE = 256        # Hz (adjust to match your ADC)
WINDOW_SIZE = 256          # Samples per analysis window (1 second at 256 Hz)
OVERLAP = 128              # Overlapping samples between windows
BAUD_EEG = 230400          # Baud rate for EEG input (SpikeRecorder default)
BAUD_MOTOR = 9600          # Baud rate for Arduino motor controller

# EEG Frequency Bands (Hz)
BANDS = {
    'delta': (0.5, 4),
    'theta': (4, 7),
    'alpha': (8, 13),
    'beta':  (14, 30),
}

# Command classification thresholds
# High beta / alpha ratio = focused/active thought -> forward
# High alpha = relaxed -> stop
# High theta = drowsy -> stop + alert
BETA_ALPHA_THRESHOLD_FORWARD = 1.5
BETA_ALPHA_THRESHOLD_LEFT = 1.2
BETA_ALPHA_THRESHOLD_RIGHT = 1.8
ALPHA_DOMINANCE_THRESHOLD = 0.6   # Alpha is >60% of total -> stop


# ──────────────────────────────────────────
# Signal Processing Filters
# ──────────────────────────────────────────
def setup_filters(sampling_rate):
    """
    Create notch (50 Hz) and bandpass (0.5-30 Hz) IIR filters.
    Modify filter parameters as needed for your mains frequency (50/60 Hz).
    """
    # 50 Hz Notch Filter (removes power line interference)
    b_notch, a_notch = sig.iirnotch(
        w0=50.0 / (0.5 * sampling_rate),
        Q=30.0
    )

    # 0.5-30 Hz Bandpass Filter (isolates EEG frequency range)
    b_bandpass, a_bandpass = sig.butter(
        N=4,
        Wn=[0.5 / (0.5 * sampling_rate), 30.0 / (0.5 * sampling_rate)],
        btype='band'
    )

    return b_notch, a_notch, b_bandpass, a_bandpass


def process_eeg_data(data, b_notch, a_notch, b_bandpass, a_bandpass):
    """
    Apply notch and bandpass filters to raw EEG data.
    """
    # Remove 50 Hz power line noise
    filtered = sig.filtfilt(b_notch, a_notch, data)
    # Isolate 0.5-30 Hz EEG band
    filtered = sig.filtfilt(b_bandpass, a_bandpass, filtered)
    return filtered


# ──────────────────────────────────────────
# Feature Extraction
# ──────────────────────────────────────────
def calculate_psd_features(segment, sampling_rate):
    """
    Calculate Power Spectral Density (PSD) features for EEG frequency bands.
    Returns a dict with absolute and relative power for each band.
    """
    f, psd_values = sig.welch(segment, fs=sampling_rate, nperseg=len(segment))

    band_powers = {}
    total_power = np.trapz(psd_values, f)

    for band_name, (low, high) in BANDS.items():
        idx = np.logical_and(f >= low, f <= high)
        band_power = np.trapz(psd_values[idx], f[idx])
        band_powers[band_name] = {
            'absolute': band_power,
            'relative': band_power / total_power if total_power > 0 else 0
        }

    return band_powers


# ──────────────────────────────────────────
# Command Classification
# ──────────────────────────────────────────
def classify_command(band_powers):
    """
    Map EEG band power ratios to wheelchair commands.

    Classification logic:
      - High beta/alpha ratio -> focused intent -> 'f' (forward)
      - Moderate beta + left asymmetry -> 'l' (left)
      - High beta + right asymmetry -> 'r' (right)
      - Alpha dominant -> relaxed -> 's' (stop)
      - Theta dominant -> drowsy -> 's' (stop + warning)
    """
    alpha = band_powers['alpha']['relative']
    beta = band_powers['beta']['relative']
    theta = band_powers['theta']['relative']
    delta = band_powers['delta']['relative']

    # Safety: if theta is very high, user may be drowsy
    if theta > 0.4:
        return 's', 'DROWSY_ALERT'

    # Alpha dominance = relaxed = stop
    if alpha > ALPHA_DOMINANCE_THRESHOLD:
        return 's', 'RELAXED'

    # Beta/Alpha ratio for movement intent
    ratio = beta / alpha if alpha > 0.01 else 0

    if ratio > BETA_ALPHA_THRESHOLD_RIGHT:
        return 'r', f'RIGHT (B/A={ratio:.2f})'
    elif ratio > BETA_ALPHA_THRESHOLD_FORWARD:
        return 'f', f'FORWARD (B/A={ratio:.2f})'
    elif ratio > BETA_ALPHA_THRESHOLD_LEFT:
        return 'l', f'LEFT (B/A={ratio:.2f})'
    else:
        return 's', f'IDLE (B/A={ratio:.2f})'


# ──────────────────────────────────────────
# Serial Port Utilities
# ──────────────────────────────────────────
def find_ports():
    """List available serial ports."""
    ports = serial.tools.list_ports.comports()
    for p in ports:
        print(f"  [{p.device}] {p.description}")
    return ports


def connect_serial(port, baud, label=""):
    """Connect to a serial port with error handling."""
    try:
        ser = serial.Serial(port, baud, timeout=1)
        print(f"[+] {label} connected: {port} @ {baud} baud")
        return ser
    except Exception as e:
        print(f"[!] {label} failed on {port}: {e}")
        return None


# ──────────────────────────────────────────
# Main Processing Loop
# ──────────────────────────────────────────
def run_processor(eeg_serial, motor_serial, simulate=False):
    """
    Main real-time processing loop.
    Reads EEG samples, processes in windows, classifies, sends commands.
    """
    b_notch, a_notch, b_bandpass, a_bandpass = setup_filters(SAMPLING_RATE)
    buffer = deque(maxlen=WINDOW_SIZE)
    last_command = 's'
    sample_count = 0

    print("\n" + "=" * 60)
    print("  EEG Signal Processor - Real-Time Classification")
    print("=" * 60)
    print(f"  Sampling Rate : {SAMPLING_RATE} Hz")
    print(f"  Window Size   : {WINDOW_SIZE} samples ({WINDOW_SIZE / SAMPLING_RATE:.1f}s)")
    print(f"  Bands         : {', '.join(BANDS.keys())}")
    print(f"  Mode          : {'SIMULATION' if simulate else 'LIVE'}")
    print("=" * 60 + "\n")

    try:
        while True:
            # -- Read Samples --
            if simulate:
                # Generate synthetic EEG (10 Hz alpha + noise)
                t = sample_count / SAMPLING_RATE
                sample = (
                    50 * np.sin(2 * np.pi * 10 * t)     # Alpha wave
                    + 20 * np.sin(2 * np.pi * 22 * t)    # Beta wave
                    + 10 * np.random.randn()              # Noise
                    + 5 * np.sin(2 * np.pi * 50 * t)     # 50 Hz mains noise
                )
                buffer.append(sample)
                sample_count += 1
                time.sleep(1.0 / SAMPLING_RATE)
            else:
                # Read from SpikeRecorder serial
                if eeg_serial and eeg_serial.in_waiting > 0:
                    try:
                        raw = eeg_serial.readline().decode('utf-8', errors='ignore').strip()
                        if raw:
                            sample = float(raw)
                            buffer.append(sample)
                            sample_count += 1
                    except ValueError:
                        continue

            # -- Process Window --
            if len(buffer) >= WINDOW_SIZE and sample_count % OVERLAP == 0:
                segment = np.array(buffer)

                # Apply filters
                filtered = process_eeg_data(segment, b_notch, a_notch, b_bandpass, a_bandpass)

                # Extract PSD features
                band_powers = calculate_psd_features(filtered, SAMPLING_RATE)

                # Classify command
                command, reason = classify_command(band_powers)

                # Print telemetry
                powers_str = " | ".join(
                    f"{b.upper()}: {band_powers[b]['relative']:.3f}"
                    for b in BANDS
                )
                print(f"[{time.strftime('%H:%M:%S')}] {powers_str} -> CMD: '{command}' ({reason})")

                # Send command (only if changed)
                if command != last_command:
                    if motor_serial and motor_serial.is_open:
                        motor_serial.write(command.encode('utf-8'))
                        print(f"  >> Sent '{command}' to Arduino")
                    last_command = command

    except KeyboardInterrupt:
        print("\n[*] Shutting down EEG processor...")
    finally:
        if eeg_serial and eeg_serial.is_open:
            eeg_serial.close()
        if motor_serial and motor_serial.is_open:
            motor_serial.close()


# ──────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="EEG Signal Processor - Real-Time BCI Wheelchair Controller"
    )
    parser.add_argument('--eeg', type=str, help='Serial port for EEG input (e.g., COM3)')
    parser.add_argument('--motor', type=str, help='Serial port for Arduino motor controller (e.g., COM5)')
    parser.add_argument('--simulate', action='store_true', help='Run in simulation mode (no hardware)')
    parser.add_argument('--list-ports', action='store_true', help='List available serial ports and exit')
    args = parser.parse_args()

    if args.list_ports:
        print("Available serial ports:")
        find_ports()
        sys.exit(0)

    if args.simulate:
        print("[*] Running in SIMULATION mode (synthetic EEG data)")
        run_processor(None, None, simulate=True)
    else:
        print("Available serial ports:")
        find_ports()

        eeg_serial = connect_serial(args.eeg, BAUD_EEG, "EEG Input") if args.eeg else None
        motor_serial = connect_serial(args.motor, BAUD_MOTOR, "Motor Output") if args.motor else None

        if not eeg_serial and not motor_serial:
            print("\n[!] No ports specified. Use --simulate for demo mode.")
            print("    Example: python eeg_signal_processor.py --simulate")
            sys.exit(1)

        run_processor(eeg_serial, motor_serial)


if __name__ == '__main__':
    main()
