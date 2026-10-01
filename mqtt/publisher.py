import json
import ssl
import time

import paho.mqtt.client as mqtt

from simulator.device_config import get_all_devices
from simulator.sensor_generator import generate_sensor_data
from simulator.fault_injector import inject_fault

from mqtt.config import (
    EMQX_BROKER,
    EMQX_PORT,
    EMQX_USERNAME,
    EMQX_PASSWORD,
    MQTT_KEEPALIVE
)


def on_connect(client, userdata, flags, reason_code, properties=None):

    if reason_code == 0:
        print("✅ Connected to EMQX Cloud")

    else:
        print(f"❌ EMQX connection failed: {reason_code}")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties=None):

    print(f"Disconnected from EMQX. Reason: {reason_code}")


def create_mqtt_client():

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="factory-simulator"
    )

    client.username_pw_set(
        EMQX_USERNAME,
        EMQX_PASSWORD
    )

    client.tls_set(
        cert_reqs=ssl.CERT_REQUIRED
    )

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    return client


def run_publisher(interval=2):

    devices = get_all_devices()

    client = create_mqtt_client()

    print("Connecting to EMQX Cloud...")

    client.connect(
        EMQX_BROKER,
        EMQX_PORT,
        MQTT_KEEPALIVE
    )

    client.loop_start()

    try:

        while True:

            for device in devices:

                # Generate normal telemetry
                data = generate_sensor_data(device)

                # Inject possible fault
                data, fault = inject_fault(data)

                # Add fault information to payload
                data["fault"] = fault

                # MQTT topic
                topic = (
                    f"factory/"
                    f"{device['device_type']}/"
                    f"{device['device_id']}/"
                    f"telemetry"
                )

                # Convert Python dictionary → JSON
                payload = json.dumps(data)

                # Publish
                result = client.publish(
                    topic,
                    payload,
                    qos=1
                )

                if result.rc == mqtt.MQTT_ERR_SUCCESS:

                    status = (
                        f"🚨 {fault}"
                        if fault
                        else "NORMAL"
                    )

                    print(
                        f"{device['device_id']} → "
                        f"{topic} → {status}"
                    )

                else:

                    print(
                        f"❌ Failed to publish "
                        f"{device['device_id']}"
                    )

            print("-" * 70)

            time.sleep(interval)

    except KeyboardInterrupt:

        print("\nStopping publisher...")

    finally:

        client.loop_stop()
        client.disconnect()

        print("MQTT connection closed.")


if __name__ == "__main__":
    run_publisher()