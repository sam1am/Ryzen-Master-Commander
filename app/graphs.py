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