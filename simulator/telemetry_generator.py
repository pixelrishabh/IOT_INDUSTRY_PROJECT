# simulator/telemetry_generator.py

import random


def add_noise(value, percentage=0.02):
    """
    Add small random variation to a sensor value.
    """

    noise = value * percentage

    return round(
        value + random.uniform(-noise, noise),
        2
    )


def generate_telemetry(device):

    device_type = device["device_type"]

    telemetry = {}

    if device_type == "CNC":

        telemetry = {
            "spindle_temperature": add_noise(65),
            "spindle_vibration": add_noise(2.5),
            "spindle_rpm": add_noise(3500),
            "motor_current": add_noise(18),
            "tool_wear": add_noise(20),
            "cutting_force": add_noise(450),
            "coolant_temperature": add_noise(28),
            "coolant_flow_rate": add_noise(15),
            "acoustic_emission": add_noise(55),
            "power_consumption": add_noise(8.5)
        }

    elif device_type == "PRESS":

        telemetry = {
            "hydraulic_pressure": add_noise(180),
            "oil_temperature": add_noise(55),
            "ram_position": add_noise(120),
            "ram_speed": add_noise(40),
            "motor_current": add_noise(30),
            "stroke_count": random.randint(1000, 5000),
            "oil_flow_rate": add_noise(25),
            "die_temperature": add_noise(120),
            "vibration": add_noise(3),
            "cycle_time": add_noise(8)
        }

    elif device_type == "CONVEYOR":

        telemetry = {
            "motor_temperature": add_noise(45),
            "motor_current": add_noise(8),
            "belt_speed": add_noise(2.5),
            "vibration": add_noise(1.5),
            "load_weight": add_noise(250),
            "alignment_deviation": add_noise(2),
            "running_hours": add_noise(2500),
            "start_stop_count": random.randint(100, 500),
            "ambient_temperature": add_noise(30),
            "energy_consumption": add_noise(3.5)
        }

    elif device_type == "ROBOT":

        telemetry = {
            "motor_temperature": add_noise(50),
            "motor_current": add_noise(12),
            "joint_position": add_noise(45),
            "joint_speed": add_noise(80),
            "vibration": add_noise(1.2),
            "load": add_noise(40),
            "cycle_time": add_noise(12),
            "running_hours": add_noise(4000),
            "energy_consumption": add_noise(4),
            "error_count": random.randint(0, 2)
        }

    elif device_type == "PUMP":

        telemetry = {
            "inlet_pressure": add_noise(3),
            "outlet_pressure": add_noise(8),
            "flow_rate": add_noise(40),
            "motor_temperature": add_noise(50),
            "motor_current": add_noise(15),
            "vibration": add_noise(2),
            "rpm": add_noise(1450),
            "fluid_temperature": add_noise(40),
            "leakage": round(random.uniform(0, 0.05), 3),
            "cavitation_indicator": round(random.uniform(0, 0.1), 3),
            "energy_consumption": add_noise(5)
        }

    elif device_type == "COMPRESSOR":

        telemetry = {
            "discharge_pressure": add_noise(8),
            "suction_pressure": add_noise(1),
            "air_temperature": add_noise(35),
            "motor_temperature": add_noise(60),
            "motor_current": add_noise(20),
            "vibration": add_noise(2),
            "rpm": add_noise(3000),
            "air_flow_rate": add_noise(100),
            "humidity": add_noise(45),
            "running_hours": add_noise(5000),
            "energy_consumption": add_noise(12)
        }

    elif device_type == "ENERGY_METER":

        telemetry = {
            "voltage_l1": add_noise(230),
            "voltage_l2": add_noise(230),
            "voltage_l3": add_noise(230),
            "current_l1": add_noise(20),
            "current_l2": add_noise(20),
            "current_l3": add_noise(20),
            "active_power": add_noise(12),
            "reactive_power": add_noise(4),
            "power_factor": add_noise(0.95),
            "frequency": add_noise(50),
            "total_energy_kwh": add_noise(15000),
            "thd": add_noise(3),
            "voltage_imbalance": add_noise(1)
        }

    return telemetry