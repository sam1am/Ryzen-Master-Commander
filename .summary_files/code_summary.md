Output of tree command:
```
|-- LICENSE
|-- app
    |-- __init__.py
    |-- __pycache__
    |-- graphs.py
    |-- main_window.py
    |-- profile_manager.py
    |-- system_utils.py
|-- fan_profiles
    |-- GPD_Win_Mini2.json
|-- main.py
|-- manifest.in
|-- requirements.txt
|-- setup.py
|-- tdp_profiles
    |-- WinMini-Balanced.json
    |-- WinMini-BatterySaver.json
    |-- WinMini-MaxPerformance.json

```

---

./setup.py
```
from setuptools import setup, find_packages

setup(
    name='ryzen-master-commander',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'matplotlib',
        'ttkbootstrap',
    ],
    entry_points={
        'console_scripts': [
            'ryzen-master-commander = app.main:main',
        ],
    },
)```
---

./main.py
```
import ttkbootstrap as ttk
from app.main_window import MainWindow

def main():
    root = ttk.Window(themename="darkly")
    root.title("Ryzen Master and Commander")
    root.geometry("300x640")  # Set the initial window size to 800x600 pixels
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()```
---

./requirements.txt
```
matplotlib
ttkbootstrap```
---

./app/graphs.py
```
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
            self.canvas.draw()```
---

./app/main_window.py
```
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter.simpledialog import askstring
import sys
# import json
# import os
# from json.decoder import JSONDecodeError
import subprocess
from app.graphs import TemperatureGraph, FanSpeedGraph
from app.system_utils import get_system_readings, apply_tdp_settings
from app.profile_manager import ProfileManager

class MainWindow:
    def __init__(self, root):
        sudo_password = askstring("Sudo Password", "Enter your sudo password:", show='*')
        self.root = root
        self.root.sudo_password = sudo_password
        self.graph_visible = True
        self.graph_frame = None
        self.profile_manager = ProfileManager(self.root, self.root.sudo_password)
        self.fan_speed_adjustment_delay = None

        self.create_widgets()
        self.update_readings()

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
            subprocess.run(['sudo', '-k'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(['sudo', '-S', 'nbfc', 'set', '-s', str(slider_value)], input=self.root.sudo_password + '\n', text=True)
            self.manual_control_value_label.config(text=f"{slider_value}%")
        except subprocess.CalledProcessError as e:
            print(f"Error setting fan speed: {e}")

    def set_auto_control(self):
        self.current_control_mode = 'auto'
        try:
            subprocess.run(['sudo', '-k'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(['sudo', '-S', 'nbfc', 'set', '-a'], input=sudo_password + '\n', text=True)
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
    ```
---

./app/profile_manager.py
```
from app.system_utils import apply_tdp_settings
from tkinter.simpledialog import askstring
import ttkbootstrap as ttk
import json
import os

class ProfileManager:
    def __init__(self, root, sudo_password):
        self.root = root
        self.sudo_password = sudo_password
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

        apply_tdp_button = ttk.Button(tdp_frame, text="Apply TDP Settings", command=lambda: apply_tdp_settings(self.current_profile, self.sudo_password))
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
        apply_tdp_settings(self.current_profile, self.root.sudo_password)```
---

./app/system_utils.py
```
import subprocess
import re

def get_system_readings():
    try:
        output = subprocess.check_output(['nbfc', 'status', '-a'], text=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to execute 'nbfc status -a': {e}")
        return "n/a", "n/a"

    temperature_match = re.search(r'Temperature\s+:\s+(\d+\.?\d*)', output)
    fan_speed_match = re.search(r'Current fan speed\s+:\s+(\d+\.?\d*)', output)

    temperature = temperature_match.group(1) if temperature_match else "n/a"
    fan_speed = fan_speed_match.group(1) if fan_speed_match else "n/a"
    print(f"Temperature: {temperature}, Fan Speed: {fan_speed}")
    return temperature, fan_speed

def apply_tdp_settings(current_profile, sudo_password):
    if current_profile:
        command = ['sudo', '-S', 'ryzenadj']
        for key, value in current_profile.items():
            if key in ["fast-limit", "slow-limit"]:
                command.extend([f'--{key}={value * 1000}'])
            elif key == "slow-time":
                command.extend([f'--{key}={value * 1000}'])
            elif key not in ["name", "max_performance", "power_saving"]:
                command.extend([f'--{key}={value}'])
        if current_profile.get("max_performance"):
            command.append("--max-performance")
        elif current_profile.get("power_saving"):
            command.append("--power-saving")
        try:
            subprocess.run(command, input=sudo_password + '\n', text=True)
        except subprocess.CalledProcessError as e:
            print(f"Error applying TDP settings: {e}")```
---
