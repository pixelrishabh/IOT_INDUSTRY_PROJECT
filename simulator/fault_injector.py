
import random


def inject_fault(data):
    """
    Randomly inject a realistic fault into industrial sensor data.

    Fault probability:
        10% chance of fault
        90% chance of normal operation

    Returns:
        data  : Modified sensor data
        fault : Fault name or None
    """

    device_type = data["device_type"]

    # 90% normal operation
    if random.random() > 0.10:
        return data, None

    # =========================================================
    # CNC FAULTS
    # =========================================================

    if device_type == "CNC":

        fault = random.choice([
            "spindle_overheating",
            "excessive_vibration",
            "tool_wear"
        ])

        if fault == "spindle_overheating":

            data["spindle_temperature"] = round(
                random.uniform(90, 110), 2
            )

            data["motor_current"] = round(
                random.uniform(16, 22), 2
            )

        elif fault == "excessive_vibration":

            data["spindle_vibration"] = round(
                random.uniform(7, 12), 2
            )

            data["acoustic_emission"] = round(
                random.uniform(75, 100), 2
            )

        elif fault == "tool_wear":

            data["tool_wear"] = round(
                random.uniform(80, 100), 2
            )

            data["cutting_force"] = round(
                random.uniform(900, 1200), 2
            )

        return data, fault

    # =========================================================
    # PRESS FAULTS
    # =========================================================

    elif device_type == "PRESS":

        fault = random.choice([
            "hydraulic_pressure_drop",
            "oil_overheating",
            "excessive_vibration"
        ])

        if fault == "hydraulic_pressure_drop":

            data["hydraulic_pressure"] = round(
                random.uniform(40, 70), 2
            )

            data["oil_flow_rate"] = round(
                random.uniform(5, 10), 2
            )

        elif fault == "oil_overheating":

            data["oil_temperature"] = round(
                random.uniform(80, 100), 2
            )

            data["die_temperature"] = round(
                random.uniform(70, 90), 2
            )

        elif fault == "excessive_vibration":

            data["vibration"] = round(
                random.uniform(8, 12), 2
            )

        return data, fault

    # =========================================================
    # CONVEYOR FAULTS
    # =========================================================

    elif device_type == "CONVEYOR":

        fault = random.choice([
            "motor_overheating",
            "belt_misalignment",
            "excessive_vibration"
        ])

        if fault == "motor_overheating":

            data["motor_temperature"] = round(
                random.uniform(85, 105), 2
            )

            data["motor_current"] = round(
                random.uniform(15, 22), 2
            )

        elif fault == "belt_misalignment":

            data["alignment_deviation"] = round(
                random.uniform(8, 15), 2
            )

        elif fault == "excessive_vibration":

            data["vibration"] = round(
                random.uniform(8, 12), 2
            )

        return data, fault

    # =========================================================
    # ROBOT FAULTS
    # =========================================================

    elif device_type == "ROBOT":

        fault = random.choice([
            "motor_overheating",
            "joint_vibration",
            "excessive_load"
        ])

        if fault == "motor_overheating":

            data["motor_temperature"] = round(
                random.uniform(85, 105), 2
            )

        elif fault == "joint_vibration":

            data["vibration"] = round(
                random.uniform(8, 12), 2
            )

        elif fault == "excessive_load":

            data["load"] = round(
                random.uniform(40, 60), 2
            )

            data["motor_current"] = round(
                random.uniform(18, 25), 2
            )

        return data, fault

    # =========================================================
    # PUMP FAULTS
    # =========================================================

    elif device_type == "PUMP":

        fault = random.choice([
            "cavitation",
            "pressure_drop",
            "motor_overheating"
        ])

        if fault == "cavitation":

            data["cavitation_indicator"] = round(
                random.uniform(0.80, 1.00), 2
            )

            data["vibration"] = round(
                random.uniform(7, 12), 2
            )

        elif fault == "pressure_drop":

            data["outlet_pressure"] = round(
                random.uniform(2, 4), 2
            )

            data["flow_rate"] = round(
                random.uniform(5, 15), 2
            )

        elif fault == "motor_overheating":

            data["motor_temperature"] = round(
                random.uniform(85, 105), 2
            )

            data["motor_current"] = round(
                random.uniform(18, 25), 2
            )

        return data, fault

    # =========================================================
    # COMPRESSOR FAULTS
    # =========================================================

    elif device_type == "COMPRESSOR":

        fault = random.choice([
            "high_discharge_pressure",
            "motor_overheating",
            "excessive_vibration"
        ])

        if fault == "high_discharge_pressure":

            data["discharge_pressure"] = round(
                random.uniform(14, 18), 2
            )

        elif fault == "motor_overheating":

            data["motor_temperature"] = round(
                random.uniform(85, 105), 2
            )

            data["motor_current"] = round(
                random.uniform(20, 28), 2
            )

        elif fault == "excessive_vibration":

            data["vibration"] = round(
                random.uniform(8, 12), 2
            )

        return data, fault

    # =========================================================
    # ENERGY METER FAULTS
    # =========================================================

    elif device_type == "ENERGY_METER":

        fault = random.choice([
            "voltage_imbalance",
            "low_power_factor",
            "high_thd"
        ])

        if fault == "voltage_imbalance":

            data["voltage_l1"] = round(
                random.uniform(200, 210), 2
            )

            data["voltage_l2"] = round(
                random.uniform(220, 240), 2
            )

            data["voltage_l3"] = round(
                random.uniform(245, 255), 2
            )

            data["voltage_imbalance"] = round(
                random.uniform(5, 10), 2
            )

        elif fault == "low_power_factor":

            data["power_factor"] = round(
                random.uniform(0.55, 0.70), 2
            )

            data["reactive_power"] = round(
                random.uniform(8, 15), 2
            )

        elif fault == "high_thd":

            data["thd"] = round(
                random.uniform(10, 20), 2
            )

        return data, fault

    # =========================================================
    # UNKNOWN DEVICE
    # =========================================================

    return data, None
