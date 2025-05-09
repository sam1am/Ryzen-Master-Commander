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