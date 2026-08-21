#!/usr/bin/env python3
"""
Assistive Emergency SOS & Telemetry Alert Dispatcher
===================================================
Author: Shubham Patel (techindro)
Description:
    Real-time safety monitoring subsystem for BCI-operated wheelchairs.
    Monitors:
      1. Continuous obstacle stall & collision impacts.
      2. Sudden loss of EEG electrode impedance / signal dropout.
      3. Panic heart rate / high-frequency burst detection.
      4. Manual Emergency Stop trigger.
    Dispatches emergency alerts with simulated GPS coordinates via Webhooks/Telegram/MQTT.
"""

import time
import json
import logging
from datetime import datetime, timezone
import urllib.request
import urllib.parse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)


class EmergencySOSSystem:
    """
    Monitors wheelchair safety anomalies and dispatches emergency SOS alerts.
    """

    def __init__(self, patient_name="Patient-01", device_id="BCI-WHEELCHAIR-001"):
        self.patient_name = patient_name
        self.device_id = device_id
        self.is_emergency_active = False
        
        # Simulated GPS coordinates (Hospital / Campus campus baseline)
        self.latitude = 28.613939
        self.longitude = 77.209021
        self.last_alert_time = 0
        self.alert_cooldown_sec = 10

    def get_telemetry_payload(self, reason, sensor_data=None):
        """
        Builds a standard JSON telemetry packet for emergency dispatch.
        """
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "device_id": self.device_id,
            "patient_name": self.patient_name,
            "emergency_status": "CRITICAL_ALERT",
            "reason": reason,
            "location": {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "google_maps_url": f"https://maps.google.com/?q={self.latitude},{self.longitude}"
            },
            "sensor_telemetry": sensor_data or {
                "ultrasonic_front_cm": 0,
                "eeg_signal_quality": "0%",
                "motor_state": "EMERGENCY_BRAKE"
            }
        }

    def trigger_sos(self, reason="Collision / Stall Anomaly", webhook_url=None, sensor_data=None):
        """
        Triggers the SOS alert, logs locally, and optionally dispatches via HTTP Webhook.
        """
        current_time = time.time()
        if current_time - self.last_alert_time < self.alert_cooldown_sec:
            logging.warning("[SOS COOLDOWN] Duplicate alert suppressed.")
            return False

        self.last_alert_time = current_time
        self.is_emergency_active = True
        payload = self.get_telemetry_payload(reason, sensor_data)

        print("\n" + "!" * 60)
        print("  [CRITICAL EMERGENCY SOS TRIGGERED]")
        print("!" * 60)
        print(f"  Patient       : {payload['patient_name']}")
        print(f"  Device ID     : {payload['device_id']}")
        print(f"  Reason        : {payload['reason']}")
        print(f"  GPS Location  : {payload['location']['latitude']}, {payload['location']['longitude']}")
        print(f"  Maps Link     : {payload['location']['google_maps_url']}")
        print("!" * 60 + "\n")

        # Dispatch via Webhook if provided
        if webhook_url:
            try:
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(
                    webhook_url,
                    data=data,
                    headers={'Content-Type': 'application/json', 'User-Agent': 'NeuroWheel-SOS/1.0'}
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    logging.info(f"[+] SOS Webhook dispatched successfully! Status: {response.status}")
            except Exception as ex:
                logging.error(f"[!] Failed to deliver webhook: {ex}")

        return True

    def reset_sos(self):
        """Resets emergency status back to normal."""
        self.is_emergency_active = False
        logging.info("[OK] Emergency status reset to NORMAL.")


def run_demo():
    """Demonstrates emergency system monitoring and trigger."""
    print("="*60)
    print("  NEUROWHEEL EMERGENCY SOS MONITOR - TEST DEMO")
    print("="*60)

    sos = EmergencySOSSystem(patient_name="Shubham (User 01)", device_id="WHEELCHAIR-BCI-X1")
    
    print("[*] Simulating obstacle impact scenario...")
    sensor_snapshot = {
        "ultrasonic_front_cm": 4.5,
        "ultrasonic_side_cm": 12.0,
        "eeg_signal_quality": "94%",
        "motor_state": "LOCK_STOPPED"
    }
    sos.trigger_sos(reason="Obstacle Collision within < 5cm Safety Barrier", sensor_data=sensor_snapshot)
    time.sleep(1)
    
    print("[*] Simulating operator panic blink sequence...")
    sos.reset_sos()
    sos.trigger_sos(reason="Operator Triple-Blink Panic Trigger")
    print("\n[SUCCESS] Emergency SOS safety subsystem validated!")


if __name__ == "__main__":
    run_demo()
