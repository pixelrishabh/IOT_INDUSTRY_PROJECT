from fault_detection.rules import (
    detect_cnc_fault,
    detect_press_fault,
    detect_conveyor_fault,
    detect_robot_fault,
    detect_pump_fault,
    detect_compressor_fault,
    detect_energy_meter_fault,
)


DETECTORS = {
    "CNC": detect_cnc_fault,
    "PRESS": detect_press_fault,
    "CONVEYOR": detect_conveyor_fault,
    "ROBOT": detect_robot_fault,
    "PUMP": detect_pump_fault,
    "COMPRESSOR": detect_compressor_fault,
    "ENERGY_METER": detect_energy_meter_fault,
}


def detect_fault(data):
    device_type = data.get("device_type")

    detector = DETECTORS.get(device_type)

    if detector is None:
        return []

    return detector(data)

if __name__ == "__main__":

    test_data = {
        "device_type": "CNC",
        "spindle_temperature": 95,
        "vibration": 10,
        "tool_wear": 90
    }

    detected = detect_fault(test_data)

    print("Detected faults:")
    for fault in detected:
        print("⚠️", fault)