import random
from datetime import datetime


def generate_sensor_data(device):
    """
    Generate simulated sensor data for one industrial device.
    """

    device_type = device["device_type"]

    data = {
        "device_id": device["device_id"],
        "device_type": device_type,
        "timestamp": datetime.now().isoformat()
    }

    if device_type == "CNC":

        data.update({
            "spindle_temperature": round(random.uniform(55, 75), 2),
            "spindle_vibration": round(random.uniform(1, 4), 2),
            "spindle_rpm": random.randint(2500, 5000),
            "motor_current": round(random.uniform(8, 15), 2),
            "tool_wear": round(random.uniform(10, 40), 2),
            "cutting_force": round(random.uniform(400, 800), 2),
            "coolant_temperature": round(random.uniform(25, 35), 2),
            "coolant_flow_rate": round(random.uniform(8, 15), 2),
            "acoustic_emission": round(random.uniform(40, 65), 2),
            "power_consumption": round(random.uniform(4, 8), 2)
        })

    elif device_type == "PRESS":

        data.update({
            "hydraulic_pressure": round(random.uniform(100, 180), 2),
            "oil_temperature": round(random.uniform(40, 65), 2),
            "ram_position": round(random.uniform(0, 100), 2),
            "ram_speed": round(random.uniform(10, 30), 2),
            "motor_current": round(random.uniform(10, 20), 2),
            "stroke_count": random.randint(100, 500),
            "oil_flow_rate": round(random.uniform(15, 30), 2),
            "die_temperature": round(random.uniform(35, 60), 2),
            "vibration": round(random.uniform(1, 4), 2),
            "cycle_time": round(random.uniform(2, 6), 2)
        })

    elif device_type == "CONVEYOR":

        data.update({
            "motor_temperature": round(random.uniform(40, 65), 2),
            "motor_current": round(random.uniform(5, 12), 2),
            "belt_speed": round(random.uniform(1, 5), 2),
            "vibration": round(random.uniform(1, 4), 2),
            "load_weight": round(random.uniform(100, 500), 2),
            "alignment_deviation": round(random.uniform(0, 3), 2),
            "running_hours": round(random.uniform(100, 5000), 2),
            "start_stop_count": random.randint(50, 500),
            "ambient_temperature": round(random.uniform(20, 35), 2),
            "energy_consumption": round(random.uniform(2, 6), 2)
        })

    elif device_type == "ROBOT":

        data.update({
            "motor_temperature": round(random.uniform(40, 65), 2),
            "motor_current": round(random.uniform(5, 15), 2),
            "joint_position": round(random.uniform(0, 180), 2),
            "joint_speed": round(random.uniform(10, 60), 2),
            "vibration": round(random.uniform(1, 4), 2),
            "load": round(random.uniform(5, 30), 2),
            "cycle_time": round(random.uniform(2, 8), 2),
            "running_hours": round(random.uniform(100, 5000), 2),
            "energy_consumption": round(random.uniform(2, 7), 2),
            "error_count": random.randint(0, 3)
        })

    elif device_type == "PUMP":

        data.update({
            "inlet_pressure": round(random.uniform(2, 5), 2),
            "outlet_pressure": round(random.uniform(5, 10), 2),
            "flow_rate": round(random.uniform(20, 50), 2),
            "motor_temperature": round(random.uniform(40, 65), 2),
            "motor_current": round(random.uniform(5, 15), 2),
            "vibration": round(random.uniform(1, 4), 2),
            "rpm": random.randint(1000, 3000),
            "fluid_temperature": round(random.uniform(25, 50), 2),
            "leakage": round(random.uniform(0, 1), 2),
            "cavitation_indicator": round(random.uniform(0, 1), 2),
            "energy_consumption": round(random.uniform(2, 7), 2)
        })

    elif device_type == "COMPRESSOR":

        data.update({
            "discharge_pressure": round(random.uniform(7, 12), 2),
            "suction_pressure": round(random.uniform(1, 4), 2),
            "air_temperature": round(random.uniform(25, 45), 2),
            "motor_temperature": round(random.uniform(45, 70), 2),
            "motor_current": round(random.uniform(8, 18), 2),
            "vibration": round(random.uniform(1, 4), 2),
            "rpm": random.randint(1000, 3000),
            "air_flow_rate": round(random.uniform(50, 120), 2),
            "humidity": round(random.uniform(30, 70), 2),
            "running_hours": round(random.uniform(100, 5000), 2),
            "energy_consumption": round(random.uniform(5, 12), 2)
        })

    elif device_type == "ENERGY_METER":

        data.update({
            "voltage_l1": round(random.uniform(220, 240), 2),
            "voltage_l2": round(random.uniform(220, 240), 2),
            "voltage_l3": round(random.uniform(220, 240), 2),
            "current_l1": round(random.uniform(5, 20), 2),
            "current_l2": round(random.uniform(5, 20), 2),
            "current_l3": round(random.uniform(5, 20), 2),
            "active_power": round(random.uniform(5, 20), 2),
            "reactive_power": round(random.uniform(1, 5), 2),
            "power_factor": round(random.uniform(0.85, 0.99), 2),
            "frequency": round(random.uniform(49.8, 50.2), 2),
            "total_energy_kwh": round(random.uniform(1000, 10000), 2),
            "thd": round(random.uniform(1, 5), 2),
            "voltage_imbalance": round(random.uniform(0, 2), 2)
        })

    return data