import json
import os
import subprocess
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QComboBox,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QInputDialog,
    QWidget,
    QVBoxLayout,
)
from PyQt6.QtCore import pyqtSlot, Qt, QProcess

from src.app.system_utils import apply_tdp_settings


class ProfileManager:
    def __init__(self):
        # Check multiple potential profile directories
        potential_dirs = [
            "./tdp_profiles",  # Development location
            "/usr/share/ryzen-master-commander/tdp_profiles",  # System-wide installation
            os.path.expanduser(
                "~/.local/share/ryzen-master-commander/tdp_profiles"
            ),  # User installation
        ]

        # Use the first directory that exists AND contains profiles
        self.profiles_directory = None
        for dir_path in potential_dirs:
            if os.path.exists(dir_path):
                # Check if directory contains any json files
                if any(f.endswith(".json") for f in os.listdir(dir_path)):
                    self.profiles_directory = dir_path
                    break

        # Fallback to default if no valid directory found
        if not self.profiles_directory:
            self.profiles_directory = "./tdp_profiles"

        print(f"Using profiles from: {self.profiles_directory}")

        self.current_profile = None
        self.cached_profiles = self.load_profiles()

    def create_widgets(self, parent):
        self.parent = parent
        layout = parent.layout()

        # Main TDP settings - SIDE BY SIDE in a HBox
        power_controls_layout = QHBoxLayout()
        
        # Average power draw - LEFT SIDE
        avg_power_group = QGroupBox("Avg Power (W)")
        avg_power_layout = QVBoxLayout(avg_power_group)
        self.slow_limit_entry = QLineEdit()
        self.slow_limit_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slow_limit_entry.setStyleSheet("font-size: 18px; font-weight: bold; padding: 8px;")
        # Connect to change event for auto-apply
        self.slow_limit_entry.editingFinished.connect(self.auto_apply_basic_settings)
        avg_power_layout.addWidget(self.slow_limit_entry)
        power_controls_layout.addWidget(avg_power_group)
        
        # Boost power draw - RIGHT SIDE
        boost_power_group = QGroupBox("Boost Power (W)")
        boost_power_layout = QVBoxLayout(boost_power_group)
        self.fast_limit_entry = QLineEdit()
        self.fast_limit_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fast_limit_entry.setStyleSheet("font-size: 18px; font-weight: bold; padding: 8px;")
        # Connect to change event for auto-apply
        self.fast_limit_entry.editingFinished.connect(self.auto_apply_basic_settings)
        boost_power_layout.addWidget(self.fast_limit_entry)
        power_controls_layout.addWidget(boost_power_group)
        
        # Add the power controls to the main layout
        layout.addLayout(power_controls_layout)
        
        # Collapsible Advanced Settings Section
        self.advanced_container = QWidget()
        advanced_container_layout = QVBoxLayout(self.advanced_container)
        advanced_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with toggle button for advanced section
        advanced_header = QHBoxLayout()
        advanced_toggle_btn = QPushButton("▶ Advanced Settings")
        advanced_toggle_btn.setStyleSheet("text-align: left; padding-left: 5px;")
        advanced_toggle_btn.setFlat(True)
        advanced_toggle_btn.clicked.connect(self.toggle_advanced_section)
        advanced_header.addWidget(advanced_toggle_btn)
        advanced_container_layout.addLayout(advanced_header)
        
        # Advanced settings content (hidden by default)
        self.advanced_content = QWidget()
        advanced_content_layout = QVBoxLayout(self.advanced_content)
        advanced_content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Slow time
        slow_time_layout = QHBoxLayout()
        slow_time_layout.addWidget(QLabel("Boost Duration (s):"))
        self.slow_time_entry = QLineEdit()
        slow_time_layout.addWidget(self.slow_time_entry)
        advanced_content_layout.addLayout(slow_time_layout)

        # Tctl temp
        tctl_temp_layout = QHBoxLayout()
        tctl_temp_layout.addWidget(QLabel("CPU Temp Limit (°C):"))
        self.tctl_temp_entry = QLineEdit()
        tctl_temp_layout.addWidget(self.tctl_temp_entry)
        advanced_content_layout.addLayout(tctl_temp_layout)

        # APU skin temp
        apu_skin_temp_layout = QHBoxLayout()
        apu_skin_temp_layout.addWidget(QLabel("APU Skin Temp (°C):"))
        self.apu_skin_temp_entry = QLineEdit()
        apu_skin_temp_layout.addWidget(self.apu_skin_temp_entry)
        advanced_content_layout.addLayout(apu_skin_temp_layout)

        # Performance options
        performance_group = QGroupBox("Performance Mode")
        performance_layout = QHBoxLayout(performance_group)

        self.max_performance_var = QCheckBox("Max Performance")
        self.max_performance_var.stateChanged.connect(
            lambda: (
                self.power_saving_var.setChecked(False)
                if self.max_performance_var.isChecked()
                else None
            )
        )
        performance_layout.addWidget(self.max_performance_var)

        self.power_saving_var = QCheckBox("Power Saving")
        self.power_saving_var.stateChanged.connect(
            lambda: (
                self.max_performance_var.setChecked(False)
                if self.power_saving_var.isChecked()
                else None
            )
        )
        performance_layout.addWidget(self.power_saving_var)
        advanced_content_layout.addWidget(performance_group)
        
        # Apply button in advanced section
        apply_tdp_button = QPushButton("Apply Advanced Settings")
        apply_tdp_button.clicked.connect(lambda: self.apply_current_settings(True))
        advanced_content_layout.addWidget(apply_tdp_button)
        
        # Add advanced content to container
        advanced_container_layout.addWidget(self.advanced_content)
        
        # Hide advanced content by default
        self.advanced_content.hide()
        
        # Store the toggle button for later reference
        self.advanced_toggle_btn = advanced_toggle_btn
        
        # Add advanced container to main layout
        layout.addWidget(self.advanced_container)
        
        # Collapsible Profile Management Box
        self.profile_container = QWidget()
        profile_container_layout = QVBoxLayout(self.profile_container)
        profile_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with toggle button for profile section
        profile_header = QHBoxLayout()
        profile_toggle_btn = QPushButton("▶ Profile Management")
        profile_toggle_btn.setStyleSheet("text-align: left; padding-left: 5px;")
        profile_toggle_btn.setFlat(True)
        profile_toggle_btn.clicked.connect(self.toggle_profile_section)
        profile_header.addWidget(profile_toggle_btn)
        profile_container_layout.addLayout(profile_header)
        
        # Profile content (hidden by default)
        self.profile_content = QWidget()
        profile_content_layout = QVBoxLayout(self.profile_content)
        profile_content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Profile selection row
        profile_selection_layout = QHBoxLayout()
        profile_selection_layout.addWidget(QLabel("Load:"))
        self.profile_dropdown = QComboBox()
        self.profile_dropdown.currentIndexChanged.connect(self.on_profile_select)
        profile_selection_layout.addWidget(self.profile_dropdown)
        profile_content_layout.addLayout(profile_selection_layout)
        
        # Save profile button
        save_profile_button = QPushButton("Save Current Settings as Profile")
        save_profile_button.clicked.connect(self.save_profile)
        profile_content_layout.addWidget(save_profile_button)
        
        # Add profile content to container
        profile_container_layout.addWidget(self.profile_content)
        
        # Hide profile content by default
        self.profile_content.hide()
        
        # Store the toggle button for later reference
        self.profile_toggle_btn = profile_toggle_btn
        
        # Add profile container to main layout
        layout.addWidget(self.profile_container)
        layout.addStretch()

        # Populate profile dropdown
        self.update_profile_dropdown()

    def toggle_advanced_section(self):
        """Toggle visibility of advanced settings section"""
        if self.advanced_content.isVisible():
            self.advanced_content.hide()
            self.advanced_toggle_btn.setText("▶ Advanced Settings")
        else:
            self.advanced_content.show()
            self.advanced_toggle_btn.setText("▼ Advanced Settings")

    def toggle_profile_section(self):
        """Toggle visibility of profile management section"""
        if self.profile_content.isVisible():
            self.profile_content.hide()
            self.profile_toggle_btn.setText("▶ Profile Management")
        else:
            self.profile_content.show()
            self.profile_toggle_btn.setText("▼ Profile Management")

    def auto_apply_basic_settings(self):
        """Auto-apply basic settings when values change"""
        # Only auto-apply if advanced settings are hidden
        if not self.advanced_content.isVisible():
            try:
                # Create basic profile with just the essential settings
                basic_profile = {
                    "fast-limit": int(self.fast_limit_entry.text()),
                    "slow-limit": int(self.slow_limit_entry.text()),
                }
                apply_tdp_settings(basic_profile)
                print("Auto-applied basic TDP settings")
            except (ValueError, TypeError) as e:
                print(f"Error auto-applying settings: {e}")

    def apply_current_settings(self, include_advanced=False):
        """Apply current TDP settings"""
        try:
            # Create basic profile with just the basic settings
            profile = {
                "fast-limit": int(self.fast_limit_entry.text()),
                "slow-limit": int(self.slow_limit_entry.text()),
            }
            
            # If advanced settings should be included
            if include_advanced:
                profile.update({
                    "slow-time": int(self.slow_time_entry.text()),
                    "tctl-temp": int(self.tctl_temp_entry.text()),
                    "apu-skin-temp": int(self.apu_skin_temp_entry.text()),
                    "max-performance": self.max_performance_var.isChecked(),
                    "power-saving": self.power_saving_var.isChecked(),
                })
            
            # Apply the settings
            apply_tdp_settings(profile)
        except (ValueError, TypeError) as e:
            print(f"Error applying settings: {e}")

    def load_profiles(self):
        profiles = []
        if not os.path.exists(self.profiles_directory):
            os.makedirs(self.profiles_directory)
            print(f"Created profiles directory: {self.profiles_directory}")

        # Debug: list all files in the directory
        files = os.listdir(self.profiles_directory)
        print(f"Found {len(files)} files in profiles directory: {files}")

        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(self.profiles_directory, file)
                try:
                    with open(file_path, "r") as f:
                        file_content = f.read()
                        profile = json.loads(file_content)

                        # Validate profile has required fields
                        if "name" not in profile:
                            print(
                                f"Warning: Profile '{file}' missing required 'name' field"
                            )
                            profile["name"] = os.path.splitext(file)[
                                0
                            ]  # Use filename as name

                        profiles.append(profile)
                        print(
                            f"Successfully loaded profile: {profile['name']}"
                        )
                except json.JSONDecodeError as e:
                    print(f"Error loading profile '{file}': {e}")
                    print(f"Content causing error: {file_content[:100]}...")
                except Exception as e:
                    print(f"Unexpected error loading profile '{file}': {e}")

        print(f"Loaded {len(profiles)} profiles total")
        return profiles  # Return the loaded profiles

    def update_profile_dropdown(self):
        if self.cached_profiles:
            self.profile_dropdown.clear()
            for profile in self.cached_profiles:
                self.profile_dropdown.addItem(profile["name"])

            # Select first profile by default if none is selected
            if (
                self.profile_dropdown.currentIndex() == -1
                and self.profile_dropdown.count() > 0
            ):
                self.profile_dropdown.setCurrentIndex(0)

    # Fixed method to properly handle the signal
    def on_profile_select(self, index):
        """Handle profile selection from dropdown"""
        if (
            index < 0
            or not self.cached_profiles
            or index >= len(self.cached_profiles)
        ):
            return

        selected_profile = self.cached_profiles[index]
        self.current_profile = selected_profile

        # Update the entries with profile values
        self.fast_limit_entry.setText(str(self.current_profile["fast-limit"]))
        self.slow_limit_entry.setText(str(self.current_profile["slow-limit"]))
        self.slow_time_entry.setText(str(self.current_profile["slow-time"]))
        self.tctl_temp_entry.setText(str(self.current_profile["tctl-temp"]))
        self.apu_skin_temp_entry.setText(
            str(self.current_profile["apu-skin-temp"])
        )
        self.max_performance_var.setChecked(
            self.current_profile["max-performance"]
        )
        self.power_saving_var.setChecked(self.current_profile["power-saving"])

        # Apply the profile
        apply_tdp_settings(self.current_profile)

    def save_profile(self):
        profile_name, ok = QInputDialog.getText(
            self.parent, "Save Profile", "Enter profile name:"
        )

        if ok and profile_name:
            profile = {
                "name": profile_name,
                "fast-limit": int(self.fast_limit_entry.text()),
                "slow-limit": int(self.slow_limit_entry.text()),
                # Include advanced settings if they're set
                "slow-time": int(self.slow_time_entry.text()) if self.slow_time_entry.text() else 0,
                "tctl-temp": int(self.tctl_temp_entry.text()) if self.tctl_temp_entry.text() else 0,
                "apu-skin-temp": int(self.apu_skin_temp_entry.text()) if self.apu_skin_temp_entry.text() else 0,
                "max-performance": self.max_performance_var.isChecked(),
                "power-saving": self.power_saving_var.isChecked(),
            }

            # Profile file path
            profile_path = os.path.join(self.profiles_directory, f"{profile_name}.json")
            
            # Try to save using a helper script with elevated privileges
            try:
                # First attempt to save directly - this works for user directories
                self.save_profile_with_privileges(profile, profile_path)
                
                # Update cached profiles
                self.cached_profiles = self.load_profiles()

                # Update dropdown with new profile
                self.update_profile_dropdown()

                # Select the new profile
                index = self.profile_dropdown.findText(profile_name)
                if index >= 0:
                    self.profile_dropdown.setCurrentIndex(index)
                    
            except Exception as e:
                print(f"Error saving profile: {e}")
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self.parent,
                    "Error Saving Profile",
                    f"Failed to save profile: {e}\n\nMake sure you have permission to write to {self.profiles_directory}"
                )

    def save_profile_with_privileges(self, profile, profile_path):
        """Save profile with elevated privileges if needed"""
        try:
            # First try to save directly
            with open(profile_path, "w") as f:
                json.dump(profile, f, indent=2)
                print(f"Saved profile to {profile_path}")
        except PermissionError:
            # If permission denied, use pkexec
            print(f"Permission denied, trying with elevated privileges...")

            # Create a temporary file in /tmp (which should be writable)
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                temp_path = temp_file.name
                json.dump(profile, temp_file, indent=2)

            # Create QProcess for non-blocking execution
            process = QProcess()

            def on_cp_finished(exit_code, exit_status):
                if exit_code == 0 and exit_status == QProcess.ExitStatus.NormalExit:
                    # Now set permissions
                    chmod_process = QProcess()

                    def on_chmod_finished(chmod_exit_code, chmod_exit_status):
                        if chmod_exit_code == 0 and chmod_exit_status == QProcess.ExitStatus.NormalExit:
                            print(f"Successfully saved profile with elevated privileges")
                            # Clean up temp file
                            os.unlink(temp_path)
                        else:
                            print(f"Failed to set permissions on {profile_path}")
                            os.unlink(temp_path)

                    chmod_process.finished.connect(on_chmod_finished)
                    chmod_process.start("pkexec", ["chmod", "644", profile_path])
                else:
                    stderr = process.readAllStandardError().data().decode('utf-8', errors='ignore')
                    error_msg = f"Failed to save with elevated privileges: {stderr}"
                    print(error_msg)
                    # Clean up temp file on error
                    os.unlink(temp_path)
                    raise Exception(error_msg)

            process.finished.connect(on_cp_finished)
            process.start("pkexec", ["cp", temp_path, profile_path])