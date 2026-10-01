import json
import ssl

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
except Exception:
    _detector = None


def on_message(client, userdata, message):

    try:

        # MQTT payload → JSON → Python dictionary
        data = json.loads(message.payload.decode())

        print(f"\n📥 MESSAGE RECEIVED")
        print(f"Topic: {message.topic}")

        # Run real-time ML fault detection if fault not already tagged
        if _detector and not data.get("fault"):
            pred = _detector.predict(data, well_id=data.get("device_id", "LIVE-DEVICE"))
            if pred["status"] == "anomaly":
                data["fault"] = pred["predicted_event"]
                print(f"🚨 ML DETECTED FAULT: {data['fault']} (Confidence: {pred['confidence']*100:.1f}%)")

        # Store telemetry in PostgreSQL
        insert_telemetry(data)

        print(
            f"💾 SAVED: "
            f"{data['device_id']} → PostgreSQL"
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