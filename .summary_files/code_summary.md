Project Root: /home/sam/github/Ryzen-Master-Commander
Project Structure:
```
.
|-- .gitignore
|-- LICENSE
|-- README.md
|-- bin
    |-- ryzen-master-commander
    |-- ryzen-master-commander-helper
|-- builds
    |-- ryzen-master-commander
        |-- PKGBUILD
        |-- ryzen-master-commander-1.0.0-1-any.pkg.tar.zst
        |-- ryzen-master-commander-1.0.0.tar.gz
        |-- tdp_profiles
|-- img
    |-- icon.png
    |-- main_ui.png
    |-- profile_saver.png
    |-- ui_w_graph.png
|-- install_fan_profile.sh
|-- manifest.in
|-- polkit
    |-- com.merrythieves.ryzenadj.policy
|-- rebuild_install.sh
|-- requirements.txt
|-- ryzen_master_commander
    |-- __init__.py
    |-- app
        |-- __init__.py
        |-- fan_profile_editor.py
        |-- graphs.py
        |-- main_window.py
        |-- profile_manager.py
        |-- system_utils.py
    |-- main.py
|-- setup.py
|-- share
    |-- applications
        |-- ryzen-master-commander.desktop
    |-- icons
        |-- hicolor
            |-- 128x128
                |-- apps
                    |-- ryzen-master-commander.png
            |-- 16x16
                |-- apps
                    |-- ryzen-master-commander.png
            |-- 32x32
                |-- apps
                    |-- ryzen-master-commander.png
            |-- 64x64
                |-- apps
                    |-- ryzen-master-commander.png
    |-- ryzen-master-commander
        |-- fan_profiles
            |-- GPD_Win_Mini2.json
        |-- tdp_profiles
            |-- WinMini-Balanced.json
            |-- WinMini-BatterySaver.json
            |-- WinMini-MaxPerformance.json

```

---
## File: polkit/com.merrythieves.ryzenadj.policy

```policy
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC
 "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig>
  <vendor>Ryzen Master Commander</vendor>
  <vendor_url>https://github.com/sam1am/Ryzen-Master-Commander</vendor_url>

  <action id="com.merrythieves.ryzenadj">
    <description>Run ryzenadj with elevated privileges</description>
    <message>Authentication is required to change processor settings</message>
    <icon_name>cpu</icon_name>
    <defaults>
      <allow_any>auth_admin_keep</allow_any>
      <allow_inactive>auth_admin_keep</allow_inactive>
      <allow_active>yes</allow_active>
    </defaults>
    <annotate key="org.freedesktop.policykit.exec.path">/usr/bin/ryzenadj</annotate>
    <annotate key="org.freedesktop.policykit.exec.allow_gui">true</annotate>
  </action>
  
  <action id="com.merrythieves.nbfc">
    <description>Run nbfc with elevated privileges</description>
    <message>Authentication is required to control fan settings</message>
    <icon_name>fan</icon_name>
    <defaults>
      <allow_any>auth_admin_keep</allow_any>
      <allow_inactive>auth_admin_keep</allow_inactive>
      <allow_active>yes</allow_active>
    </defaults>
    <annotate key="org.freedesktop.policykit.exec.path">/usr/bin/nbfc</annotate>
    <annotate key="org.freedesktop.policykit.exec.allow_gui">true</annotate>
  </action>
</policyconfig>
```
---
## File: ryzen_master_commander/__init__.py

```py

```
---
## File: ryzen_master_commander/app/__init__.py

```py
"""App package for Ryzen Master Commander."""
```
---
## File: ryzen_master_commander/app/fan_profile_editor.py

```py
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
    def __init__(self):
        super().__init__()
        
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
        
        # Load a default profile if available
        if self.profiles_list:
            self.on_profile_selected(0)
    
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
```
---
## File: ryzen_master_commander/app/graphs.py

```py
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPen
import pyqtgraph as pg
import numpy as np

class CombinedGraph(QWidget):
    def __init__(self, parent=None):
        super(CombinedGraph, self).__init__(parent)
        self.temperature_readings = []
        self.fanspeed_readings = []
        self.time_points = []
        
        # Configure global PyQtGraph settings
        pg.setConfigOptions(antialias=True)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create PlotWidget - use transparent background to respect app theme
        self.plot_widget = pg.PlotWidget(background=None)
        layout.addWidget(self.plot_widget)
        
        # Setup the plot
        self.setup_plot()
        
    def setup_plot(self):
        # Enable grid
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Define colors for temperature and fan speed
        temp_color = '#3498db'  # Blue
        fan_color = '#e74c3c'   # Red
        
        # Setup left Y axis (Temperature)
        left_axis = self.plot_widget.getAxis('left')
        left_axis.setLabel(text='Temperature', units='°C', color=temp_color)
        left_axis.setPen(pg.mkPen(color=temp_color, width=2))
        left_axis.setTextPen(temp_color)
        
        # Setup right Y axis (Fan Speed)
        self.plot_widget.showAxis('right') # Explicitly tell PlotItem to show the right axis
        right_axis = self.plot_widget.getAxis('right')
        right_axis.setLabel(text='Fan Speed', units='%', color=fan_color) # Set label
        right_axis.setPen(pg.mkPen(color=fan_color, width=2))
        right_axis.setTextPen(fan_color)
        right_axis.setStyle(showValues=True) # Ensure tick values are shown
        # Add tick values for fan speed (0%, 25%, 50%, 75%, 100%)
        right_axis.setTicks([[(0, '0%'), (25, '25%'), (50, '50%'), (75, '75%'), (100, '100%')]])
        
        # Setup bottom X axis (Time)
        bottom_axis = self.plot_widget.getAxis('bottom')
        bottom_axis.setLabel('Time (seconds)')
        
        # Create ViewBox for Fan Speed
        self.fan_view = pg.ViewBox()
        self.plot_widget.scene().addItem(self.fan_view) # Add to scene
        right_axis.linkToView(self.fan_view) # Link the axis to this view
        self.fan_view.setXLink(self.plot_widget.getViewBox()) # Link X axes
        # Fix fan speed range to 0-100%
        self.fan_view.setYRange(0, 100, padding=0)
        
        # Create temperature plot
        self.temp_curve = pg.PlotCurveItem(
            pen=pg.mkPen(color=temp_color, width=3),
            symbolBrush=temp_color,
            symbolPen='w',
            symbol='o',
            symbolSize=7,
            name="Temperature"
        )
        self.plot_widget.addItem(self.temp_curve)
        
        # Create fan speed plot (on secondary y-axis)
        self.fan_curve = pg.PlotCurveItem(
            pen=pg.mkPen(color=fan_color, width=3),
            symbolBrush=fan_color,
            symbolPen='w',
            symbol='s',
            symbolSize=7,
            name="Fan Speed"
        )
        self.fan_view.addItem(self.fan_curve) # Add to the fan_view
        
        # Create legend and position it below the graph
        self.legend = pg.LegendItem() # Create instance without initial offset
        self.legend.setParentItem(self.plot_widget.graphicsItem()) # Parent is PlotItem
        # Anchor top-center of legend to bottom-center of plot item, with a 10px downward offset
        self.legend.anchor(itemPos=(0.5, 0), parentPos=(0.5, 1), offset=(0, 10)) 
        
        # Add items to legend
        self.legend.addItem(self.temp_curve, "Temperature (°C)")
        # Create a proxy item for fan speed for the legend
        self.fan_proxy = pg.PlotDataItem( # Use PlotDataItem for legend proxy if curve itself is complex
            pen=pg.mkPen(color=fan_color, width=3),
            symbolBrush=fan_color,
            symbolPen='w',
            symbol='s',
            symbolSize=7
        )
        self.legend.addItem(self.fan_proxy, "Fan Speed (%)")
        
        # Connect resize event to update views and ensure sync
        self.plot_widget.getViewBox().sigResized.connect(self.updateViews)
        
        # Update views initially
        self.updateViews()
        
    def updateViews(self):
        # Keep the views in sync when resizing
        # The main ViewBox (getViewBox()) controls the geometry of the plot area
        # The fan_view needs to match this geometry
        main_vb_rect = self.plot_widget.getViewBox().sceneBoundingRect()
        self.fan_view.setGeometry(main_vb_rect)
        
        # This call is important to sync the X-axis state (range, etc.)
        # from the main ViewBox to the fan_view's X-axis.
        self.fan_view.linkedViewChanged(self.plot_widget.getViewBox(), self.fan_view.XAxis)
        
    def update_data(self, temperature, fan_speed):
        if temperature == "n/a" and fan_speed == "n/a":
            return
        
        # Add current time (seconds since start)
        if not self.time_points:
            self.time_points.append(0)
        else:
            self.time_points.append(self.time_points[-1] + 1)
        
        # Keep only the last 60 points
        if len(self.time_points) > 60:
            self.time_points = self.time_points[-60:]
        
        # Update temperature data
        if temperature != "n/a":
            self.temperature_readings.append(float(temperature))
        else:
            # If no reading, use the previous value or zero
            self.temperature_readings.append(self.temperature_readings[-1] if self.temperature_readings else 0)
            
        # Keep only the last 60 points
        if len(self.temperature_readings) > 60:
            self.temperature_readings = self.temperature_readings[-60:]
        
        # Update fan speed data
        if fan_speed != "n/a":
            self.fanspeed_readings.append(float(fan_speed))
        else:
            # If no reading, use the previous value or zero
            self.fanspeed_readings.append(self.fanspeed_readings[-1] if self.fanspeed_readings else 0)
            
        # Keep only the last 60 points
        if len(self.fanspeed_readings) > 60:
            self.fanspeed_readings = self.fanspeed_readings[-60:]
        
        # Ensure all data arrays have the same length matching the shortest one
        min_len = min(len(self.time_points), len(self.temperature_readings), len(self.fanspeed_readings))
        if min_len == 0: # Avoid issues if no data yet
            time_data, temp_data, fan_data = [], [], []
        else:
            time_data = self.time_points[-min_len:]
            temp_data = self.temperature_readings[-min_len:]
            fan_data = self.fanspeed_readings[-min_len:]
        
        # Update plot data
        self.temp_curve.setData(time_data, temp_data)
        self.fan_curve.setData(time_data, fan_data)
        if self.fan_proxy: # Check if fan_proxy exists before setting data
             self.fan_proxy.setData(time_data, fan_data)  # Update the legend proxy
        
        # Auto-scale temperature y-axis
        if temp_data:
            max_temp = max(temp_data) + 5
            min_temp = max(0, min(temp_data) - 5)
            # Ensure max_temp is at least a reasonable value like 50, and min_temp is not negative
            self.plot_widget.setYRange(min_temp, max(max_temp, 50.0)) 
        else:
            self.plot_widget.setYRange(0, 50) # Default if no data

        # Make sure the fan scale stays 0-100
        self.fan_view.setYRange(0, 100, padding=0)
        
        # Update ViewBox to ensure correct sizing and linking
        self.updateViews()
```
---
## File: ryzen_master_commander/app/main_window.py

```py
import os
import subprocess
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                            QSlider, QComboBox, QGroupBox, QCheckBox, QPushButton, 
                            QRadioButton, QStatusBar, QFrame, QSplitter, QApplication)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont

from ryzen_master_commander.app.graphs import CombinedGraph
from ryzen_master_commander.app.system_utils import get_system_readings, apply_tdp_settings
from ryzen_master_commander.app.profile_manager import ProfileManager
from ryzen_master_commander.app.fan_profile_editor import FanProfileEditor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize instance variables
        self.profile_manager = ProfileManager()
        self.fan_speed_adjustment_delay = None
        self.graph_visible = True
        
        # Set up the UI
        self.init_ui()
        
        # Set auto control by default
        self.radio_auto_control.setChecked(True)
        self.set_auto_control()
        
        # Start reading system values
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.update_readings)
        self.refresh_timer.start(5000)  # Initial refresh every 5 seconds
        
        # Schedule first reading
        QTimer.singleShot(1000, self.update_readings)
    
    def init_ui(self):
        # Set window properties
        self.setWindowTitle("Ryzen Master Commander")
        self.resize(900, 700)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for graphs and controls
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter, 1)
        
        # Create graph widget
        self.graph_widget = QWidget()
        graph_layout = QVBoxLayout(self.graph_widget)
        
        # Add combined graph
        graph_group = QGroupBox("System Monitoring")
        graph_inner_layout = QVBoxLayout(graph_group)
        self.combined_graph = CombinedGraph(self)
        graph_inner_layout.addWidget(self.combined_graph)
        graph_layout.addWidget(graph_group)
        
        splitter.addWidget(self.graph_widget)
        
        # Controls container
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        splitter.addWidget(controls_container)
        
        # Set initial sizes for splitter
        splitter.setSizes([380, 320])
        
        # Create TDP Controls group box
        tdp_group = QGroupBox("TDP Controls")
        tdp_layout = QVBoxLayout(tdp_group)
        self.profile_manager.create_widgets(tdp_group)
        controls_layout.addWidget(tdp_group)
        
        # Create Fan Controls group box
        fan_group = QGroupBox("Fan Controls")
        fan_layout = QVBoxLayout(fan_group)
        
        # Fan profile editor button
        fan_profile_editor_btn = QPushButton("Fan Profile Editor")
        fan_profile_editor_btn.clicked.connect(self.open_fan_profile_editor)
        fan_layout.addWidget(fan_profile_editor_btn)
        
        # Refresh interval slider
        refresh_label = QLabel("Refresh Interval (seconds):")
        fan_layout.addWidget(refresh_label)
        
        self.refresh_slider = QSlider(Qt.Horizontal)
        self.refresh_slider.setRange(1, 30)
        self.refresh_slider.setValue(5)
        self.refresh_slider.setTickPosition(QSlider.TicksBelow)
        self.refresh_slider.setTickInterval(5)
        self.refresh_slider.valueChanged.connect(self.update_refresh_interval)
        fan_layout.addWidget(self.refresh_slider)
        
        refresh_value_layout = QHBoxLayout()
        refresh_value_layout.addWidget(QLabel("1"))
        refresh_value_layout.addStretch()
        refresh_value_layout.addWidget(QLabel("30"))
        fan_layout.addLayout(refresh_value_layout)
        
        # Fan control mode
        control_mode_group = QGroupBox("Fan Control Mode")
        control_mode_layout = QHBoxLayout(control_mode_group)
        
        self.radio_auto_control = QRadioButton("Auto Control")
        self.radio_auto_control.toggled.connect(self.set_auto_control)
        control_mode_layout.addWidget(self.radio_auto_control)
        
        self.radio_manual_control = QRadioButton("Manual Control")
        self.radio_manual_control.toggled.connect(self.set_manual_control)
        control_mode_layout.addWidget(self.radio_manual_control)
        
        fan_layout.addWidget(control_mode_group)
        
        # Manual fan speed slider
        manual_control_label = QLabel("Manual Fan Speed (%):")
        fan_layout.addWidget(manual_control_label)
        
        self.fan_speed_control_slider = QSlider(Qt.Horizontal)
        self.fan_speed_control_slider.setRange(0, 100)
        self.fan_speed_control_slider.setValue(50)
        self.fan_speed_control_slider.setTickPosition(QSlider.TicksBelow)
        self.fan_speed_control_slider.setTickInterval(10)
        self.fan_speed_control_slider.valueChanged.connect(self.delayed_fan_setting)
        self.fan_speed_control_slider.setEnabled(False)  # Disabled by default (auto mode)
        fan_layout.addWidget(self.fan_speed_control_slider)
        
        fan_speed_value_layout = QHBoxLayout()
        fan_speed_value_layout.addWidget(QLabel("0%"))
        fan_speed_value_layout.addStretch()
        self.manual_control_value_label = QLabel("50%")
        fan_speed_value_layout.addWidget(self.manual_control_value_label)
        fan_speed_value_layout.addStretch()
        fan_speed_value_layout.addWidget(QLabel("100%"))
        fan_layout.addLayout(fan_speed_value_layout)
        
        # Toggle graph button
        toggle_graph_btn = QPushButton("Hide Graphs")
        toggle_graph_btn.clicked.connect(self.toggle_graph)
        self.toggle_graph_btn = toggle_graph_btn
        fan_layout.addWidget(toggle_graph_btn)
        
        fan_layout.addStretch()
        controls_layout.addWidget(fan_group)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status bar widgets
        self.temp_label = QLabel("Temperature: --°C")
        self.fan_speed_label = QLabel("Fan Speed: --%")
        self.current_profile_label = QLabel("Current Profile: --")
        
        # Add separators between status items
        self.status_bar.addPermanentWidget(self.temp_label)
        self.status_bar.addPermanentWidget(QFrame(frameShape=QFrame.VLine))
        self.status_bar.addPermanentWidget(self.fan_speed_label)
        self.status_bar.addPermanentWidget(QFrame(frameShape=QFrame.VLine))
        self.status_bar.addPermanentWidget(self.current_profile_label)
    
    def update_readings(self):
        temperature, fan_speed, current_profile = get_system_readings()
        
        # Update status bar labels
        self.temp_label.setText(f"Temperature: {temperature}°C")
        self.fan_speed_label.setText(f"Fan Speed: {fan_speed}%")
        self.current_profile_label.setText(f"Current Profile: {current_profile}")
        
        # Update combined graph
        self.combined_graph.update_data(temperature, fan_speed)
    
    def update_refresh_interval(self):
        refresh_seconds = self.refresh_slider.value() * 1000  # Convert to milliseconds
        self.refresh_timer.setInterval(refresh_seconds)
    
    def delayed_fan_setting(self):
        # Cancel previous timer if it exists
        if hasattr(self, 'delay_timer') and self.delay_timer.isActive():
            self.delay_timer.stop()
        
        # Create a new timer to apply the setting after a delay
        self.delay_timer = QTimer(self)
        self.delay_timer.timeout.connect(self.apply_fan_speed)
        self.delay_timer.setSingleShot(True)
        self.delay_timer.start(1000)  # 1 second delay
        
        # Update the displayed value immediately
        slider_value = self.fan_speed_control_slider.value()
        self.manual_control_value_label.setText(f"{slider_value}%")
    
    def apply_fan_speed(self):
        slider_value = self.fan_speed_control_slider.value()
        try:
            subprocess.run(['pkexec', 'nbfc', 'set', '-s', str(slider_value)])
        except subprocess.CalledProcessError as e:
            print(f"Error setting fan speed: {e}")
    
    def set_auto_control(self):
        if self.radio_auto_control.isChecked():
            try:
                subprocess.run(['pkexec', 'nbfc', 'set', '-a'])
            except subprocess.CalledProcessError as e:
                print(f"Error setting automatic fan control: {e}")
            self.fan_speed_control_slider.setEnabled(False)
    
    def set_manual_control(self):
        if self.radio_manual_control.isChecked():
            self.fan_speed_control_slider.setEnabled(True)
    
    def toggle_graph(self):
        if self.graph_visible:
            self.graph_widget.hide()
            self.toggle_graph_btn.setText("Show Graphs")
        else:
            self.graph_widget.show()
            self.toggle_graph_btn.setText("Hide Graphs")
        
        self.graph_visible = not self.graph_visible
    
    def open_fan_profile_editor(self):
        self.fan_editor = FanProfileEditor()
        self.fan_editor.show()
```
---
## File: ryzen_master_commander/app/profile_manager.py

```py
import json
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
                           QComboBox, QLineEdit, QCheckBox, QPushButton, QInputDialog)
from PyQt5.QtCore import pyqtSlot, Qt

from ryzen_master_commander.app.system_utils import apply_tdp_settings

class ProfileManager:
    def __init__(self):
        # Check multiple potential profile directories
        potential_dirs = [
            "./tdp_profiles",  # Development location
            "/usr/share/ryzen-master-commander/tdp_profiles",  # System-wide installation
            os.path.expanduser("~/.local/share/ryzen-master-commander/tdp_profiles")  # User installation
        ]
        
        # Use the first directory that exists
        self.profiles_directory = next((d for d in potential_dirs if os.path.exists(d)), "./tdp_profiles")
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
```
---
## File: ryzen_master_commander/app/system_utils.py

```py
import subprocess
import re
import os

def get_system_readings():
    try:
        output = subprocess.check_output(['nbfc', 'status', '-a'], text=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to execute 'nbfc status -a': {e}")
        return "n/a", "n/a", "n/a"
    except FileNotFoundError:
        print("nbfc command not found. Make sure NoteBook FanControl is installed.")
        return "n/a", "n/a", "n/a"

    temperature_match = re.search(r'Temperature\s+:\s+(\d+\.?\d*)', output)
    fan_speed_match = re.search(r'Current Fan Speed\s+:\s+(\d+\.?\d*)', output)
    current_profile_match = re.search(r'Selected Config Name\s+:\s+(.*?)$', output, re.MULTILINE)

    temperature = temperature_match.group(1) if temperature_match else "n/a"
    fan_speed = fan_speed_match.group(1) if fan_speed_match else "n/a"
    current_profile = current_profile_match.group(1) if current_profile_match else "n/a"
    return temperature, fan_speed, current_profile

def apply_tdp_settings(current_profile):
    if current_profile:
        command = ['pkexec', 'ryzenadj']
        for key, value in current_profile.items():
            if key in ["fast-limit", "slow-limit"]:
                command.extend([f'--{key}={value * 1000}'])
            elif key == "slow-time":
                command.extend([f'--{key}={value * 1000}'])
            elif key not in ["name", "max-performance", "power-saving"]:
                command.extend([f'--{key}={value}'])
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
        subprocess.run(['pkexec', 'nbfc', 'config', '-a', profile_name], check=True)
        return True, f"Fan profile '{profile_name}' applied successfully"
    except Exception as e:
        return False, f"Error applying fan profile: {str(e)}"
```
---
## File: ryzen_master_commander/main.py

```py
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ryzen_master_commander.app.main_window import MainWindow

def main():
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Ryzen Master Commander")
    
    # Set application icon
    icon_paths = [
        "/usr/share/icons/hicolor/128x128/apps/ryzen-master-commander.png",
        "./share/icons/hicolor/128x128/apps/ryzen-master-commander.png",
        "./img/icon.png"
    ]
    
    for path in icon_paths:
        if os.path.exists(path):
            app.setWindowIcon(QIcon(path))
            break
    
    # Configure PyQtGraph for dark/light mode
    try:
        import pyqtgraph as pg
        # Check for KDE dark mode
        is_dark_mode = False
        
        if os.environ.get('XDG_CURRENT_DESKTOP') == 'KDE':
            try:
                result = subprocess.run(
                    ["kreadconfig5", "--group", "General", "--key", "ColorScheme"],
                    capture_output=True, text=True
                )
                is_dark_mode = "dark" in result.stdout.strip().lower()
            except Exception as e:
                print(f"Error detecting KDE theme: {e}")
        
        # Another approach for dark mode detection
        if not is_dark_mode:
            try:
                from PyQt5.QtGui import QPalette
                app_palette = app.palette()
                # If text is lighter than background, we're likely in dark mode
                bg_color = app_palette.color(QPalette.Window).lightness()
                text_color = app_palette.color(QPalette.WindowText).lightness()
                is_dark_mode = text_color > bg_color
            except Exception as e:
                print(f"Error using palette for theme detection: {e}")
        
        print(f"Dark mode detected: {is_dark_mode}")
        
        # Set PyQtGraph theme
        if is_dark_mode:
            pg.setConfigOption('background', 'k')
            pg.setConfigOption('foreground', 'w')
        else:
            pg.setConfigOption('background', 'w')
            pg.setConfigOption('foreground', 'k')
    except ImportError:
        print("PyQtGraph not available")
    
    # Create and show the main window
    main_window = MainWindow()
    main_window.show()
    
    # Start the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
```
---
## File: setup.py

```py
from setuptools import setup, find_packages
import os

# Get the absolute path to the directory where setup.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define proper paths based on setup.py location
fan_profiles_path = os.path.join(BASE_DIR, 'share/ryzen-master-commander/fan_profiles')
tdp_profiles_path = os.path.join(BASE_DIR, 'share/ryzen-master-commander/tdp_profiles')

# Create data files structure properly
# Add this to your data_files list in setup.py
data_files = [
    ('share/applications', [os.path.join(BASE_DIR, 'share/applications/ryzen-master-commander.desktop')]),
    ('share/ryzen-master-commander/fan_profiles', 
     [os.path.join(fan_profiles_path, file) for file in os.listdir(fan_profiles_path) if os.path.isfile(os.path.join(fan_profiles_path, file))]),
    ('share/ryzen-master-commander/tdp_profiles', 
     [os.path.join(tdp_profiles_path, file) for file in os.listdir(tdp_profiles_path) if os.path.isfile(os.path.join(tdp_profiles_path, file))]),
    ('bin', [os.path.join(BASE_DIR, 'bin/ryzen-master-commander'), 
             os.path.join(BASE_DIR, 'bin/ryzen-master-commander-helper')]),
    # Add this line for the polkit policy
    ('share/polkit-1/actions', [os.path.join(BASE_DIR, 'polkit/com.merrythieves.ryzenadj.policy')]),
]

# Add icon files
for size in ['16x16', '32x32', '64x64', '128x128']:
    icon_dir = os.path.join(BASE_DIR, f'share/icons/hicolor/{size}/apps')
    if os.path.exists(icon_dir):
        data_files.append((f'share/icons/hicolor/{size}/apps', 
                          [os.path.join(icon_dir, 'ryzen-master-commander.png')]))

setup(
    name="ryzen-master-commander",
    version="1.0.1",
    author="sam1am",
    author_email="noreply@merrythieves.com",
    description="TDP and fan control for AMD Ryzen processors",
    url="https://github.com/sam1am/Ryzen-Master-Commander",
    packages=['ryzen_master_commander', 'ryzen_master_commander.app'],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    install_requires=[
        "PyQt5",
        "pyqtgraph",
        "numpy",
        "Pillow",
        "pystray",
    ],
    python_requires=">=3.6",
    data_files=data_files,
    entry_points={
        'console_scripts': [
            'ryzen-master-commander=ryzen_master_commander.main:main',
        ],
    },
)
```
---
## File: share/applications/ryzen-master-commander.desktop

```desktop
[Desktop Entry]
Name=Ryzen Master Commander
Comment=AMD Ryzen TDP and Fan Control
GenericName=Hardware Control
Exec=ryzen-master-commander %U
Icon=ryzen-master-commander
Terminal=false
Type=Application
Categories=System;Settings;HardwareSettings;
Keywords=AMD;Ryzen;TDP;Fan;Control;
StartupNotify=true
StartupWMClass=ryzen-master-commander
Path=/usr/share/ryzen-master-commander
```
---
