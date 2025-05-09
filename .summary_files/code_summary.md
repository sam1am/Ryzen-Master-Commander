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
        |-- pkg
            |-- ryzen-master-commander
                |-- .BUILDINFO
                |-- .MTREE
                |-- .PKGINFO
                |-- usr
                    |-- bin
                        |-- ryzen-master-commander
                        |-- ryzen-master-commander-helper
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
                        |-- licenses
                            |-- ryzen-master-commander
                                |-- LICENSE
                        |-- ryzen-master-commander
                            |-- fan_profiles
                                |-- GPD_Win_Mini2.json
                            |-- tdp_profiles
                                |-- WinMini-Balanced.json
                                |-- WinMini-BatterySaver.json
                                |-- WinMini-MaxPerformance.json
        |-- ryzen-master-commander-1.0.0-1-any.pkg.tar.zst
        |-- ryzen-master-commander-1.0.0.tar.gz
        |-- src
            |-- ryzen-master-commander-1.0.0
                |-- .gitignore
                |-- LICENSE
                |-- README.md
                |-- bin
                    |-- ryzen-master-commander
                    |-- ryzen-master-commander-helper
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
                |-- tdp_profiles
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
|-- tdp_profiles

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

  <action id="org.yourusername.ryzenadj">
    <description>Run ryzenadj with elevated privileges</description>
    <message>Authentication is required to change processor settings</message>
    <icon_name>cpu</icon_name>
    <defaults>
      <allow_any>auth_admin_keep</allow_any>
      <allow_inactive>auth_admin_keep</allow_inactive>
      <allow_active>auth_admin_keep</allow_active>
    </defaults>
    <annotate key="org.freedesktop.policykit.exec.path">/usr/bin/ryzenadj</annotate>
    <annotate key="org.freedesktop.policykit.exec.allow_gui">true</annotate>
  </action>
  
  <action id="org.yourusername.nbfc">
    <description>Run nbfc with elevated privileges</description>
    <message>Authentication is required to control fan settings</message>
    <icon_name>fan</icon_name>
    <defaults>
      <allow_any>auth_admin_keep</allow_any>
      <allow_inactive>auth_admin_keep</allow_inactive>
      <allow_active>auth_admin_keep</allow_active>
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
## File: ryzen_master_commander/app/graphs.py

```py
import ttkbootstrap as ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class TemperatureGraph:
    def __init__(self, root):
        self.root = root
        self.temperature_readings = []
        self.fig, self.ax = plt.subplots(figsize=(6, 1.5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack()

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
import sys
import subprocess
from ryzen_master_commander.app.graphs import TemperatureGraph, FanSpeedGraph
from ryzen_master_commander.app.system_utils import get_system_readings, apply_tdp_settings
from ryzen_master_commander.app.profile_manager import ProfileManager

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.graph_visible = True
        self.graph_frame = None
        self.profile_manager = ProfileManager(self.root)
        self.fan_speed_adjustment_delay = None

        self.create_widgets()
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

        # Create a button to toggle graph visibility
        self.graph_button = ttk.Button(content_frame, text="Show Graph", command=self.toggle_graph)
        self.graph_button.pack(pady=5)

        # Create temperature label
        self.temp_label = ttk.Label(content_frame, text="Temperature: ")
        self.temp_label.pack(pady=5)

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
        self.radio_auto_control = ttk.Radiobutton(control_mode_frame, text='Auto Control', value='auto', variable='control_mode', command=self.set_auto_control)
        self.radio_auto_control.grid(row=0, column=0, padx=5)
        self.radio_manual_control = ttk.Radiobutton(control_mode_frame, text='Manual Control', value='manual', variable='control_mode', command=self.set_manual_control)
        self.radio_manual_control.grid(row=0, column=1, padx=5)

        # Create TDP controls
        separator = ttk.Separator(center_frame, orient='horizontal')
        separator.pack(fill='x', pady=10)

        tdp_controls_label = ttk.Label(center_frame, text="TDP Controls", font=("Helvetica", 14, "bold"))
        tdp_controls_label.pack(pady=5)

        self.profile_manager.create_widgets(center_frame)
        # self.setup_system_tray()

    def update_readings(self):
        temperature, fan_speed = get_system_readings()
        self.temp_label.config(text=f"Temperature: {temperature} °C")
        self.fan_speed_label.config(text=f"Fan Speed: {fan_speed}%")
        self.temperature_graph.update_temperature(temperature)
        self.fan_speed_graph.update_fan_speed(fan_speed)
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
        if self.graph_visible:
            self.graph_frame.pack_forget()
            self.graph_button.config(text="Show Graph")
        else:
            self.graph_frame.pack(side=ttk.TOP, fill=ttk.BOTH, expand=True)
            self.graph_button.config(text="Hide Graph")
        self.graph_visible = not self.graph_visible
    
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
        self.profiles_directory = "./tdp_profiles"
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
        for file in os.listdir(self.profiles_directory):
            if file.endswith(".json"):
                file_path = os.path.join(self.profiles_directory, file)
                try:
                    with open(file_path, "r") as f:
                        profile = json.load(f)
                        profiles.append(profile)
                except json.JSONDecodeError as e:
                    print(f"Error loading profile '{file}': {e}")
                    print(f"Skipping profile '{file}'")
        return profiles

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

    def update_profile_dropdown(self):
        profiles = self.load_profiles()
        self.profile_dropdown['values'] = [profile["name"] for profile in profiles]

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
    fan_speed_match = re.search(r'Current fan speed\s+:\s+(\d+\.?\d*)', output)

    temperature = temperature_match.group(1) if temperature_match else "n/a"
    fan_speed = fan_speed_match.group(1) if fan_speed_match else "n/a"
    return temperature, fan_speed

def apply_tdp_settings(current_profile):
    # Remove sudo_password parameter
    if current_profile:
        command = ['pkexec', 'ryzenadj']  # Use pkexec instead of sudo
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
            subprocess.run(command)  # No input needed with pkexec
        except subprocess.CalledProcessError as e:
            print(f"Error applying TDP settings: {e}")

```
---
## File: ryzen_master_commander/main.py

```py
import ttkbootstrap as ttk
from ryzen_master_commander.app.main_window import MainWindow
import time

def main():
    theme = detect_system_theme()
    root = ttk.Window(themename=theme)
    root.title("Ryzen Master and Commander")
    root.geometry("500x950")
    
    # Center the window on the screen
    center_window(root, 500, 950)
    
    app = MainWindow(root)
    
    # Use after method to ensure window visibility after initialization
    root.after(100, lambda: ensure_window_visible(root))
    
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
## File: share/applications/ryzen-master-commander.desktop

```desktop
[Desktop Entry]
Name=Ryzen Master Commander
Comment=AMD Ryzen TDP and Fan Control
GenericName=Hardware Control
Exec=ryzen-master-commander
Icon=/usr/share/icons/hicolor/128x128/apps/ryzen-master-commander.png
Terminal=false
Type=Application
Categories=System;Settings;HardwareSettings;
Keywords=AMD;Ryzen;TDP;Fan;Control;
StartupNotify=true
```
---
