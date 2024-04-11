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
        apply_tdp_settings(self.current_profile, self.root.sudo_password)