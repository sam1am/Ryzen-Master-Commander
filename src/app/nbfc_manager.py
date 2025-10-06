import os
import subprocess
from PyQt6.QtWidgets import (
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QListWidget,
    QPushButton,
    QLabel,
)
from PyQt6.QtCore import QProcess


class NBFCManager:
    """Class to manage NBFC (Notebook Fan Control) setup and configuration"""

    @staticmethod
    def is_nbfc_installed():
        """Check if NBFC is installed"""
        try:
            subprocess.run(
                ["nbfc", "--version"], capture_output=True, text=True
            )
            return True
        except FileNotFoundError:
            return False

    @staticmethod
    def is_nbfc_running():
        """Check if NBFC service is running"""
        try:
            result = subprocess.run(
                ["nbfc", "status"], capture_output=True, text=True
            )
            return "ERROR: connect()" not in result.stderr
        except Exception:
            return False

    @staticmethod
    def is_nbfc_configured():
        """Check if NBFC is configured by looking for config file"""
        try:
            # First check if the service can start
            result = subprocess.run(
                ["sudo", "nbfc", "start"], capture_output=True, text=True
            )
            # If there's an error about missing config file, it's not configured
            return (
                "ERROR: /etc/nbfc/nbfc.json: No such file or directory"
                not in result.stderr
            )
        except Exception:
            # If we can't run the command, assume it's not configured
            return False

    @staticmethod
    def update_nbfc_configs(parent=None, callback=None):
        """Download available NBFC configs silently using QProcess.

        Args:
            parent: Parent widget
            callback: Optional callback function(success) to call when complete
        """
        process = QProcess()

        def on_finished(exit_code, exit_status):
            success = exit_code == 0 and exit_status == QProcess.ExitStatus.NormalExit
            if callback:
                callback(success)

        process.finished.connect(on_finished)
        process.start("pkexec", ["nbfc", "update"])

        return None

    @staticmethod
    def get_recommended_config():
        """Get the recommended config for this system"""
        try:
            result = subprocess.run(
                ["pkexec", "nbfc", "config", "-r"],
                capture_output=True,
                text=True,
            )

            stdout = result.stdout.strip()
            # print("NBFC config -r output with pkexec:")
            # print(repr(stdout))

            lines = stdout.split("\n")
            for line in lines:
                # Skip lines that are likely part of the header/info text
                if (
                    line
                    and "error" not in line.lower()
                    and "found" not in line.lower()
                    and "config" not in line.lower()
                    and "recommend" not in line.lower()
                    and not line.startswith("-")
                    and not line.startswith("[")
                ):

                    config_name = line.strip()
                    if config_name:
                        print(f"Found possible config name: {config_name}")
                        return config_name

            print("No recommended nbfc config found.")
            return None
        except Exception as e:
            print(f"Error while getting recommended config: {str(e)}")
            return None

    @staticmethod
    def get_available_configs():
        """Get list of all available NBFC configs"""
        configs = []
        config_dirs = ["/usr/share/nbfc/configs", "/etc/nbfc/configs"]

        for directory in config_dirs:
            if os.path.exists(directory):
                for file in os.listdir(directory):
                    if file.endswith(".json"):
                        configs.append(file[:-5])  # Remove .json extension

        return sorted(configs)

    @staticmethod
    def set_nbfc_config(config_name, parent=None, callback=None):
        """Set NBFC to use the specified config using QProcess.

        Args:
            config_name: Name of the config to set
            parent: Parent widget
            callback: Optional callback function(success) to call when complete
        """
        process = QProcess()

        def on_finished(exit_code, exit_status):
            stderr = process.readAllStandardError().data().decode('utf-8', errors='ignore')
            success = exit_code == 0 and exit_status == QProcess.ExitStatus.NormalExit and "ERROR" not in stderr
            if callback:
                callback(success)

        process.finished.connect(on_finished)
        process.start("pkexec", ["nbfc", "config", "-s", config_name])

        return None

    @staticmethod
    def start_nbfc_service(parent=None, callback=None):
        """Start the NBFC service using QProcess.

        Args:
            parent: Parent widget
            callback: Optional callback function(success) to call when complete
        """
        process = QProcess()

        def on_finished(exit_code, exit_status):
            # Check if service is actually running after the command
            success = NBFCManager.is_nbfc_running()
            if callback:
                callback(success)

        process.finished.connect(on_finished)
        process.start("pkexec", ["nbfc", "start"])

        return None

    @staticmethod
    def setup_nbfc(parent=None):
        """Complete NBFC setup process with minimal user interaction"""
        if not NBFCManager.is_nbfc_installed():
            QMessageBox.critical(
                parent,
                "NBFC Not Installed",
                "Notebook Fan Control (NBFC) is not installed on this system.\n"
                "Please install it using your package manager.",
            )
            return False

        # If NBFC is already running, we're good
        if NBFCManager.is_nbfc_running():
            return True
        print("NBFC is not running, attempting to start it...")

        # Try to start the service first
        if NBFCManager.start_nbfc_service(parent):
            return True

        print("NBFC service failed to start, checking configuration...")
        # If still not running, update configs silently
        NBFCManager.update_nbfc_configs()

        # Try to get and apply recommended config automatically
        recommended = NBFCManager.get_recommended_config()

        if recommended:
            # Apply recommended config silently
            if NBFCManager.set_nbfc_config(recommended):
                print(f"Applied recommended config: {recommended}")
                return NBFCManager.start_nbfc_service()

        # Only show dialog if we couldn't find or apply a recommended config
        print(
            "No recommended config found or failed to apply, showing selection dialog..."
        )
        config_dialog = ConfigSelectionDialog(parent)
        if (
            config_dialog.exec() == QDialog.DialogCode.Accepted
            and config_dialog.selected_config
        ):
            if NBFCManager.set_nbfc_config(config_dialog.selected_config):
                return NBFCManager.start_nbfc_service()

        return False


class ConfigSelectionDialog(QDialog):
    """Dialog for selecting an NBFC configuration"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select NBFC Configuration")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self.selected_config = None

        layout = QVBoxLayout(self)

        # Instructions with more detailed guidance
        instructions = QLabel(
            "Select your model or the nearest match you can find.\n\n"
            "If your model is not supported, check the nbfc-linux project at\n"
            "https://github.com/nbfc-linux/ for assistance."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Config list
        self.config_list = QListWidget()
        layout.addWidget(self.config_list)

        # Populate list
        configs = NBFCManager.get_available_configs()
        for config in configs:
            self.config_list.addItem(config)

        # Buttons
        button_layout = QVBoxLayout()
        select_button = QPushButton("Select")
        select_button.clicked.connect(self.accept_selection)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(select_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def accept_selection(self):
        """Accept the selected configuration"""
        current_item = self.config_list.currentItem()
        if current_item:
            self.selected_config = current_item.text()
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Selection Required",
                "Please select a configuration from the list.",
            )
