import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
                           QComboBox, QLineEdit, QCheckBox, QPushButton, QInputDialog)
from PyQt6.QtCore import pyqtSlot, Qt

from ryzen_master_commander.app.system_utils import apply_tdp_settings

class ProfileManager:
    def __init__(self):
        # Check multiple potential profile directories
        potential_dirs = [
            "./tdp_profiles",  # Development location
            "/usr/share/ryzen-master-commander/tdp_profiles",  # System-wide installation
            os.path.expanduser("~/.local/share/ryzen-master-commander/tdp_profiles")  # User installation
        ]
        
        # Use the first directory that exists AND contains profiles
        self.profiles_directory = None
        for dir_path in potential_dirs:
            if os.path.exists(dir_path):
                # Check if directory contains any json files
                if any(f.endswith('.json') for f in os.listdir(dir_path)):
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
        
        # Profile selection
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("Performance Profile:"))
        
        self.profile_dropdown = QComboBox()
        # Explicitly connect with the correct type
        self.profile_dropdown.currentIndexChanged.connect(self.on_profile_select)
        profile_layout.addWidget(self.profile_dropdown)
        layout.addLayout(profile_layout)
        
        # TDP settings
        # Fast limit
        fast_limit_layout = QHBoxLayout()
        fast_limit_layout.addWidget(QLabel("Fast Limit (W):"))
        self.fast_limit_entry = QLineEdit()
        fast_limit_layout.addWidget(self.fast_limit_entry)
        layout.addLayout(fast_limit_layout)
        
        # Slow limit
        slow_limit_layout = QHBoxLayout()
        slow_limit_layout.addWidget(QLabel("Slow Limit (W):"))
        self.slow_limit_entry = QLineEdit()
        slow_limit_layout.addWidget(self.slow_limit_entry)
        layout.addLayout(slow_limit_layout)
        
        # Slow time
        slow_time_layout = QHBoxLayout()
        slow_time_layout.addWidget(QLabel("Slow Time (s):"))
        self.slow_time_entry = QLineEdit()
        slow_time_layout.addWidget(self.slow_time_entry)
        layout.addLayout(slow_time_layout)
        
        # Tctl temp
        tctl_temp_layout = QHBoxLayout()
        tctl_temp_layout.addWidget(QLabel("Tctl Temp (°C):"))
        self.tctl_temp_entry = QLineEdit()
        tctl_temp_layout.addWidget(self.tctl_temp_entry)
        layout.addLayout(tctl_temp_layout)
        
        # APU skin temp
        apu_skin_temp_layout = QHBoxLayout()
        apu_skin_temp_layout.addWidget(QLabel("APU Skin Temp (°C):"))
        self.apu_skin_temp_entry = QLineEdit()
        apu_skin_temp_layout.addWidget(self.apu_skin_temp_entry)
        layout.addLayout(apu_skin_temp_layout)
        
        # Performance options
        performance_group = QGroupBox("Performance Mode")
        performance_layout = QHBoxLayout(performance_group)
        
        self.max_performance_var = QCheckBox("Max Performance")
        self.max_performance_var.stateChanged.connect(
            lambda: self.power_saving_var.setChecked(False) if self.max_performance_var.isChecked() else None
        )
        performance_layout.addWidget(self.max_performance_var)
        
        self.power_saving_var = QCheckBox("Power Saving")
        self.power_saving_var.stateChanged.connect(
            lambda: self.max_performance_var.setChecked(False) if self.power_saving_var.isChecked() else None
        )
        performance_layout.addWidget(self.power_saving_var)
        
        layout.addWidget(performance_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        apply_tdp_button = QPushButton("Apply TDP Settings")
        apply_tdp_button.clicked.connect(lambda: apply_tdp_settings(self.current_profile))
        button_layout.addWidget(apply_tdp_button)
        
        save_profile_button = QPushButton("Save Profile")
        save_profile_button.clicked.connect(self.save_profile)
        button_layout.addWidget(save_profile_button)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        # Populate profile dropdown
        self.update_profile_dropdown()
        
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
                            print(f"Warning: Profile '{file}' missing required 'name' field")
                            profile["name"] = os.path.splitext(file)[0]  # Use filename as name
                        
                        profiles.append(profile)
                        print(f"Successfully loaded profile: {profile['name']}")
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
            if self.profile_dropdown.currentIndex() == -1 and self.profile_dropdown.count() > 0:
                self.profile_dropdown.setCurrentIndex(0)

    # Fixed method to properly handle the signal
    def on_profile_select(self, index):
        """Handle profile selection from dropdown"""
        if index < 0 or not self.cached_profiles or index >= len(self.cached_profiles):
            return
            
        selected_profile = self.cached_profiles[index]
        self.current_profile = selected_profile
        
        # Update the entries with profile values
        self.fast_limit_entry.setText(str(self.current_profile["fast-limit"]))
        self.slow_limit_entry.setText(str(self.current_profile["slow-limit"]))
        self.slow_time_entry.setText(str(self.current_profile["slow-time"]))
        self.tctl_temp_entry.setText(str(self.current_profile["tctl-temp"]))
        self.apu_skin_temp_entry.setText(str(self.current_profile["apu-skin-temp"]))
        self.max_performance_var.setChecked(self.current_profile["max-performance"])
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
                "slow-time": int(self.slow_time_entry.text()),
                "tctl-temp": int(self.tctl_temp_entry.text()),
                "apu-skin-temp": int(self.apu_skin_temp_entry.text()),
                "max-performance": self.max_performance_var.isChecked(),
                "power-saving": self.power_saving_var.isChecked()
            }
            
            # Save profile to file
            with open(os.path.join(self.profiles_directory, f"{profile_name}.json"), "w") as f:
                json.dump(profile, f, indent=2)
            
            # Update cached profiles
            self.cached_profiles = self.load_profiles()
            
            # Update dropdown with new profile
            self.update_profile_dropdown()
            
            # Select the new profile
            index = self.profile_dropdown.findText(profile_name)
            if index >= 0:
                self.profile_dropdown.setCurrentIndex(index)