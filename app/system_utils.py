import subprocess
import re

def get_system_readings():
    try:
        output = subprocess.check_output(['nbfc', 'status', '-a'], text=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to execute 'nbfc status -a': {e}")
        return "n/a", "n/a"

    temperature_match = re.search(r'Temperature\s+:\s+(\d+\.?\d*)', output)
    fan_speed_match = re.search(r'Current fan speed\s+:\s+(\d+\.?\d*)', output)

    temperature = temperature_match.group(1) if temperature_match else "n/a"
    fan_speed = fan_speed_match.group(1) if fan_speed_match else "n/a"
    print(f"Temperature: {temperature}, Fan Speed: {fan_speed}")
    return temperature, fan_speed

def apply_tdp_settings(current_profile, sudo_password):
    if current_profile:
        command = ['sudo', '-S', 'ryzenadj']
        for key, value in current_profile.items():
            if key in ["fast-limit", "slow-limit"]:
                command.extend([f'--{key}={value * 1000}'])
            elif key == "slow-time":
                command.extend([f'--{key}={value * 1000}'])
            elif key not in ["name", "max_performance", "power_saving"]:
                command.extend([f'--{key}={value}'])
        if current_profile.get("max_performance"):
            command.append("--max-performance")
        elif current_profile.get("power_saving"):
            command.append("--power-saving")
        try:
            subprocess.run(command, input=sudo_password + '\n', text=True)
        except subprocess.CalledProcessError as e:
            print(f"Error applying TDP settings: {e}")