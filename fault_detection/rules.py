def detect_cnc_fault(data):
    faults = []

    if data.get("spindle_temperature", 0) > 85:
        faults.append("spindle_overheating")

    if data.get("vibration", 0) > 8:
        faults.append("excessive_vibration")

    if data.get("tool_wear", 0) > 80:
        faults.append("tool_wear")

    return faults


def detect_press_fault(data):
    faults = []

    if data.get("hydraulic_pressure", 0) < 80:
        faults.append("hydraulic_pressure_drop")

    if data.get("oil_temperature", 0) > 85:
        faults.append("oil_overheating")

    if data.get("vibration", 0) > 8:
        faults.append("excessive_vibration")

    return faults


def detect_conveyor_fault(data):
    faults = []

    if data.get("motor_temperature", 0) > 85:
        faults.append("motor_overheating")

    if data.get("belt_alignment", 0) > 5:
        faults.append("belt_misalignment")

    if data.get("vibration", 0) > 8:
        faults.append("excessive_vibration")

    return faults


def detect_robot_fault(data):
    faults = []

    if data.get("motor_temperature", 0) > 85:
        faults.append("motor_overheating")

    if data.get("joint_vibration", 0) > 8:
        faults.append("joint_vibration")

    if data.get("load", 0) > 90:
        faults.append("excessive_load")

    return faults


def detect_pump_fault(data):
    faults = []

    if data.get("cavitation", 0) > 0.8:
        faults.append("cavitation")

    if data.get("pressure", 0) < 40:
        faults.append("pressure_drop")

    if data.get("motor_temperature", 0) > 85:
        faults.append("motor_overheating")

    return faults


def detect_compressor_fault(data):
    faults = []

    if data.get("discharge_pressure", 0) > 150:
        faults.append("high_discharge_pressure")

    if data.get("motor_temperature", 0) > 85:
        faults.append("motor_overheating")

    if data.get("vibration", 0) > 8:
        faults.append("excessive_vibration")

    return faults


def detect_energy_meter_fault(data):
    faults = []

    if data.get("voltage_imbalance", 0) > 5:
        faults.append("voltage_imbalance")

    if data.get("power_factor", 1) < 0.7:
        faults.append("low_power_factor")

    if data.get("thd", 0) > 8:
        faults.append("high_thd")

    return faults