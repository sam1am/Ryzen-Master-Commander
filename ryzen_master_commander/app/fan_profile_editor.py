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
        user_profiles = glob.glob(os.path.join(self.user_configs_dir, "*.json"))
        
        # Combine and extract names
        all_profiles = system_profiles + user_profiles
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