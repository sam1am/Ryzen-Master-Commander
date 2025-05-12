import subprocess
import re
import os


def get_system_readings():
    # Get temperature and fan speed from NBFC
    try:
        output = subprocess.check_output(["nbfc", "status", "-a"], text=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to execute 'nbfc status -a': {e}")
        temp, fan_speed, profile = "n/a", "n/a", "n/a"
    except FileNotFoundError:
        print(
            "nbfc command not found. Make sure NoteBook FanControl is installed."
        )
        temp, fan_speed, profile = "n/a", "n/a", "n/a"
    else:
        temperature_match = re.search(r"Temperature\s+:\s+(\d+\.?\d*)", output)
        fan_speed_match = re.search(r"Current Fan Speed\s+:\s+(\d+\.?\d*)", output)
        current_profile_match = re.search(
            r"Selected Config Name\s+:\s+(.*?)$", output, re.MULTILINE
        )

        temp = temperature_match.group(1) if temperature_match else "n/a"
        fan_speed = fan_speed_match.group(1) if fan_speed_match else "n/a"
        profile = (
            current_profile_match.group(1) if current_profile_match else "n/a"
        )
    
    # Get power consumption data using sensors
    try:
        sensors_output = subprocess.check_output(["sensors"], text=True)
        power_match = re.search(r"power1:\s+(\d+\.\d+)\s*W", sensors_output)
        power = power_match.group(1) if power_match else "n/a"
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Failed to get power data: {e}")
        power = "n/a"
    
    return temp, fan_speed, profile, power


def apply_tdp_settings(current_profile):
    if current_profile:
        command = ["pkexec", "ryzenadj"]
        for key, value in current_profile.items():
            if key in ["fast-limit", "slow-limit"]:
                command.extend([f"--{key}={value * 1000}"])
            elif key == "slow-time":
                command.extend([f"--{key}={value * 1000}"])
            elif key not in ["name", "max-performance", "power-saving"]:
                command.extend([f"--{key}={value}"])
        if current_profile.get("power-saving"):
            command.append("--power-saving")
        elif current_profile.get("max-performance"):
            command.append("--max-performance")
        try:
            subprocess.run(command)
            print(f"Applied TDP settings with command: {' '.join(command)}")
            return True, "TDP settings applied successfully"
        except subprocess.CalledProcessError as e:
            error_msg = f"Error applying TDP settings: {e}"
            print(error_msg)
            return False, error_msg
    return False, "No profile selected"


def apply_fan_profile(profile_name):
    """Apply a fan profile by name with nbfc command"""
    try:
        # Use the profile name (without extension) with nbfc config command
        profile_name = os.path.splitext(os.path.basename(profile_name))[0]
        subprocess.run(
            ["pkexec", "nbfc", "config", "-a", profile_name], check=True
        )
        return True, f"Fan profile '{profile_name}' applied successfully"
    except Exception as e:
        return False, f"Error applying fan profile: {str(e)}"