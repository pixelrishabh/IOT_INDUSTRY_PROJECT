# simulator/device_config.py

DEVICE_TYPES = {
    "CNC": {
        "count": 5,
        "parameters": [
            "spindle_temperature",
            "spindle_vibration",
            "spindle_rpm",
            "motor_current",
            "tool_wear",
            "cutting_force",
            "coolant_temperature",
            "coolant_flow_rate",
            "acoustic_emission",
            "power_consumption"
        ]
    },

    "PRESS": {
        "count": 3,
        "parameters": [
            "hydraulic_pressure",
            "oil_temperature",
            "ram_position",
            "ram_speed",
            "motor_current",
            "stroke_count",
            "oil_flow_rate",
            "die_temperature",
            "vibration",
            "cycle_time"
        ]
    },

    "CONVEYOR": {
        "count": 2,
        "parameters": [
            "motor_temperature",
            "motor_current",
            "belt_speed",
            "vibration",
            "load_weight",
            "alignment_deviation",
            "running_hours",
            "start_stop_count",
            "ambient_temperature",
            "energy_consumption"
        ]
    },

    "ROBOT": {
        "count": 1,
        "parameters": [
            "motor_temperature",
            "motor_current",
            "joint_position",
            "joint_speed",
            "vibration",
            "load",
            "cycle_time",
            "running_hours",
            "energy_consumption",
            "error_count"
        ]
    },

    "PUMP": {
        "count": 2,
        "parameters": [
            "inlet_pressure",
            "outlet_pressure",
            "flow_rate",
            "motor_temperature",
            "motor_current",
            "vibration",
            "rpm",
            "fluid_temperature",
            "leakage",
            "cavitation_indicator",
            "energy_consumption"
        ]
    },

    "COMPRESSOR": {
        "count": 2,
        "parameters": [
            "discharge_pressure",
            "suction_pressure",
            "air_temperature",
            "motor_temperature",
            "motor_current",
            "vibration",
            "rpm",
            "air_flow_rate",
            "humidity",
            "running_hours",
            "energy_consumption"
        ]
    },

    "ENERGY_METER": {
        "count": 3,
        "parameters": [
            "voltage_l1",
            "voltage_l2",
            "voltage_l3",
            "current_l1",
            "current_l2",
            "current_l3",
            "active_power",
            "reactive_power",
            "power_factor",
            "frequency",
            "total_energy_kwh",
            "thd",
            "voltage_imbalance"
        ]
    }
}


def get_all_devices():
    """
    Generate all virtual devices for the simulated factory.
    """

    devices = []

    for device_type, config in DEVICE_TYPES.items():

        for i in range(1, config["count"] + 1):

            device_id = f"{device_type}-{i:02d}"

            devices.append({
                "device_id": device_id,
                "device_type": device_type,
                "parameters": config["parameters"]
            })

    return devices