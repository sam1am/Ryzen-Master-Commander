import os
import subprocess
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                            QSlider, QGroupBox, QPushButton, 
                            QRadioButton, QStatusBar, QFrame, QSplitter, QApplication,
                            QSystemTrayIcon, QMenu, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QAction
# import sys

from ryzen_master_commander.app.graphs import CombinedGraph
from ryzen_master_commander.app.system_utils import get_system_readings
from ryzen_master_commander.app.profile_manager import ProfileManager
from ryzen_master_commander.app.fan_profile_editor import FanProfileEditor
from ryzen_master_commander.app.nbfc_manager import NBFCManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize instance variables
        self.profile_manager = ProfileManager()
        self.fan_speed_adjustment_delay = None
        self.graph_visible = True

        NBFCManager.setup_nbfc(self)
        
        # Set up the UI
        self.init_ui()
        
        # Set up system tray
        self.setup_system_tray()
        
        # Set auto control by default
        self.radio_auto_control.setChecked(True)
        # self.set_auto_control()
        
        # Start reading system values
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.update_readings)
        self.refresh_timer.start(5000)  # Initial refresh every 5 seconds
        
        # Schedule first reading
        QTimer.singleShot(1000, self.update_readings)

    def check_nbfc_running(self):
        """Check if NBFC service is running"""
        try:
            result = subprocess.run(['nbfc', 'status'], 
                                   capture_output=True, 
                                   text=True)
            return "ERROR: connect()" not in result.stderr
        except Exception:
            print(f"nbfc not running: {result.stderr}")
            return False
    
    def start_nbfc_service(self):
        """Prompt user to start NBFC service"""
        # msg = QMessageBox(self)
        # msg.setIcon(QMessageBox.Warning)
        # msg.setWindowTitle("NBFC Service Not Running")
        # msg.setText("The notebook fan control service (NBFC) is not running.")
        # msg.setInformativeText("Fan control features require NBFC to be running. Would you like to start it now?")
        # msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        # msg.setDefaultButton(QMessageBox.Yes)
        
        # if msg.exec_() == QMessageBox.Yes:

        print("Attempting to start NBFC service...")
        try:
            subprocess.run(['pkexec', 'nbfc', 'start'], check=True)
            # QMessageBox.information(self, "Success", "NBFC service started successfully.")
        except subprocess.CalledProcessError:
            QMessageBox.critical(self, "Error", "Failed to start NBFC service. Fan control features may not work properly.")
    
    def setup_system_tray(self):
        """Set up the system tray icon and menu"""
        # Create the tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Get the application icon
        app_icon = QApplication.windowIcon()
        if not app_icon.isNull():
            self.tray_icon.setIcon(app_icon)
        else:
            # Try to find icon in standard locations
            for path in ["/usr/share/icons/hicolor/128x128/apps/ryzen-master-commander.png",
                        "./share/icons/hicolor/128x128/apps/ryzen-master-commander.png",
                        "./img/icon.png"]:
                if os.path.exists(path):
                    self.tray_icon.setIcon(QIcon(path))
                    break
        
        # Create the tray menu
        tray_menu = QMenu()
        
        # Add actions to the tray menu
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show_from_tray)
        tray_menu.addAction(show_action)
        
        toggle_auto_action = QAction("Auto Fan Control", self)
        toggle_auto_action.setCheckable(True)
        toggle_auto_action.setChecked(self.radio_auto_control.isChecked())
        toggle_auto_action.triggered.connect(self.toggle_auto_control_from_tray)
        tray_menu.addAction(toggle_auto_action)
        self.toggle_auto_action = toggle_auto_action
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        # Set the context menu for the tray icon
        self.tray_icon.setContextMenu(tray_menu)
        
        # Connect signals
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Show the tray icon
        self.tray_icon.show()
        
        # Update tooltip with temperature and fan speed
        self.update_tray_tooltip()

    def update_tray_tooltip(self):
        """Update tray icon tooltip with current system information"""
        temp_text = self.temp_label.text().replace("Temperature: ", "")
        fan_text = self.fan_speed_label.text().replace("Fan Speed: ", "")
        profile_text = self.current_profile_label.text().replace("Current Profile: ", "")
        
        tooltip = f"Ryzen Master Commander\n{temp_text} | {fan_text}\nProfile: {profile_text}"
        self.tray_icon.setToolTip(tooltip)

    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.Trigger:  # Left click
            if self.isVisible():
                self.hide()
            else:
                self.show_from_tray()

    def show_from_tray(self):
        """Show the main window from tray"""
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def toggle_auto_control_from_tray(self, checked):
        """Toggle auto control from tray menu"""
        if checked:
            self.radio_auto_control.setChecked(True)
        else:
            self.radio_manual_control.setChecked(True)

    def quit_application(self):
        """Quit the application"""
        QApplication.quit()

    def closeEvent(self, event):
        """Override close event to minimize to tray instead of closing"""
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()

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
        splitter = QSplitter(Qt.Orientation.Vertical)
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
        
        self.refresh_slider = QSlider(Qt.Orientation.Horizontal)
        self.refresh_slider.setRange(1, 30)
        self.refresh_slider.setValue(5)
        self.refresh_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
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
        
        self.fan_speed_control_slider = QSlider(Qt.Orientation.Horizontal)
        self.fan_speed_control_slider.setRange(0, 100)
        self.fan_speed_control_slider.setValue(50)
        self.fan_speed_control_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
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
        self.status_bar.addPermanentWidget(QFrame(frameShape=QFrame.Shape.VLine))
        self.status_bar.addPermanentWidget(self.fan_speed_label)
        self.status_bar.addPermanentWidget(QFrame(frameShape=QFrame.Shape.VLine))
        self.status_bar.addPermanentWidget(self.current_profile_label)
    
    def update_readings(self):
        temperature, fan_speed, current_profile = get_system_readings()
        
        # Update status bar labels
        self.temp_label.setText(f"Temperature: {temperature}°C")
        self.fan_speed_label.setText(f"Fan Speed: {fan_speed}%")
        self.current_profile_label.setText(f"Current Profile: {current_profile}")
        
        # Update combined graph
        self.combined_graph.update_data(temperature, fan_speed)
        
        # Update tray tooltip
        self.update_tray_tooltip()
        
        # Update tray menu auto control checkbox state
        if hasattr(self, 'toggle_auto_action'):
            self.toggle_auto_action.setChecked(self.radio_auto_control.isChecked())

    
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