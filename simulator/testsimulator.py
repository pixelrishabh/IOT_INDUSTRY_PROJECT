from simulator.device_config import get_all_devices
from simulator.sensor_generator import generate_sensor_data
from simulator.fault_injector import inject_fault


devices = get_all_devices()

for device in devices:

    data = generate_sensor_data(device)

    data, fault = inject_fault(data)

    print("\n-----------------------------")
    print("DEVICE:", data["device_id"])
    print("TYPE:", data["device_type"])

    if fault:
        print("🚨 FAULT:", fault)
    else:
        print("STATUS: NORMAL")

    print("DATA:", data)