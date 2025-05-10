import os
import glob
import json
import subprocess
import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                            QLabel, QComboBox, QPushButton, QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class FanProfileEditor(QMainWindow):
    def __init__(self, current_nbfc_profile_name=None):
        super().__init__()
        self.current_nbfc_profile_name_from_main = current_nbfc_profile_name
        
        self.points = [(20, 0), (40, 30), (60, 60), (80, 100)]  # Default curve points (temp, fan_speed)
        self.current_config = None  # Store the full config for saving
        self.hover_point = None
        self.drag_point = None
        
        # NBFC configs directory
        self.nbfc_configs_dir = "/usr/share/nbfc/configs/"
        
        # User configs directory for saving custom profiles
        self.user_configs_dir = os.path.expanduser("/usr/share/nbfc/configs/")
        if not os.path.exists(self.user_configs_dir):
            os.makedirs(self.user_configs_dir, exist_ok=True)
        
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("NBFC Fan Profile Editor")
        self.resize(800, 600)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("NBFC Fan Profile Editor")
        title_label.setAlignment(Qt.AlignCenter)
        font = title_label.font()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        main_layout.addWidget(title_label)
        
        # Available profiles frame
        profiles_group = QGroupBox("Available Profiles")
        profiles_layout = QHBoxLayout(profiles_group)
        
        profiles_layout.addWidget(QLabel("Select Profile:"))
        
        self.profiles_list = self.get_available_profiles()
        self.profile_dropdown = QComboBox()
        self.profile_dropdown.addItems(self.profiles_list)
        self.profile_dropdown.currentIndexChanged.connect(self.on_profile_selected)
        profiles_layout.addWidget(self.profile_dropdown, 1)
        
        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self.load_selected_profile)
        profiles_layout.addWidget(load_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_selected_profile)
        profiles_layout.addWidget(apply_btn)
        
        main_layout.addWidget(profiles_group)
        
        # Matplotlib figure for plotting
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('motion_notify_event', self.on_hover)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        main_layout.addWidget(self.canvas)
        
        # Controls for curve manipulation
        controls_group = QGroupBox("Curve Controls")
        controls_layout = QHBoxLayout(controls_group)
        
        add_point_btn = QPushButton("Add Point")
        add_point_btn.clicked.connect(self.add_point)
        controls_layout.addWidget(add_point_btn)
        
        remove_point_btn = QPushButton("Remove Point")
        remove_point_btn.clicked.connect(self.remove_point)
        controls_layout.addWidget(remove_point_btn)
        
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_curve)
        controls_layout.addWidget(reset_btn)
        
        main_layout.addWidget(controls_group)
        
        # Save profile section
        save_group = QGroupBox("Save Profile")
        save_layout = QHBoxLayout(save_group)
        
        save_layout.addWidget(QLabel("Profile Name:"))
        
        self.custom_profile_name = QLineEdit("MyCustomProfile")
        save_layout.addWidget(self.custom_profile_name, 1)
        
        save_btn = QPushButton("Save Custom Profile")
        save_btn.clicked.connect(self.save_custom_profile)
        save_layout.addWidget(save_btn)
        
        main_layout.addWidget(save_group)
        
        # Initialize plot
        self.update_plot()
        
        # Determine initial profile to select in the dropdown
        initial_profile_to_set = None
        if self.current_nbfc_profile_name_from_main and \
           self.current_nbfc_profile_name_from_main != "n/a" and \
           self.current_nbfc_profile_name_from_main != "--":
            if self.current_nbfc_profile_name_from_main in self.profiles_list:
                initial_profile_to_set = self.current_nbfc_profile_name_from_main

        if initial_profile_to_set:
            try:
                index = self.profiles_list.index(initial_profile_to_set)
                self.profile_dropdown.setCurrentIndex(index)
            except ValueError: # Should not happen if logic above is correct
                if self.profiles_list: # Fallback to first if something unexpected occurs
                    self.profile_dropdown.setCurrentIndex(0)
        elif self.profiles_list: # Fallback if no current profile passed/found or it's "n/a"
            self.profile_dropdown.setCurrentIndex(0)
        # If self.profile_dropdown.setCurrentIndex() was called and changed the index,
        # the on_profile_selected -> load_selected_profile chain will be triggered.
    
    def get_available_profiles(self):
        """Get list of available NBFC profiles"""
        # Check system profiles
        system_profiles = glob.glob(os.path.join(self.nbfc_configs_dir, "*.json"))
        
        # Extract names
        profile_names = [os.path.splitext(os.path.basename(p))[0] for p in system_profiles]
        
        return sorted(profile_names)
    
    def on_profile_selected(self, index):
        """Handle profile selection from dropdown"""
        if index >= 0:
            self.load_selected_profile()
    
    def load_selected_profile(self):
        """Load the currently selected profile"""
        profile_name = self.profile_dropdown.currentText()
        if not profile_name:
            return
        self.custom_profile_name.setText(profile_name) # Pre-fill save name field
            
        # Try user directory first
        user_path = os.path.join(self.user_configs_dir, f"{profile_name}.json")
        system_path = os.path.join(self.nbfc_configs_dir, f"{profile_name}.json")
        
        if os.path.exists(user_path):
            file_path = user_path
        elif os.path.exists(system_path):
            file_path = system_path
        else:
            QMessageBox.critical(self, "Error", f"Profile '{profile_name}' not found")
            return
            
        try:
            # Load the NBFC config
            with open(file_path, 'r') as f:
                config = json.load(f)
            
            # Store the full config for later saving    
            self.current_config = config
            
            # Extract fan curve points
            if 'FanConfigurations' in config and len(config['FanConfigurations']) > 0:
                fan_config = config['FanConfigurations'][0]
                curve_points = []
                
                # Check for TemperatureThresholds
                if 'TemperatureThresholds' in fan_config and fan_config['TemperatureThresholds']:
                    for threshold in fan_config['TemperatureThresholds']:
                        if 'UpThreshold' in threshold and 'FanSpeed' in threshold:
                            curve_points.append((threshold['UpThreshold'], threshold['FanSpeed']))
                
                # Check for FanSpeedPercentageOverrides - different format types
                if 'FanSpeedPercentageOverrides' in fan_config and fan_config['FanSpeedPercentageOverrides']:
                    overrides = fan_config['FanSpeedPercentageOverrides']
                    
                    # Check if using Temperature/FanSpeed format
                    if overrides and 'Temperature' in overrides[0] and 'FanSpeed' in overrides[0]:
                        for override in overrides:
                            curve_points.append((override['Temperature'], override['FanSpeed']))
                    
                    # Check if using FanSpeedPercentage/FanSpeedValue format
                    elif overrides and 'FanSpeedPercentage' in overrides[0] and 'FanSpeedValue' in overrides[0]:
                        # For this format, we need additional info about min/max speed values
                        # We'll create a mapping of temps based on position in array
                        min_temp = 30
                        max_temp = 90
                        step = (max_temp - min_temp) / (len(overrides) - 1) if len(overrides) > 1 else 10
                        
                        for i, override in enumerate(overrides):
                            temp = min_temp + i * step
                            curve_points.append((temp, override['FanSpeedPercentage']))
                
                if curve_points:
                    # Use the extracted points
                    self.points = curve_points
                    self.update_plot()
                    # QMessageBox.information(self, "Success", f"Loaded fan curve from '{profile_name}'")
                else:
                    # No points found, create default
                    self.reset_curve()
                    QMessageBox.information(self, "Note", "No fan curve found, using default curve")
            else:
                QMessageBox.warning(self, "Warning", "Selected profile doesn't contain fan configuration")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load profile: {str(e)}")
            self.reset_curve()
    
    def apply_selected_profile(self):
        """Apply the selected profile using nbfc command"""
        profile_name = self.profile_dropdown.currentText()
        if not profile_name:
            QMessageBox.warning(self, "Warning", "Please select a profile first")
            return
            
        try:
            subprocess.run(['pkexec', 'nbfc', 'config', '-a', profile_name], check=True)
            QMessageBox.information(self, "Success", f"Applied fan profile '{profile_name}'")
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: pkexec nbfc config -a '{profile_name}'\nError: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
    
    def save_custom_profile(self):
        """Save the current fan curve as a custom NBFC profile with root privileges"""
        name = self.custom_profile_name.text()
        if not name:
            QMessageBox.warning(self, "Warning", "Please enter a profile name")
            return
                
        # Start with a template or use current loaded config as base
        if self.current_config:
            config = self.current_config.copy()
            # Update name
            config["NotebookModel"] = name
        else:
            # Create a basic NBFC config
            config = {
                "NotebookModel": name,
                "Author": "Ryzen Master Commander",
                "EcPollInterval": 5000,
                "ReadWriteWords": False,
                "CriticalTemperature": 85,
                "FanConfigurations": [
                    {
                        "ReadRegister": 122,
                        "WriteRegister": 122,
                        "MinSpeedValue": 0,
                        "MaxSpeedValue": 255,
                        "ResetRequired": True,
                        "FanSpeedResetValue": 0,
                        "FanDisplayName": "Fan"
                    }
                ]
            }
        
        # Make sure FanConfigurations exists
        if "FanConfigurations" not in config or not config["FanConfigurations"]:
            config["FanConfigurations"] = [{"ReadRegister": 122, "WriteRegister": 122}]
        
        # Create temperature thresholds from points
        config["FanConfigurations"][0]["TemperatureThresholds"] = [
            {
                "UpThreshold": int(temp),
                "DownThreshold": max(0, int(temp) - 5),  # 5 degree hysteresis
                "FanSpeed": float(speed)
            }
            for temp, speed in sorted(self.points, key=lambda p: p[0])
        ]
        
        try:
            # First save to a temporary file in the user's home directory
            temp_dir = os.path.expanduser("~/.config/ryzen-master-commander/temp")
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = os.path.join(temp_dir, f"{name}.json")
            
            with open(temp_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Use pkexec to copy the file to the system directory
            target_file = f"/usr/share/nbfc/configs/{name}.json"
            
            # Execute cp with pkexec to copy with root privileges
            subprocess.run([
                'pkexec', 'cp', temp_file, target_file
            ], check=True)
            
            QMessageBox.information(self, "Success", f"Saved profile to {target_file}")
            
            # Update the profile list
            self.refresh_ui()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save profile: {str(e)}")

    def refresh_ui(self):
        """Refresh the profile list in the UI"""
        # Get updated profile list
        self.profiles_list = self.get_available_profiles()
        
        # Update dropdown
        self.profile_dropdown.clear()
        self.profile_dropdown.addItems(self.profiles_list)
    
    def update_plot(self):
        self.ax.clear()
        
        # Sort points by temperature (x-axis)
        sorted_points = sorted(self.points, key=lambda p: p[0])
        self.points = sorted_points
        
        # Extract x and y values
        temps, speeds = zip(*self.points) if self.points else ([], [])
        
        # Plot the curve
        self.ax.plot(temps, speeds, 'b-', marker='o', markersize=8)
        
        # Highlight hover point
        if self.hover_point is not None:
            idx = self.hover_point
            self.ax.plot(self.points[idx][0], self.points[idx][1], 'ro', markersize=10)
        
        # Set labels and limits
        self.ax.set_xlabel('Temperature (°C)')
        self.ax.set_ylabel('Fan Speed (%)')
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(0, 100)
        self.ax.grid(True)
        self.ax.set_title('Fan Speed Curve')
        
        # Draw the plot
        self.fig.tight_layout()
        self.canvas.draw()
    
    def on_click(self, event):
        if event.inaxes != self.ax:
            return
        
        # Check if clicking near existing point
        for i, (x, y) in enumerate(self.points):
            if abs(event.xdata - x) < 3 and abs(event.ydata - y) < 3:
                if event.button == 1:  # Left click to drag
                    self.drag_point = i
                    return
                elif event.button == 3:  # Right click to delete
                    if len(self.points) > 2:  # Keep at least 2 points
                        self.points.pop(i)
                        self.update_plot()
                    else:
                        QMessageBox.information(self, "Can't Remove", "Fan curve must have at least 2 points")
                    return
        
        # If double click and not on point, add new point
        if event.dblclick:
            self.points.append((max(0, min(100, event.xdata)), max(0, min(100, event.ydata))))
            self.update_plot()
    
    def on_hover(self, event):
        if event.inaxes != self.ax:
            self.hover_point = None
            return
        
        # Check if dragging a point
        if self.drag_point is not None:
            # Update point position
            temp = max(0, min(100, event.xdata))
            speed = max(0, min(100, event.ydata))
            self.points[self.drag_point] = (temp, speed)
            self.update_plot()
            return
        
        # Otherwise check for hover
        old_hover = self.hover_point
        self.hover_point = None
        for i, (x, y) in enumerate(self.points):
            if abs(event.xdata - x) < 3 and abs(event.ydata - y) < 3:
                self.hover_point = i
                break
        
        if old_hover != self.hover_point:
            self.update_plot()
    
    def on_release(self, event):
        self.drag_point = None
    
    def add_point(self):
        if not self.points:
            self.reset_curve()
            return
            
        # Add a point in the middle
        temps = [p[0] for p in self.points]
        min_temp, max_temp = min(temps), max(temps)
        new_temp = (min_temp + max_temp) / 2
        
        # Find where to insert
        for i, p in enumerate(self.points):
            if p[0] > new_temp:
                prev_speed = self.points[i-1][1]
                next_speed = p[1]
                new_speed = (prev_speed + next_speed) / 2
                self.points.insert(i, (new_temp, new_speed))
                break
        
        self.update_plot()
    
    def remove_point(self):
        if self.hover_point is not None and len(self.points) > 2:
            self.points.pop(self.hover_point)
            self.hover_point = None
            self.update_plot()
        else:
            QMessageBox.information(self, "Remove Point", 
                                    "Hover over a point to select it first, or fan curve must have at least 2 points")
    
    def reset_curve(self):
        self.points = [(20, 0), (40, 30), (60, 60), (80, 100)]  # Default curve
        self.update_plot()