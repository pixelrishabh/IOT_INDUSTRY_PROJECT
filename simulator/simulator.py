import time

from simulator.device_config import get_all_devices
from simulator.sensor_generator import generate_sensor_data
from simulator.fault_injector import inject_fault


def run_simulator(interval=2):
    """
    Continuously generate telemetry for all virtual devices.
    """

    devices = get_all_devices()

    print(f"Starting factory simulator...")
    print(f"Total devices: {len(devices)}")
    print(f"Publishing cycle every {interval} seconds")
    print("-" * 50)

    try:
        while True:

            for device in devices:

                # Generate normal sensor data
                data = generate_sensor_data(device)

                # Possibly inject a fault
                data, fault = inject_fault(data)

                print(
                    f"{data['device_id']} | "
                    f"{data['device_type']} | ",
                    end=""
                )

                if fault:
                    print(f"🚨 FAULT: {fault}")
                else:
                    print("NORMAL")

            print("-" * 50)

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nSimulator stopped.")


if __name__ == "__main__":
    run_simulator()