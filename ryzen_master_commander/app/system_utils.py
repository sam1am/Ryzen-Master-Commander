import subprocess
import re
import json

def get_system_readings():
    try:
        output = subprocess.check_output(['nbfc', 'status', '-a'], text=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to execute 'nbfc status -a': {e}")
        return "n/a", "n/a"
    except FileNotFoundError:
        print("nbfc command not found. Make sure NoteBook FanControl is installed.")
        return "n/a", "n/a"

    temperature_match = re.search(r'Temperature\s+:\s+(\d+\.?\d*)', output)
    fan_speed_match = re.search(r'Current Fan Speed\s+:\s+(\d+\.?\d*)', output)

    temperature = temperature_match.group(1) if temperature_match else "n/a"
    fan_speed = fan_speed_match.group(1) if fan_speed_match else "n/a"
    return temperature, fan_speed

def apply_tdp_settings(current_profile):
    if current_profile:
        command = ['pkexec', 'ryzenadj']
        for key, value in current_profile.items():
            if key in ["fast-limit", "slow-limit"]:
                command.extend([f'--{key}={value * 1000}'])
            elif key == "slow-time":
                command.extend([f'--{key}={value * 1000}'])
            elif key not in ["name", "max_performance", "power_saving"]:
                command.extend([f'--{key}={value}'])
        if current_profile.get("power_saving"):
            command.append("--power-saving")
        elif current_profile.get("max_performance"):
            command.append("--max-performance")
        try:
            subprocess.run(command)
        except subprocess.CalledProcessError as e:
            print(f"Error applying TDP settings: {e}")

def apply_fan_profile(profile_name):
    """Apply a fan profile by name with nbfc command"""
    try:
        # Use the profile name (without extension) with nbfc config command
        profile_name = os.path.splitext(os.path.basename(profile_name))[0]
        subprocess.run(['pkexec', 'nbfc', 'config', '-a', profile_name], check=True)
        return True, f"Fan profile '{profile_name}' applied successfully"
    except Exception as e:
        return False, f"Error applying fan profile: {str(e)}"