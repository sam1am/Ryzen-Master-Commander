import subprocess
import re
import os
from PyQt6.QtCore import QProcess


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


def apply_tdp_settings(current_profile, callback=None, parent=None):
    """Apply TDP settings using QProcess for non-blocking execution.

    Args:
        current_profile: Profile dictionary with TDP settings
        callback: Optional callback function(success, message) to call when complete
        parent: Parent QObject to own the QProcess (prevents garbage collection)
    """
    if current_profile:
        command = ["ryzenadj"]

        # Basic settings always included
        if "fast-limit" in current_profile:
            command.extend([f"--fast-limit={current_profile['fast-limit'] * 1000}"])
        if "slow-limit" in current_profile:
            command.extend([f"--slow-limit={current_profile['slow-limit'] * 1000}"])

        # Advanced settings only if provided
        if "slow-time" in current_profile:
            command.extend([f"--slow-time={current_profile['slow-time'] * 1000}"])

        # Other advanced parameters
        for key in ["tctl-temp", "apu-skin-temp"]:
            if key in current_profile:
                command.extend([f"--{key}={current_profile[key]}"])

        # Performance mode flags
        if current_profile.get("power-saving"):
            command.append("--power-saving")
        elif current_profile.get("max-performance"):
            command.append("--max-performance")

        print(f"Applying TDP settings with command: pkexec {' '.join(command)}")

        # Create QProcess for non-blocking execution with parent to prevent GC
        process = QProcess(parent)

        # Store callback for when process finishes
        def on_finished(exit_code, exit_status):
            if exit_code == 0 and exit_status == QProcess.ExitStatus.NormalExit:
                print("TDP settings applied successfully")
                if callback:
                    callback(True, "TDP settings applied successfully")
            else:
                error_msg = f"Error applying TDP settings (exit code: {exit_code})"
                stderr = process.readAllStandardError().data().decode('utf-8', errors='ignore')
                if stderr:
                    error_msg += f": {stderr}"
                print(error_msg)
                if callback:
                    callback(False, error_msg)
            # Clean up process after finished
            process.deleteLater()

        process.finished.connect(on_finished)

        # Start the process with pkexec
        process.start("pkexec", command)

        # Note: We don't return True/False immediately since it's async
        # Callback will be called when process completes
        return None

    if callback:
        callback(False, "No profile selected")
    return False, "No profile selected"


def apply_fan_profile(profile_name, callback=None, parent=None):
    """Apply a fan profile by name with nbfc command using QProcess.

    Args:
        profile_name: Name of the fan profile to apply
        callback: Optional callback function(success, message) to call when complete
        parent: Parent QObject to own the QProcess (prevents garbage collection)
    """
    # Use the profile name (without extension) with nbfc config command
    profile_name = os.path.splitext(os.path.basename(profile_name))[0]

    print(f"Applying fan profile: {profile_name}")

    # Create QProcess for non-blocking execution with parent to prevent GC
    process = QProcess(parent)

    def on_finished(exit_code, exit_status):
        if exit_code == 0 and exit_status == QProcess.ExitStatus.NormalExit:
            msg = f"Fan profile '{profile_name}' applied successfully"
            print(msg)
            if callback:
                callback(True, msg)
        else:
            error_msg = f"Error applying fan profile '{profile_name}' (exit code: {exit_code})"
            stderr = process.readAllStandardError().data().decode('utf-8', errors='ignore')
            if stderr:
                error_msg += f": {stderr}"
            print(error_msg)
            if callback:
                callback(False, error_msg)
        # Clean up process after finished
        process.deleteLater()

    process.finished.connect(on_finished)

    # Start the process with pkexec
    process.start("pkexec", ["nbfc", "config", "-a", profile_name])

    return None