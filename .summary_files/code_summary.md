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
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import os
import subprocess
from tkinter import filedialog, messagebox
import numpy as np
import glob

class FanProfileEditor:
    def __init__(self, parent):
        self.parent = parent
        self.points = [(20, 0), (40, 30), (60, 60), (80, 100)]  # Default curve points (temp, fan_speed)
        self.current_config = None  # Store the full config for saving
        
        # NBFC configs directory
        self.nbfc_configs_dir = "/usr/share/nbfc/configs/"
        
        # User configs directory for saving custom profiles
        self.user_configs_dir = os.path.expanduser("/usr/share/nbfc/configs/")
        if not os.path.exists(self.user_configs_dir):
            os.makedirs(self.user_configs_dir, exist_ok=True)
        
        # Main frame
        self.main_frame = ttk.Frame(parent)
        self.main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(self.main_frame, text="NBFC Fan Profile Editor", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Available profiles frame
        profiles_frame = ttk.LabelFrame(self.main_frame, text="Available Profiles")
        profiles_frame.pack(fill=X, pady=10)
        
        # Profile selection
        self.profiles_list = self.get_available_profiles()
        profile_label = ttk.Label(profiles_frame, text="Select Profile:")
        profile_label.pack(side=LEFT, padx=5, pady=5)
        
        self.profile_var = ttk.StringVar()
        profile_combobox = ttk.Combobox(profiles_frame, textvariable=self.profile_var, 
                                        values=self.profiles_list, width=40)
        profile_combobox.pack(side=LEFT, fill=X, expand=True, padx=5, pady=5)
        profile_combobox.bind("<<ComboboxSelected>>", self.on_profile_selected)
        
        load_btn = ttk.Button(profiles_frame, text="Load", command=self.load_selected_profile)
        load_btn.pack(side=LEFT, padx=5, pady=5)
        
        apply_btn = ttk.Button(profiles_frame, text="Apply", command=self.apply_selected_profile)
        apply_btn.pack(side=LEFT, padx=5, pady=5)
        
        # Create the figure and plot
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=BOTH, expand=True)
        
        # Connect mouse events
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('motion_notify_event', self.on_hover)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        
        # Active point for dragging
        self.hover_point = None
        self.drag_point = None
        
        # Add controls frame
        controls_frame = ttk.Frame(self.main_frame)
        controls_frame.pack(fill=X, pady=10)
        
        # Add point button
        add_point_btn = ttk.Button(controls_frame, text="Add Point", command=self.add_point)
        add_point_btn.pack(side=LEFT, padx=5)
        
        # Remove point button
        remove_point_btn = ttk.Button(controls_frame, text="Remove Point", command=self.remove_point)
        remove_point_btn.pack(side=LEFT, padx=5)
        
        # Reset button
        reset_btn = ttk.Button(controls_frame, text="Reset", command=self.reset_curve)
        reset_btn.pack(side=LEFT, padx=5)
        
        # Save frame
        save_frame = ttk.LabelFrame(self.main_frame, text="Save Profile")
        save_frame.pack(fill=X, pady=10)
        
        # Profile name entry
        name_label = ttk.Label(save_frame, text="Profile Name:")
        name_label.pack(side=LEFT, padx=5, pady=5)
        
        self.custom_profile_name = ttk.StringVar(value="MyCustomProfile")
        name_entry = ttk.Entry(save_frame, textvariable=self.custom_profile_name, width=30)
        name_entry.pack(side=LEFT, fill=X, expand=True, padx=5, pady=5)
        
        save_btn = ttk.Button(save_frame, text="Save Custom Profile", command=self.save_custom_profile)
        save_btn.pack(side=LEFT, padx=5, pady=5)
        
        # Initialize plot
        self.update_plot()
        
        # Load a default profile if available
        if self.profiles_list:
            self.profile_var.set(self.profiles_list[0])
    
    def get_available_profiles(self):
        """Get list of available NBFC profiles"""
        # Check system profiles
        system_profiles = glob.glob(os.path.join(self.nbfc_configs_dir, "*.json"))
        
        # Check user profiles
        # user_profiles = glob.glob(os.path.join(self.user_configs_dir, "*.json"))
        
        # Combine and extract names
        all_profiles = system_profiles
        profile_names = [os.path.splitext(os.path.basename(p))[0] for p in all_profiles]
        
        return sorted(profile_names)
    
    def on_profile_selected(self, event):
        """Handle profile selection from dropdown"""
        self.load_selected_profile()
    
    def load_selected_profile(self):
        """Load the currently selected profile"""
        profile_name = self.profile_var.get()
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
            messagebox.showerror("Error", f"Profile '{profile_name}' not found")
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
                    messagebox.showinfo("Success", f"Loaded fan curve from '{profile_name}'")
                else:
                    # No points found, create default
                    self.reset_curve()
                    messagebox.showinfo("Note", "No fan curve found, using default curve")
            else:
                messagebox.showwarning("Warning", "Selected profile doesn't contain fan configuration")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load profile: {str(e)}")
            self.reset_curve()
    
    def apply_selected_profile(self):
        """Apply the selected profile using nbfc command"""
        profile_name = self.profile_var.get()
        if not profile_name:
            messagebox.showwarning("Warning", "Please select a profile first")
            return
            
        try:
            # Use the correct command format, without including quotes in the string
            # subprocess handles spaces in arguments correctly when using a list
            subprocess.run(['pkexec', 'nbfc', 'config', '-a', profile_name], check=True)
            
            # For debugging, log the exact command
            print(f"Executing: pkexec nbfc config -a '{profile_name}'")
            
            messagebox.showinfo("Success", f"Applied fan profile '{profile_name}'")
        except subprocess.CalledProcessError as e:
            # Enhanced error message with the command that was run
            error_msg = f"Command failed: pkexec nbfc config -a '{profile_name}'\nError: {str(e)}"
            messagebox.showerror("Error", error_msg)
            
            # Try getting help output for debugging
            try:
                help_output = subprocess.check_output(['nbfc', 'config', '--help'], text=True)
                print(f"NBFC config help:\n{help_output}")
            except:
                pass
    
    def save_custom_profile(self):
        """Save the current fan curve as a custom NBFC profile with root privileges"""
        name = self.custom_profile_name.get()
        if not name:
            messagebox.showwarning("Warning", "Please enter a profile name")
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
            
            messagebox.showinfo("Success", f"Saved profile to {target_file}")
            
            # Update the profile list
            self.profiles_list = self.get_available_profiles()
            
            # Rather than trying to find the combobox widget directly, create a variable 
            # at initialization time to store it, or simply refresh the entire UI
            self.refresh_ui()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save profile: {str(e)}")

    def refresh_ui(self):
        """Refresh the profile list in the UI"""
        # Get updated profile list
        self.profiles_list = self.get_available_profiles()
        
        # Find all combobox widgets and update them
        for child in self.main_frame.winfo_children():
            if isinstance(child, ttk.Labelframe) and child.cget("text") == "Available Profiles":
                for widget in child.winfo_children():
                    if isinstance(widget, ttk.Combobox):
                        widget['values'] = self.profiles_list
                        return
    
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
                        messagebox.showinfo("Can't Remove", "Fan curve must have at least 2 points")
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
            messagebox.showinfo("Remove Point", "Hover over a point to select it first, or fan curve must have at least 2 points")
    
    def reset_curve(self):
        self.points = [(20, 0), (40, 30), (60, 60), (80, 100)]  # Default curve
        self.update_plot()
```
---
## File: ryzen_master_commander/app/graphs.py

```py
import ttkbootstrap as ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class TemperatureGraph:
    def __init__(self, root):
        self.root = root
        self.temperature_readings = []
        
        # Set matplotlib to not use its own window
        import matplotlib
        matplotlib.use('TkAgg')
        
        # Create figure with proper embedding settings
        self.fig, self.ax = plt.subplots(figsize=(6, 1.5))
        self.fig.patch.set_facecolor('none')  # Transparent background
        
        # Create canvas and explicitly set master
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        self.canvas.draw()
        plt.close(self.fig)  # Close the figure manager but keep the canvas

    def update_temperature(self, temperature):
        if temperature != "n/a":
            self.temperature_readings.append(float(temperature))
            self.temperature_readings = self.temperature_readings[-600:]
            self.ax.clear()
            self.ax.plot(self.temperature_readings, marker='o', color='b')
            self.ax.set_title('Temperature Over Time')
            self.ax.set_ylabel('Temperature (°C)')
            self.ax.set_xlabel('Reading')
            self.ax.grid(True)
            self.canvas.draw()

class FanSpeedGraph:
    def __init__(self, root):
        self.root = root
        self.fanspeed_readings = []
        self.fig, self.ax = plt.subplots(figsize=(6, 1.5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack()

    def update_fan_speed(self, fan_speed):
        if fan_speed != "n/a":
            self.fanspeed_readings.append(float(fan_speed))
            if len(self.fanspeed_readings) > 600:
                self.fanspeed_readings.pop(0)
            self.ax.clear()
            self.ax.plot(self.fanspeed_readings, marker='o', color='r')
            self.ax.set_title('Fan Speed Over Time')
            self.ax.set_ylabel('Fan Speed (%)')
            self.ax.set_xlabel('Reading')
            self.ax.set_ylim(0, 100)
            self.ax.grid(True)
            self.canvas.draw()
```
---
## File: ryzen_master_commander/app/main_window.py

```py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter.simpledialog import askstring
import os
import subprocess
from ryzen_master_commander.app.graphs import TemperatureGraph, FanSpeedGraph
from ryzen_master_commander.app.system_utils import get_system_readings
from ryzen_master_commander.app.profile_manager import ProfileManager
from ryzen_master_commander.app.fan_profile_editor import FanProfileEditor

class MainWindow:
    def __init__(self, root):
        self.root = root
        
        # The rest of your initialization code
        self.graph_visible = True
        self.graph_frame = None
        self.profile_manager = ProfileManager(self.root)
        self.fan_speed_adjustment_delay = None

        self.control_mode_var = ttk.StringVar(value='auto')

        # Create widgets in the provided root window
        self.create_widgets()
        self.set_auto_control()
        # Delay the first reading to allow window to appear
        self.root.after(1000, self.update_readings)

    def create_widgets(self):
        # Create main frame, canvas, and scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=ttk.BOTH, expand=True)

        canvas = ttk.Canvas(main_frame)
        canvas.pack(side=ttk.LEFT, fill=ttk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(main_frame, orient=ttk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=ttk.RIGHT, fill=ttk.Y)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        content_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=content_frame, anchor='nw')

        # Create a frame for the graph with a specific width
        self.graph_frame = ttk.Frame(content_frame, height=400,width=300)  # Set the desired width here
        self.graph_frame.pack_propagate(False)  # Prevent the frame from shrinking

        # Create temperature graph
        self.temperature_graph = TemperatureGraph(self.graph_frame)

        # Create fan speed graph
        self.fan_speed_graph = FanSpeedGraph(self.graph_frame)

        # Create temperature label
        self.temp_label = ttk.Label(content_frame, text="Temperature: ")
        self.temp_label.pack(pady=5)

        # Curent profile label
        self.current_profile_label = ttk.Label(content_frame, text="Current Profile: ")
        self.current_profile_label.pack(pady=5)

        # Create fan speed label
        self.fan_speed_label = ttk.Label(content_frame, text="Fan Speed: ")
        self.fan_speed_label.pack(pady=5)

        # Create a separator
        separator = ttk.Separator(content_frame, orient='horizontal')
        separator.pack(fill='x', pady=10)

        # Create a frame to center the content below the graph
        center_frame = ttk.Frame(content_frame)
        center_frame.pack(pady=10)

        # Create fan controls
        fan_controls_label = ttk.Label(center_frame, text="Fan Controls", font=("Helvetica", 14, "bold"))
        fan_controls_label.pack(pady=5)

        fan_profile_editor_btn = ttk.Button(center_frame, text="Fan Profile Editor", command=self.open_fan_profile_editor)
        fan_profile_editor_btn.pack(pady=10)

        refresh_label = ttk.Label(center_frame, text="Refresh Interval (seconds): ")
        refresh_label.pack(pady=5)
        self.refresh_slider = ttk.Scale(center_frame, from_=1, to_=30, orient='horizontal', length=300)
        self.refresh_slider.pack(pady=(0, 5))
        self.refresh_slider.set(5)

        manual_control_label = ttk.Label(center_frame, text="Manual Fan Speed (%): ")
        manual_control_label.pack(pady=5)
        self.fan_speed_control_slider = ttk.Scale(center_frame, from_=0, to_=100, orient='horizontal', length=300, command=self.delayed_fan_setting)
        self.fan_speed_control_slider.pack(pady=(0, 5))
        self.fan_speed_control_slider.set(50)

        self.manual_control_value_label = ttk.Label(center_frame, text="50%")
        self.manual_control_value_label.pack(pady=(0, 10))

        control_mode_frame = ttk.Frame(center_frame)
        control_mode_frame.pack(pady=5)
        self.radio_auto_control = ttk.Radiobutton(control_mode_frame, text='Auto Control', 
                                                value='auto', variable=self.control_mode_var, 
                                                command=self.set_auto_control)
        self.radio_auto_control.grid(row=0, column=0, padx=5)
        self.radio_manual_control = ttk.Radiobutton(control_mode_frame, text='Manual Control', 
                                                value='manual', variable=self.control_mode_var, 
                                                command=self.set_manual_control)
        self.radio_manual_control.grid(row=0, column=1, padx=5)

        # Create a button to toggle graph visibility
        self.graph_button = ttk.Button(content_frame, text="Show Graph", command=self.toggle_graph)
        self.graph_button.pack(pady=5)

        # Create TDP controls
        separator = ttk.Separator(center_frame, orient='horizontal')
        separator.pack(fill='x', pady=10)

        tdp_controls_label = ttk.Label(center_frame, text="TDP Controls", font=("Helvetica", 14, "bold"))
        tdp_controls_label.pack(pady=5)

        self.profile_manager.create_widgets(center_frame)
        # self.setup_system_tray()

    def update_readings(self):
        temperature, fan_speed, current_profile = get_system_readings()

        self.temp_label.config(text=f"Temperature: {temperature} °C")
        self.fan_speed_label.config(text=f"Fan Speed: {fan_speed}%")
        self.temperature_graph.update_temperature(temperature)
        self.fan_speed_graph.update_fan_speed(fan_speed)
        self.current_profile_label.config(text=f"Current Profile: {current_profile}")

        refresh_seconds = int(self.refresh_slider.get())
        self.root.after(refresh_seconds * 1000, self.update_readings)

    def delayed_fan_setting(self, value):
        if self.fan_speed_adjustment_delay is not None:
            self.root.after_cancel(self.fan_speed_adjustment_delay)
        self.fan_speed_adjustment_delay = self.root.after(1000, self.apply_fan_speed, value)

    def apply_fan_speed(self, value):
        slider_value = round(float(value))
        try:
            subprocess.run(['pkexec', 'nbfc', 'set', '-s', str(slider_value)])
            self.manual_control_value_label.config(text=f"{slider_value}%")
        except subprocess.CalledProcessError as e:
            print(f"Error setting fan speed: {e}")

    def open_fan_profile_editor(self):
        # Create a new top-level window
        editor_window = ttk.Toplevel(self.root)
        editor_window.title("Fan Profile Editor")
        editor_window.geometry("700x700")
        editor_window.transient(self.root)  # Make it transient to main window
        
        # Center the window
        window_width = 700
        window_height = 700
        screen_width = editor_window.winfo_screenwidth()
        screen_height = editor_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        editor_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Create the fan profile editor
        editor = FanProfileEditor(editor_window)


    def set_auto_control(self):
        self.current_control_mode = 'auto'
        try:
            subprocess.run(['pkexec', 'nbfc', 'set', '-a'])
        except subprocess.CalledProcessError as e:
            print(f"Error setting automatic fan control: {e}")
        self.fan_speed_control_slider.config(state='disabled')


    def set_manual_control(self):
        self.current_control_mode = 'manual'
        self.fan_speed_control_slider.config(state='normal')

    # def toggle_graph_visibility(self, frame):
    #     if frame.winfo_viewable():
    #         frame.pack_forget()
    #     else:
    #         frame.pack()

    def toggle_graph(self):
        # Get current window dimensions
        current_width = self.root.winfo_width()
        current_height = self.root.winfo_height()
        
        if self.graph_visible:
            # Hide graph
            self.graph_frame.pack_forget()
            self.graph_button.config(text="Show Graph")
            # Reduce window height by 300 pixels
            new_height = max(950, current_height - 300)  # Ensure minimum height of 950
            self.root.geometry(f"{current_width}x{new_height}")
        else:
            # Show graph
            self.graph_frame.pack(side=ttk.TOP, fill=ttk.BOTH, expand=True)
            self.graph_button.config(text="Hide Graph")
            # Increase window height by 300 pixels
            new_height = current_height + 300
            self.root.geometry(f"{current_width}x{new_height}")
        
        self.graph_visible = not self.graph_visible
        
        # Center the window after resizing
        # self.center_window_after_resize()

    
    def setup_system_tray(self):
        """Set up system tray icon for Linux desktop environments"""
        try:
            import pystray
            from PIL import Image, ImageDraw
            
            # Create a simple icon
            icon_image = Image.new('RGB', (64, 64), color = (0, 0, 0))
            d = ImageDraw.Draw(icon_image)
            d.rectangle((10, 10, 54, 54), fill=(0, 120, 220))
            
            def on_quit_clicked(icon, item):
                icon.stop()
                self.root.destroy()
                
            def on_show_clicked(icon, item):
                self.root.deiconify()
                
            # Create the menu
            menu = pystray.Menu(
                pystray.MenuItem('Show', on_show_clicked),
                pystray.MenuItem('Quit', on_quit_clicked)
            )
            
            # Create the icon
            self.tray_icon = pystray.Icon("RyzenMasterCommander", icon_image, "Ryzen Master Commander", menu)
            
            # Run the icon in a separate thread
            import threading
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            
            # Make window minimize to tray but don't auto-hide on startup
            # self.root.protocol('WM_DELETE_WINDOW', self.minimize_to_tray)
        except ImportError:
            print("pystray not available - system tray functionality disabled")
            
    # def minimize_to_tray(self):
    #     self.root.withdraw()

```
---
## File: ryzen_master_commander/app/profile_manager.py

```py
from ryzen_master_commander.app.system_utils import apply_tdp_settings
from tkinter.simpledialog import askstring
import ttkbootstrap as ttk
import json
import os

class ProfileManager:
    def __init__(self, root):
        self.root = root
        
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
        self.load_profiles()


    def create_widgets(self, content_frame):
        profile_frame = ttk.Frame(content_frame)
        profile_frame.pack(pady=5)

        profile_label = ttk.Label(profile_frame, text="Performance Profile: ")
        profile_label.grid(row=0, column=0, padx=5)

        self.profile_dropdown = ttk.Combobox(profile_frame, state="readonly")
        self.profile_dropdown.grid(row=0, column=1, padx=5)
        self.profile_dropdown.bind("<<ComboboxSelected>>", self.on_profile_select)

        tdp_frame = ttk.Frame(content_frame)
        tdp_frame.pack(pady=5)

        fast_limit_label = ttk.Label(tdp_frame, text="Fast Limit (W): ")
        fast_limit_label.grid(row=0, column=0, padx=5)
        self.fast_limit_entry = ttk.Entry(tdp_frame)
        self.fast_limit_entry.grid(row=0, column=1, padx=5)

        slow_limit_label = ttk.Label(tdp_frame, text="Slow Limit (W): ")
        slow_limit_label.grid(row=1, column=0, padx=5)
        self.slow_limit_entry = ttk.Entry(tdp_frame)
        self.slow_limit_entry.grid(row=1, column=1, padx=5)

        slow_time_label = ttk.Label(tdp_frame, text="Slow Time (s): ")
        slow_time_label.grid(row=2, column=0, padx=5)
        self.slow_time_entry = ttk.Entry(tdp_frame)
        self.slow_time_entry.grid(row=2, column=1, padx=5)

        tctl_temp_label = ttk.Label(tdp_frame, text="Tctl Temp (°C): ")
        tctl_temp_label.grid(row=3, column=0, padx=5)
        self.tctl_temp_entry = ttk.Entry(tdp_frame)
        self.tctl_temp_entry.grid(row=3, column=1, padx=5)

        apu_skin_temp_label = ttk.Label(tdp_frame, text="APU Skin Temp (°C): ")
        apu_skin_temp_label.grid(row=4, column=0, padx=5)
        self.apu_skin_temp_entry = ttk.Entry(tdp_frame)
        self.apu_skin_temp_entry.grid(row=4, column=1, padx=5)

        performance_frame = ttk.Frame(tdp_frame)
        performance_frame.grid(row=5, column=0, columnspan=2, pady=5)

        self.max_performance_var = ttk.BooleanVar()
        max_performance_checkbox = ttk.Checkbutton(performance_frame, text="Max Performance", variable=self.max_performance_var, command=lambda: self.power_saving_var.set(False))
        max_performance_checkbox.pack(side=ttk.LEFT, padx=5)

        self.power_saving_var = ttk.BooleanVar()
        power_saving_checkbox = ttk.Checkbutton(performance_frame, text="Power Saving", variable=self.power_saving_var, command=lambda: self.max_performance_var.set(False))
        power_saving_checkbox.pack(side=ttk.LEFT, padx=5)

        apply_tdp_button = ttk.Button(tdp_frame, text="Apply TDP Settings", command=lambda: apply_tdp_settings(self.current_profile))
        apply_tdp_button.grid(row=6, column=0, columnspan=2, pady=5)

        save_profile_button = ttk.Button(content_frame, text="Save Profile", command=self.save_profile)
        save_profile_button.pack(pady=5)

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
        self.cached_profiles = profiles  # Store for reuse
        return profiles

    def update_profile_dropdown(self):
        profiles = self.load_profiles()
        if profiles:
            profile_names = [profile["name"] for profile in profiles]
            print(f"Setting dropdown values to: {profile_names}")
            self.profile_dropdown['values'] = profile_names
        else:
            print("No profiles found to populate dropdown")

    def save_profile(self):
        profile_name = askstring("Save Profile", "Enter profile name:")
        if profile_name:
            profile = {
                "name": profile_name,
                "fast-limit": int(self.fast_limit_entry.get()),
                "slow-limit": int(self.slow_limit_entry.get()),
                "slow-time": int(self.slow_time_entry.get()),
                "tctl-temp": int(self.tctl_temp_entry.get()),
                "apu-skin-temp": int(self.apu_skin_temp_entry.get()),
                "max-performance": self.max_performance_var.get(),
                "power-saving": self.power_saving_var.get()
            }
            with open(os.path.join(self.profiles_directory, f"{profile_name}.json"), "w") as f:
                json.dump(profile, f)
            self.update_profile_dropdown()

    def on_profile_select(self, event):
        selected_profile = self.profile_dropdown.get()
        for profile in self.load_profiles():
            if profile["name"] == selected_profile:
                self.current_profile = profile
                self.fast_limit_entry.delete(0, ttk.END)
                self.fast_limit_entry.insert(0, str(self.current_profile["fast-limit"]))
                self.slow_limit_entry.delete(0, ttk.END)
                self.slow_limit_entry.insert(0, str(self.current_profile["slow-limit"]))
                self.slow_time_entry.delete(0, ttk.END)
                self.slow_time_entry.insert(0, str(self.current_profile["slow-time"]))
                self.tctl_temp_entry.delete(0, ttk.END)
                self.tctl_temp_entry.insert(0, str(self.current_profile["tctl-temp"]))
                self.apu_skin_temp_entry.delete(0, ttk.END)
                self.apu_skin_temp_entry.insert(0, str(self.current_profile["apu-skin-temp"]))
                self.max_performance_var.set(self.current_profile["max-performance"])
                self.power_saving_var.set(self.current_profile["power-saving"])
                break
        apply_tdp_settings(self.current_profile)
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
        return "n/a", "n/a"
    except FileNotFoundError:
        print("nbfc command not found. Make sure NoteBook FanControl is installed.")
        return "n/a", "n/a"

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
```
---
## File: ryzen_master_commander/main.py

```py
import ttkbootstrap as ttk
from ryzen_master_commander.app.main_window import MainWindow
import os
# import matplotlib
# matplotlib.use('TkAgg')

def main():
    theme = detect_system_theme()
    
    # Create the root window ONCE and keep it for the entire app lifecycle
    root = ttk.Window(themename=theme)
    root.title("Ryzen Master and Commander")
    root.geometry("500x950")
    
    # Set the window icon immediately
    try:
        icon_paths = [
            "/usr/share/icons/hicolor/128x128/apps/ryzen-master-commander.png",
            "./share/icons/hicolor/128x128/apps/ryzen-master-commander.png",
            "./img/icon.png"
        ]
        
        for path in icon_paths:
            if os.path.exists(path):
                from PIL import Image, ImageTk
                icon = ImageTk.PhotoImage(Image.open(path))
                root.iconphoto(False, icon)  # Changed to False to not affect future windows
                break
                
        # Set window class for KDE
        root.tk.call('wm', 'class', root._w, "ryzen-master-commander")
    except Exception as e:
        print(f"Error setting application icon: {e}")
    
    # Center window first, before adding any content
    center_window(root, 500, 950)
    
    # Ensure the window is visible and drawn before creating MainWindow
    root.update_idletasks()
    
    # Now create the main window using our already configured root
    app = MainWindow(root)
    
    # Start the main loop with the fully configured window
    root.mainloop()

def center_window(window, width, height):
    """Center the window on the screen."""
    # Get screen dimensions
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # Calculate position coordinates
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    
    # Set window position
    window.geometry(f"{width}x{height}+{x}+{y}")

def ensure_window_visible(root):
    if not root.winfo_viewable():
        root.deiconify()
    root.attributes('-topmost', True)
    root.update()
    root.attributes('-topmost', False)
    root.state('normal')
    root.focus_force()

def detect_system_theme():
    """Detect if system is using dark or light theme and return appropriate ttkbootstrap theme"""
    import os
    import subprocess
    
    # Default fallback theme
    default_theme = "darkly"
    
    try:
        # For KDE Plasma
        if os.environ.get('XDG_CURRENT_DESKTOP') == 'KDE':
            result = subprocess.run(
                ["kreadconfig5", "--group", "General", "--key", "ColorScheme"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                kde_theme = result.stdout.strip().lower()
                return "darkly" if "dark" in kde_theme else "cosmo"
                
        # For GNOME
        elif os.environ.get('XDG_CURRENT_DESKTOP') in ['GNOME', 'Unity']:
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                capture_output=True, text=True
            )
            if result.returncode == 0 and "dark" in result.stdout.lower():
                return "darkly"
            else:
                return "cosmo"
    except Exception as e:
        print(f"Error detecting system theme: {e}")
    
    return default_theme


if __name__ == "__main__":
    app.main()
```
---
