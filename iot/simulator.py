"""
reServe AI - IoT Gateway & Sensory Ingestion Pipeline
Simulates ESP32 microcontrollers streaming environmental telemetry
(Temperature, Humidity, Methane/Gas MQ-4, Energy kWh, Water Flow)
over MQTT / HTTP directly to the backend.
"""

import time
import random
import requests
from typing import Dict, Any

class KitchenIoTSimulator:
    def __init__(self, backend_url: str = "http://localhost:8000/api/v1"):
        self.backend_url = backend_url
        self.sensors = [
            {"id": "ESP32-COLD-01", "type": "TEMPERATURE", "zone": "Walk-in Cold Room A", "min": 1.5, "max": 4.5, "unit": "°C"},
            {"id": "ESP32-COLD-02", "type": "HUMIDITY", "zone": "Walk-in Cold Room A", "min": 60.0, "max": 75.0, "unit": "%RH"},
            {"id": "ESP32-GAS-01", "type": "GAS_METHANE", "zone": "Cold Storage Exhaust", "min": 2.0, "max": 8.0, "unit": "PPM"},
            {"id": "ESP32-DAIRY-01", "type": "TEMPERATURE", "zone": "Dairy Chiller Room", "min": 2.0, "max": 5.0, "unit": "°C"},
            {"id": "ESP32-PANTRY-01", "type": "TEMPERATURE", "zone": "Dry Grain Pantry", "min": 18.0, "max": 24.0, "unit": "°C"},
        ]

    def generate_reading(self, sensor: Dict[str, Any], inject_anomaly: bool = False) -> Dict[str, Any]:
        """Generate reading with optional threshold breach anomaly."""
        val = random.uniform(sensor["min"], sensor["max"])
        if inject_anomaly:
            val += 8.5  # Spikes temperature above safety threshold
        return {
            "kitchen_id": 1,
            "sensor_id": sensor["id"],
            "sensor_type": sensor["type"],
            "value": round(val, 2),
            "unit": sensor["unit"],
            "storage_zone": sensor["zone"]
        }

    def emit_telemetry_batch(self, inject_anomaly: bool = False):
        """Dispatches sensory packet to backend REST/MQTT bridge."""
        for sensor in self.sensors:
            payload = self.generate_reading(sensor, inject_anomaly and sensor["type"] == "TEMPERATURE")
            try:
                res = requests.post(f"{self.backend_url}/sensors/readings", json=payload, timeout=2.0)
                if res.status_code == 200:
                    print(f"[IoT] Streamed {sensor['id']} -> {payload['value']}{payload['unit']}")
            except Exception as e:
                # Backend might not be running at the exact instant
                pass

if __name__ == "__main__":
    sim = KitchenIoTSimulator()
    print("Starting reServe AI ESP32 Sensory Stream Simulator...")
    for _ in range(5):
        sim.emit_telemetry_batch()
        time.sleep(1)
