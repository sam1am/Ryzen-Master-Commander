import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter.simpledialog import askstring
import os
import subprocess
from ryzen_master_commander.app.graphs import TemperatureGraph, FanSpeedGraph
from ryzen_master_commander.app.system_utils import get_system_readings
from ryzen_master_commander.app.profile_manager import ProfileManager

class MainWindow:
    def __init__(self, root):
        self.root = root
        
        # The rest of your initialization code
        self.graph_visible = True
        self.graph_frame = None
        self.profile_manager = ProfileManager(self.root)
        self.fan_speed_adjustment_delay = None

        # Create widgets in the provided root window
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
