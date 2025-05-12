from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPen
import pyqtgraph as pg
# import numpy as np

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