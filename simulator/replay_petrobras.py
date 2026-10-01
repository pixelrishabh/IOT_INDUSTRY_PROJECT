"""
replay_petrobras.py - Real-World Petrobras 3W Well Telemetry Replayer
Streams genuine held-out oil well sensor readings from 3W Dataset 2.0.0
through MQTT (EMQX Cloud / Local) into the real-time IoT fault diagnosis pipeline.
"""

import argparse
import json
import os
import ssl
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import paho.mqtt.client as mqtt

from mqtt.config import (
    EMQX_BROKER,
    EMQX_PORT,
    EMQX_USERNAME,
    EMQX_PASSWORD,
    MQTT_KEEPALIVE
)

DATASET_ROOT = Path("Dstaset/3w_dataset_2.0.0")

# 3W Event descriptions for console logging
EVENT_NAMES = {
    0: "Normal Operation",
    1: "Abrupt Increase of BSW",
    2: "Spurious Closure of DHSV",
    3: "Severe Slugging",
    4: "Flow Instability",
    5: "Rapid Productivity Loss",
    6: "Quick Restriction in PCK",
    7: "Scaling in PCK",
    8: "Hydrate in Production Line",
    9: "Hydrate in Service Line",
}


def get_sample_files():
    """Retrieve sample real WELL parquet files for each event type."""
    sample_files = {}
    for event_id in range(10):
        folder = DATASET_ROOT / str(event_id)
        if folder.exists():
            files = sorted(list(folder.glob("WELL-*.parquet")))
            if files:
                sample_files[event_id] = files[0]
    return sample_files


def create_mqtt_client(client_id: str = "petrobras-3w-replayer") -> mqtt.Client:
    """Initialize secure MQTT client."""
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id
    )
    if EMQX_USERNAME and EMQX_PASSWORD:
        client.username_pw_set(EMQX_USERNAME, EMQX_PASSWORD)
    try:
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    except Exception as e:
        print(f"[MQTT] TLS notice: {e}")
    return client


def stream_petrobras_file(
    file_path: Path,
    client: Optional[mqtt.Client] = None,
    delay_sec: float = 0.5,
    max_records: int = 120,
    topic_prefix: str = "factory/oil_well"
):
    """
    Stream real 1-second telemetry rows from a Petrobras Parquet file.
    """
    print(f"\n==================================================")
    print(f"STREAMING REAL WELL FILE: {file_path.name}")
    print(f"Parent Folder: Event {file_path.parent.name} ({EVENT_NAMES.get(int(file_path.parent.name), 'Unknown')})")
    print(f"==================================================")

    df = pd.read_parquet(file_path)
    well_id = file_path.name.split("_")[0]
    topic = f"{topic_prefix}/{well_id}/telemetry"

    # Identify numerical sensors
    sensor_cols = [c for c in df.columns if c not in ["class", "state"] and pd.api.types.is_numeric_dtype(df[c])]
    
    # Subsample if max_records specified
    records_to_stream = df.iloc[:max_records]

    print(f"Total rows in recording: {len(df)} | Streaming up to: {len(records_to_stream)} rows")
    print(f"Target MQTT Topic: {topic}")
    print(f"Publish interval : {delay_sec}s per observation\n")

    for idx, (ts, row) in enumerate(records_to_stream.iterrows()):
        ts_str = str(ts) if isinstance(ts, pd.Timestamp) else str(row.get("timestamp", time.time()))
        
        # Build payload with real sensor measurements
        sensor_data = {}
        for col in sensor_cols:
            val = row[col]
            if pd.notna(val):
                sensor_data[col] = float(val)
            else:
                sensor_data[col] = None

        ground_truth_class = int(row["class"]) if ("class" in row and pd.notna(row["class"])) else None

        payload = {
            "device_id": well_id,
            "device_type": "oil_well",
            "timestamp": ts_str,
            "ground_truth_class": ground_truth_class,
            "recording_file": file_path.name,
            **sensor_data
        }

        json_payload = json.dumps(payload)

        if client:
            try:
                client.publish(topic, json_payload, qos=0)
            except Exception as e:
                print(f"Publish error: {e}")

        # Console telemetry display
        p_pdg_str = f"{sensor_data.get('P-PDG', 0)/1e5:.1f} bar" if sensor_data.get("P-PDG") else "N/A"
        p_tpt_str = f"{sensor_data.get('P-TPT', 0)/1e5:.1f} bar" if sensor_data.get("P-TPT") else "N/A"
        t_tpt_str = f"{sensor_data.get('T-TPT', 0):.1f} °C" if sensor_data.get("T-TPT") else "N/A"
        p_mon_str = f"{sensor_data.get('P-MON-CKP', 0)/1e5:.1f} bar" if sensor_data.get("P-MON-CKP") else "N/A"
        
        print(f"[{idx+1:03d}/{len(records_to_stream)}] {ts_str} | {well_id} | P-PDG: {p_pdg_str} | P-TPT: {p_tpt_str} | T-TPT: {t_tpt_str} | P-MON: {p_mon_str}")

        if delay_sec > 0:
            time.sleep(delay_sec)

    print(f"\nFinished streaming {len(records_to_stream)} rows from {file_path.name}.")


def main():
    parser = argparse.ArgumentParser(description="Petrobras 3W Real-Well Telemetry Replayer")
    parser.add_argument("--event", type=int, default=3, help="Event class (0-9) to replay")
    parser.add_argument("--file", type=str, default=None, help="Specific parquet file path")
    parser.add_argument("--delay", type=float, default=0.2, help="Seconds between rows")
    parser.add_argument("--max-rows", type=int, default=60, help="Max rows to stream")
    parser.add_argument("--dry-run", action="store_true", help="Print without publishing to MQTT")
    args = parser.parse_args()

    # Determine file
    if args.file:
        target_path = Path(args.file)
    else:
        sample_files = get_sample_files()
        if args.event not in sample_files:
            raise ValueError(f"No real files found for event {args.event}")
        target_path = sample_files[args.event]

    client = None
    if not args.dry_run:
        try:
            client = create_mqtt_client()
            print(f"Connecting to MQTT broker at {EMQX_BROKER}:{EMQX_PORT}...")
            client.connect(EMQX_BROKER, EMQX_PORT, MQTT_KEEPALIVE)
            client.loop_start()
            print("Connected to MQTT broker.")
        except Exception as e:
            print(f"MQTT connection notice (running local replay): {e}")

    stream_petrobras_file(
        file_path=target_path,
        client=client,
        delay_sec=args.delay,
        max_records=args.max_rows
    )

    if client:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
