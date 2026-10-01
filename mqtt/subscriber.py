import json
import os
import ssl
import time
from typing import Dict, Tuple

import paho.mqtt.client as mqtt

from mqtt.config import (
    EMQX_BROKER,
    EMQX_PORT,
    EMQX_USERNAME,
    EMQX_PASSWORD,
    MQTT_KEEPALIVE
)

from database.db import insert_telemetry


TOPIC = "factory/+/+/telemetry"

# Configurable diagnosis throttling interval in seconds (default: 30s per well/event)
DIAGNOSIS_COOLDOWN_SECONDS = float(os.getenv("DIAGNOSIS_COOLDOWN_SECONDS", "30.0"))

# State tracker for throttling: maps well_id -> (last_event_name, last_diagnosis_timestamp)
_last_diagnosis_tracker: Dict[str, Tuple[str, float]] = {}


def on_connect(client, userdata, flags, reason_code, properties=None):

    if reason_code == 0:
        print("✅ Connected to EMQX Cloud")

        client.subscribe(TOPIC, qos=0)

        print(f"📡 Subscribed to: {TOPIC}")
        print("-" * 70)

    else:
        print(f"❌ Connection failed: {reason_code}")


try:
    from ml.detector import FaultDetectorPipeline
    _detector = FaultDetectorPipeline()
except Exception as e:
    print(f"⚠️ Warning initializing FaultDetectorPipeline: {e}")
    _detector = None


def should_trigger_diagnosis(well_id: str, event_name: str) -> bool:
    """
    Throttle diagnosis generation: only trigger if event changed or cooldown elapsed.
    """
    now = time.time()
    if well_id not in _last_diagnosis_tracker:
        return True
    
    last_event, last_time = _last_diagnosis_tracker[well_id]
    if event_name != last_event:
        return True
    
    if (now - last_time) >= DIAGNOSIS_COOLDOWN_SECONDS:
        return True
        
    return False


def on_message(client, userdata, message):

    try:
        # MQTT payload → JSON → Python dictionary
        data = json.loads(message.payload.decode())
        well_id = data.get("device_id", "LIVE-DEVICE")

        print(f"\n📥 MESSAGE RECEIVED")
        print(f"Topic: {message.topic}")

        # Run real-time ML fault detection
        if _detector:
            pred = _detector.predict(data, well_id=well_id)
            if pred["status"] == "anomaly" or pred.get("predicted_event_id", 0) > 0:
                event_name = pred["predicted_event"]
                confidence = pred["confidence"]
                data["fault"] = event_name

                print(f"🚨 ML DETECTED FAULT: {event_name} (Confidence: {confidence * 100:.1f}%)")

                # Trigger RAG + LLM Diagnosis if appropriate (debounced/throttled)
                if should_trigger_diagnosis(well_id, event_name):
                    try:
                        diag = _detector.diagnose(data, well_id=well_id)
                        data["diagnosis"] = diag
                        _last_diagnosis_tracker[well_id] = (event_name, time.time())

                        sources = ", ".join(diag.get("retrieved_sources", []))
                        print("\n🔎 RAG RETRIEVAL")
                        print(f"Source: {sources if sources else 'Petrobras 3W Domain Engineering Documentation'}")

                        print("\n📋 LLM DIAGNOSIS")
                        print("-" * 70)
                        print(diag.get("raw_diagnosis", "").strip())
                        print("-" * 70)

                    except Exception as diag_err:
                        print(f"⚠️ Note: RAG/LLM diagnosis error (non-fatal): {diag_err}")
                else:
                    print(f"⏳ Diagnosis throttled for {well_id} [{event_name}] (cooldown active: {DIAGNOSIS_COOLDOWN_SECONDS}s)")

        # Store telemetry in PostgreSQL
        insert_telemetry(data)

        print(
            f"💾 SAVED: "
            f"{data.get('device_id', 'UNKNOWN')} → PostgreSQL"
        )

    except json.JSONDecodeError:

        print("❌ Invalid JSON received")

    except Exception as e:

        print(f"❌ Error processing message: {e}")


def create_client():

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="factory-database-subscriber"
    )

    client.username_pw_set(
        EMQX_USERNAME,
        EMQX_PASSWORD
    )

    client.tls_set(
        cert_reqs=ssl.CERT_REQUIRED
    )

    client.on_connect = on_connect
    client.on_message = on_message

    return client


def main():

    client = create_client()

    print("Connecting to EMQX Cloud...")

    client.connect(
        EMQX_BROKER,
        EMQX_PORT,
        MQTT_KEEPALIVE
    )

    client.loop_forever()


if __name__ == "__main__":
    main()