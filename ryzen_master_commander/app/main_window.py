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
        active_nbfc_profile = None
        current_profile_text = self.current_profile_label.text() # e.g. "Current Profile: SomeProfileName"
        
        prefix = "Current Profile: "
        if current_profile_text.startswith(prefix):
            profile_name_part = current_profile_text[len(prefix):].strip()
            if profile_name_part and profile_name_part != "--" and profile_name_part != "n/a":
                active_nbfc_profile = profile_name_part
                
        self.fan_editor = FanProfileEditor(current_nbfc_profile_name=active_nbfc_profile)
        self.fan_editor.show()