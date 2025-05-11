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
        |-- ryzen-master-commander-1.0.0-1-any.pkg.tar.zst
        |-- ryzen-master-commander-1.0.0.tar.gz
        |-- ryzen-master-commander-1.0.1.tar.gz
        |-- ryzen-master-commander-1.0.2.tar.gz
        |-- ryzen-master-commander-1.0.3.tar.gz
        |-- ryzen-master-commander-1.0.4.tar.gz
        |-- ryzen-master-commander-1.0.5.tar.gz
        |-- ryzen-master-commander-1.0.6-1-any.pkg.tar.zst
        |-- ryzen-master-commander-1.0.6.tar.gz
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
|-- rebuild_dev.sh
|-- requirements.txt
|-- ryzen_master_commander
    |-- __init__.py
    |-- app
        |-- __init__.py
        |-- fan_profile_editor.py
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
|-- version.txt

```

---
## File: ryzen_master_commander/app/fan_profile_editor.py

```py
import os
import glob
import json
import subprocess
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                            QLabel, QComboBox, QPushButton, QLineEdit, QMessageBox,
                            QGraphicsView) # QGraphicsView for NoDrag
from PyQt5.QtCore import Qt, pyqtSignal, QPointF

import pyqtgraph as pg

class CustomPlotWidget(pg.PlotWidget):
    """
    Custom PlotWidget to reliably emit a signal on mouse release events
    occurring specifically over this widget. Also sets NoDrag mode.
    """
    mouse_released_on_widget = pyqtSignal(object) 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set NoDrag mode for the QGraphicsView base to prevent it from initiating drags.
        self.setDragMode(QGraphicsView.NoDrag) 

    def mouseReleaseEvent(self, ev):
        super().mouseReleaseEvent(ev)
        self.mouse_released_on_widget.emit(ev)

class FanProfileEditor(QMainWindow):
    def __init__(self, current_nbfc_profile_name=None):
        super().__init__()
        self.current_nbfc_profile_name_from_main = current_nbfc_profile_name
        
        self.points = [(20, 0), (40, 30), (60, 60), (80, 100)]
        self.current_config = None
        
        self.hover_point_index = None
        self.drag_point_index = None # This is key for persistent drag
        
        self.nbfc_configs_dir = "/usr/share/nbfc/configs/"
        self.view_box = None
        
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("NBFC Fan Profile Editor")
        self.resize(800, 650) # Slightly taller for new label
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("NBFC Fan Profile Editor")
        title_label.setAlignment(Qt.AlignCenter)
        font = title_label.font(); font.setPointSize(16); font.setBold(True)
        title_label.setFont(font)
        main_layout.addWidget(title_label)
        
        # Profile Selection Group
        profiles_group = QGroupBox("Available Profiles")
        profiles_layout = QHBoxLayout(profiles_group)
        profiles_layout.addWidget(QLabel("Select Profile:"))
        self.profiles_list = self.get_available_profiles()
        self.profile_dropdown = QComboBox()
        self.profile_dropdown.addItems(self.profiles_list)
        self.profile_dropdown.currentIndexChanged.connect(self.on_profile_selected)
        profiles_layout.addWidget(self.profile_dropdown, 1)
        load_btn = QPushButton("Load"); load_btn.clicked.connect(self.load_selected_profile)
        profiles_layout.addWidget(load_btn)
        apply_btn = QPushButton("Apply"); apply_btn.clicked.connect(self.apply_selected_profile)
        profiles_layout.addWidget(apply_btn)
        main_layout.addWidget(profiles_group)
        
        # Plot Widget Setup
        self.plot_widget = CustomPlotWidget()
        main_layout.addWidget(self.plot_widget)

        self.view_box = self.plot_widget.plotItem.vb
        self.view_box.setMouseMode(pg.ViewBox.PanMode) # Default is PanMode, ensures not RectMode
        self.view_box.setMouseEnabled(x=False, y=False) # Disable ViewBox's own mouse pan/zoom
        self.plot_widget.plotItem.setMenuEnabled(False) # Disable right-click context menu on PlotItem

        self.plot_widget.setLabel('left', 'Fan Speed (%)')
        self.plot_widget.setLabel('bottom', 'Temperature (°C)')
        self.plot_widget.setXRange(0, 100, padding=0.01) # Small padding to ensure 0 and 100 are visible
        self.plot_widget.setYRange(0, 100, padding=0.01)
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setTitle('Fan Speed Curve')

        # Plot Items
        self.curve_item = self.plot_widget.plot([], [], pen='b', symbol='o', symbolSize=8, symbolBrush='b')
        self.selected_point_item = pg.ScatterPlotItem([], [], size=12, pen=pg.mkPen('r', width=2), brush=pg.mkBrush(255,0,0,120))
        self.plot_widget.addItem(self.selected_point_item)
        self.coord_text_item = pg.TextItem(anchor=(0.5,1.8)); self.plot_widget.addItem(self.coord_text_item)
        self.coord_text_item.hide()

        # Connect mouse event signals
        self.plot_widget.scene().sigMouseClicked.connect(self.pg_on_scene_click)
        self.plot_widget.scene().sigMouseMoved.connect(self.pg_on_scene_move)
        self.plot_widget.mouse_released_on_widget.connect(self.pg_on_widget_mouse_release)
        
        # Curve Controls Group
        controls_group = QGroupBox("Curve Controls")
        controls_layout = QVBoxLayout(controls_group) # Changed to QVBoxLayout for instructions
        
        buttons_layout = QHBoxLayout() # For Add and Reset buttons
        add_point_btn = QPushButton("Add Point"); add_point_btn.clicked.connect(self.add_point)
        buttons_layout.addWidget(add_point_btn)
        reset_btn = QPushButton("Reset"); reset_btn.clicked.connect(self.reset_curve)
        buttons_layout.addWidget(reset_btn)
        controls_layout.addLayout(buttons_layout)

        # Instructions for removing points
        remove_instruction_label = QLabel("<i>Right-click a point on the curve to remove it.</i>")
        remove_instruction_label.setAlignment(Qt.AlignCenter)
        controls_layout.addWidget(remove_instruction_label)
        
        main_layout.addWidget(controls_group)
        
        # Save Profile Group
        save_group = QGroupBox("Save Profile")
        save_layout = QHBoxLayout(save_group); save_layout.addWidget(QLabel("Profile Name:"))
        self.custom_profile_name = QLineEdit("MyCustomProfile")
        save_layout.addWidget(self.custom_profile_name, 1)
        save_btn = QPushButton("Save Custom Profile"); save_btn.clicked.connect(self.save_custom_profile)
        save_layout.addWidget(save_btn)
        main_layout.addWidget(save_group)
        
        self.update_plot()
        self.select_initial_profile()
    
    def select_initial_profile(self):
        """Selects the initial profile in the dropdown, if applicable."""
        initial_profile_to_set = None
        if self.current_nbfc_profile_name_from_main and \
           self.current_nbfc_profile_name_from_main not in ["n/a", "--"]:
            if self.current_nbfc_profile_name_from_main in self.profiles_list:
                initial_profile_to_set = self.current_nbfc_profile_name_from_main
        
        if initial_profile_to_set:
            try: 
                idx = self.profiles_list.index(initial_profile_to_set)
                self.profile_dropdown.setCurrentIndex(idx)
                # Manually call load if index changed, as currentIndexChanged might not fire if already at 0
                # However, if it's programmatically set, it should fire.
                # self.load_selected_profile() # This might be redundant if currentIndexChanged fires.
            except ValueError:
                if self.profiles_list: self.profile_dropdown.setCurrentIndex(0)
        elif self.profiles_list:
            self.profile_dropdown.setCurrentIndex(0)
        # If setCurrentIndex was called and it changed the index,
        # on_profile_selected -> load_selected_profile will be triggered.
        # If the index was already 0 and it was set to 0, it might not.
        # So, if index is 0 and it's the first load, explicitly load.
        if self.profile_dropdown.currentIndex() == 0 and self.profiles_list and not self.current_config:
             self.load_selected_profile()


    def get_available_profiles(self):
        """Scans the NBFC configs directory for .json files and returns their names."""
        try:
            system_profiles = glob.glob(os.path.join(self.nbfc_configs_dir, "*.json"))
            profile_names = [os.path.splitext(os.path.basename(p))[0] for p in system_profiles]
            return sorted(profile_names)
        except Exception as e:
            print(f"Error getting available profiles: {e}")
            return []
    
    def on_profile_selected(self, index):
        """Handles selection change in the profile dropdown."""
        if index >= 0:
            self.load_selected_profile()
    
    def load_selected_profile(self):
        """Loads fan curve data from the selected NBFC profile file."""
        profile_name = self.profile_dropdown.currentText()
        if not profile_name: return
        
        self.custom_profile_name.setText(profile_name)
        file_path = os.path.join(self.nbfc_configs_dir, f"{profile_name}.json")
        
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "Error", f"Profile '{profile_name}' not found at {file_path}.")
            self.reset_curve(update_dropdown=False); self.update_plot()
            return
            
        try:
            with open(file_path, 'r') as f: config = json.load(f)
            self.current_config = config
            
            curve_points = []
            # ... (Parsing logic remains the same as previous correct version)
            if 'FanConfigurations' in config and config['FanConfigurations']:
                fan_config = config['FanConfigurations'][0] 
                if 'TemperatureThresholds' in fan_config and fan_config['TemperatureThresholds']:
                    for threshold in fan_config['TemperatureThresholds']:
                        if 'UpThreshold' in threshold and 'FanSpeed' in threshold:
                            curve_points.append((threshold['UpThreshold'], threshold['FanSpeed']))
                elif 'FanSpeedPercentageOverrides' in fan_config and fan_config['FanSpeedPercentageOverrides']:
                    overrides = fan_config['FanSpeedPercentageOverrides']
                    if overrides and isinstance(overrides, list) and len(overrides) > 0:
                        if isinstance(overrides[0], dict) and 'Temperature' in overrides[0] and 'FanSpeed' in overrides[0]:
                            for override in overrides: curve_points.append((override['Temperature'], override['FanSpeed']))
                        elif isinstance(overrides[0], dict) and 'FanSpeedPercentage' in overrides[0] and 'FanSpeedValue' in overrides[0]:
                            min_temp, max_temp = 30, 90; step = (max_temp - min_temp) / (len(overrides) -1) if len(overrides)>1 else 10
                            for i, override in enumerate(overrides): curve_points.append((min_temp + i * step, override['FanSpeedPercentage']))
                
                if curve_points: self.points = [(round(p[0]), round(p[1])) for p in curve_points]
                else: QMessageBox.information(self, "Note", f"No fan curve data in '{profile_name}'. Using default."); self.reset_curve(update_dropdown=False)
            else: QMessageBox.warning(self, "Warning", f"Profile '{profile_name}' no fan config. Using default."); self.reset_curve(update_dropdown=False)
            self.update_plot()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load profile '{profile_name}': {str(e)}")
            self.reset_curve(update_dropdown=False); self.update_plot()
    
    def apply_selected_profile(self):
        """Applies the currently selected profile using 'nbfc' command with pkexec."""
        profile_name = self.profile_dropdown.currentText()
        if not profile_name: QMessageBox.warning(self, "Warning", "Please select a profile."); return
        try:
            subprocess.run(['pkexec', 'nbfc', 'config', '-a', profile_name], check=True, capture_output=True, text=True)
            QMessageBox.information(self, "Success", f"Applied fan profile '{profile_name}'.")
        except subprocess.CalledProcessError as e:
            error_details = f"Error: {e.stderr or e.stdout or str(e)}"
            QMessageBox.critical(self, "Error", f"Failed to apply profile '{profile_name}'.\n{error_details}")
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "pkexec or nbfc command not found.")
    
    def save_custom_profile(self):
        """Saves the current fan curve as a new NBFC profile .json file."""
        name = self.custom_profile_name.text().strip()
        if not name: QMessageBox.warning(self, "Warning", "Please enter a profile name."); return
        if any(c in name for c in "/\\:*?\"<>|"): QMessageBox.warning(self, "Warning", "Profile name contains invalid characters."); return

        # ... (Config creation/update logic remains the same as previous correct version)
        if self.current_config: config = self.current_config.copy(); config["NotebookModel"] = name
        else: config = { "NotebookModel": name, "Author": "Ryzen Master Commander", "EcPollInterval": 5000, "ReadWriteWords": False, "CriticalTemperature": 85, "FanConfigurations": [{"ReadRegister": 122, "WriteRegister": 122, "MinSpeedValue": 0, "MaxSpeedValue": 255, "ResetRequired": True, "FanSpeedResetValue": 0, "FanDisplayName": "Fan"}]}
        if "FanConfigurations" not in config or not config["FanConfigurations"]: config["FanConfigurations"] = [{"ReadRegister": 122, "WriteRegister": 122}] 
        if not isinstance(config["FanConfigurations"], list): config["FanConfigurations"] = [config["FanConfigurations"]]
        if not config["FanConfigurations"]: config["FanConfigurations"].append({})
        
        thresholds = []
        if self.points:
            t_0, s_0 = self.points[0]; thresholds.append({"UpThreshold": int(t_0), "DownThreshold": int(max(0, t_0 - 5)), "FanSpeed": float(s_0)})
            for i in range(1, len(self.points)):
                t_curr, s_curr = self.points[i]; t_prev, _ = self.points[i-1]
                down_thresh = min(int(t_prev + 1), int(t_curr)); down_thresh = max(0, down_thresh)
                thresholds.append({"UpThreshold": int(t_curr), "DownThreshold": down_thresh, "FanSpeed": float(s_curr)})
        config["FanConfigurations"][0]["TemperatureThresholds"] = thresholds
        config["FanConfigurations"][0].pop("FanSpeedPercentageOverrides", None)

        try:
            temp_dir = os.path.expanduser("~/.config/ryzen-master-commander/temp_profiles")
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = os.path.join(temp_dir, f"{name}.json")
            with open(temp_file, 'w') as f: json.dump(config, f, indent=2)
            target_file = os.path.join(self.nbfc_configs_dir, f"{name}.json")
            subprocess.run(['pkexec', 'cp', temp_file, target_file], check=True, capture_output=True, text=True)
            QMessageBox.information(self, "Success", f"Saved profile to {target_file}")
            self.refresh_ui_after_save(name)
        except subprocess.CalledProcessError as e:
            error_details = f"Error: {e.stderr or e.stdout or str(e)}"
            QMessageBox.critical(self, "Error", f"Failed to save profile with pkexec.\n{error_details}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save profile: {str(e)}")

    def refresh_ui_after_save(self, saved_profile_name):
        """Refreshes the profile list and selects the newly saved profile."""
        self.profiles_list = self.get_available_profiles()
        self.profile_dropdown.clear()
        self.profile_dropdown.addItems(self.profiles_list)
        if saved_profile_name in self.profiles_list:
            self.profile_dropdown.setCurrentText(saved_profile_name)
        elif self.profiles_list: self.profile_dropdown.setCurrentIndex(0)
    
    def update_plot(self):
        """Updates the fan curve plot with current points and highlights."""
        self.points = sorted([(round(p[0]), round(p[1])) for p in self.points], key=lambda p: p[0])
        temps, speeds = zip(*self.points) if self.points else ([], [])
        self.curve_item.setData(temps, speeds)
        
        self.selected_point_item.clear()
        highlight_idx = self.drag_point_index if self.drag_point_index is not None else self.hover_point_index
        if highlight_idx is not None and 0 <= highlight_idx < len(self.points):
            px, py = self.points[highlight_idx]
            self.selected_point_item.addPoints([px], [py])

    def _get_point_at_scene_pos(self, scene_pos: QPointF, sensitivity_pixels=7):
        """Checks if scene_pos is near any curve point. Returns point index or None."""
        if not self.view_box: return None
        mouse_data_pos = self.view_box.mapSceneToView(scene_pos)
        offset_scene_pos_x = QPointF(scene_pos.x() + sensitivity_pixels, scene_pos.y())
        offset_scene_pos_y = QPointF(scene_pos.x(), scene_pos.y() + sensitivity_pixels)
        offset_data_pos_x = self.view_box.mapSceneToView(offset_scene_pos_x)
        offset_data_pos_y = self.view_box.mapSceneToView(offset_scene_pos_y)
        data_sensitivity_x = abs(offset_data_pos_x.x() - mouse_data_pos.x())
        data_sensitivity_y = abs(offset_data_pos_y.y() - mouse_data_pos.y())
        mx, my = mouse_data_pos.x(), mouse_data_pos.y()
        for i, (px, py) in enumerate(self.points):
            if abs(mx - px) < data_sensitivity_x and abs(my - py) < data_sensitivity_y:
                return i
        return None

    def pg_on_scene_click(self, event): 
        """Handles mouse click events on the plot's scene."""
        if not self.view_box or not self.view_box.sceneBoundingRect().contains(event.scenePos()):
            return 
        
        # Crucially, accept the event IF it's within the plot. This stops the ViewBox from processing it.
        event.accept()

        clicked_point_idx = self._get_point_at_scene_pos(event.scenePos())
        mouse_data_pos = self.view_box.mapSceneToView(event.scenePos())

        if event.button() == Qt.LeftButton:
            if clicked_point_idx is not None: # Clicked on an existing point to start drag
                self.drag_point_index = clicked_point_idx # Set active drag point
                pt_x, pt_y = self.points[self.drag_point_index]
                self.coord_text_item.setText(f"({pt_x}, {pt_y})"); self.coord_text_item.setPos(pt_x, pt_y); self.coord_text_item.show()
                self.update_plot()
            elif event.double(): # Double-click to add point
                new_temp = round(max(0, min(100, mouse_data_pos.x())))
                new_speed = round(max(0, min(100, mouse_data_pos.y())))
                if (new_temp, new_speed) not in self.points:
                    self.points.append((new_temp, new_speed)); self.update_plot()

        elif event.button() == Qt.RightButton: # Right-click to remove point
            if clicked_point_idx is not None:
                if len(self.points) > 2:
                    self.points.pop(clicked_point_idx)
                    if self.hover_point_index == clicked_point_idx: self.hover_point_index = None
                    # If the dragged point is right-clicked (unlikely but possible), cancel drag.
                    if self.drag_point_index == clicked_point_idx: self.drag_point_index = None 
                    self.coord_text_item.hide(); self.update_plot()
                else: QMessageBox.information(self, "Can't Remove", "Fan curve must have at least 2 points.")

    def pg_on_scene_move(self, scene_pos: QPointF):
        """Handles mouse move events on the plot's scene (for hover and drag)."""
        if not self.view_box: return

        # Check if mouse is within plot bounds before processing
        if not self.view_box.sceneBoundingRect().contains(scene_pos):
            self.coord_text_item.hide()
            if self.hover_point_index is not None: self.hover_point_index = None; self.update_plot()
            # If dragging and mouse leaves, we might want to stop drag or let it continue based on button state.
            # For now, if drag_point_index is set, it will continue to update.
            return

        mouse_data_pos = self.view_box.mapSceneToView(scene_pos)
        vx, vy = mouse_data_pos.x(), mouse_data_pos.y()

        if self.drag_point_index is not None: # If a point is being dragged
            new_temp = round(max(0, min(100, vx)))
            new_speed = round(max(0, min(100, vy)))
            self.points[self.drag_point_index] = (new_temp, new_speed)
            self.coord_text_item.setText(f"({new_temp}, {new_speed})"); self.coord_text_item.setPos(new_temp, new_speed)
            if not self.coord_text_item.isVisible(): self.coord_text_item.show()
            self.update_plot()
        else: # Not dragging, handle hover
            old_hover_idx = self.hover_point_index
            self.hover_point_index = self._get_point_at_scene_pos(scene_pos)
            if old_hover_idx != self.hover_point_index: self.update_plot()
            
            if self.hover_point_index is not None and 0 <= self.hover_point_index < len(self.points):
                pt_x, pt_y = self.points[self.hover_point_index]
                self.coord_text_item.setText(f"({pt_x}, {pt_y})"); self.coord_text_item.setPos(pt_x, pt_y); self.coord_text_item.show()
            else: self.coord_text_item.hide()
    
    def pg_on_widget_mouse_release(self, event: 'QMouseEvent'):
        """Handles mouse release events specifically on the plot widget."""
        if event.button() == Qt.LeftButton and self.drag_point_index is not None:
            # Finalize position if needed, though pg_on_scene_move should be accurate
            release_scene_pos = self.plot_widget.mapToScene(event.pos())
            if self.view_box and self.view_box.sceneBoundingRect().contains(release_scene_pos):
                 mouse_data_pos = self.view_box.mapSceneToView(release_scene_pos)
                 final_temp = round(max(0, min(100, mouse_data_pos.x())))
                 final_speed = round(max(0, min(100, mouse_data_pos.y())))
                 if 0 <= self.drag_point_index < len(self.points):
                     self.points[self.drag_point_index] = (final_temp, final_speed)

            self.drag_point_index = None # Crucial: End the drag operation

            # Update hover state based on current mouse position
            self.hover_point_index = self._get_point_at_scene_pos(release_scene_pos) 
            if self.hover_point_index is not None and 0 <= self.hover_point_index < len(self.points):
                pt_x, pt_y = self.points[self.hover_point_index]
                self.coord_text_item.setText(f"({pt_x}, {pt_y})"); self.coord_text_item.setPos(pt_x, pt_y); self.coord_text_item.show()
            else: self.coord_text_item.hide()
            self.update_plot()

    def add_point(self):
        """Adds a new point to the fan curve."""
        # ... (Logic for adding points remains the same as previous correct version)
        if not self.points: self.reset_curve(); return
        self.points = sorted(self.points, key=lambda p: p[0])
        new_point = None
        if len(self.points) < 2:
            last_t, last_s = self.points[0] if self.points else (0,0); new_t = round(min(100, last_t + 20)); new_s = round(min(100, last_s + 20))
            if new_t == last_t and new_s == last_s: new_t,new_s = (50,50); new_point = (new_t, new_s)
        else:
            max_gap, insert_idx = 0, -1
            for i in range(len(self.points)-1): gap = self.points[i+1][0] - self.points[i][0];_ = (max_gap := gap, insert_idx := i) if gap > max_gap else None # Python 3.8+
            if insert_idx != -1 and max_gap > 5: p_prev, p_next = self.points[insert_idx], self.points[insert_idx+1]; new_t = round((p_prev[0]+p_next[0])/2.0); new_s = round((p_prev[1]+p_next[1])/2.0); new_point = (new_t, new_s)
            else: last_t, last_s = self.points[-1]; new_point = (round(min(100,last_t+15)), round(min(100,last_s+15))) if last_t < 90 else ( (50,50) if (50,50) not in self.points else (70,70) )
        if new_point and new_point not in self.points: self.points.append(new_point); self.update_plot()
    
    def reset_curve(self, update_dropdown=True):
        """Resets the fan curve to a default state."""
        self.points = [(20,0), (40,30), (60,60), (80,100)]
        if update_dropdown: self.current_config = None; self.custom_profile_name.setText("MyCustomProfile")
        self.hover_point_index = None; self.drag_point_index = None
        self.coord_text_item.hide()
        # Always update plot on reset, whether full or partial (like from load failure)
        self.update_plot()
```
---
## File: ryzen_master_commander/app/main_window.py

```py
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
```
---
## File: ryzen_master_commander/main.py

```py
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ryzen_master_commander.app.main_window import MainWindow

def main():
    # Create Qt application
    # For Wayland/X11 icon and .desktop file association:
    # Set the desktop file name (without .desktop extension)
    QApplication.setDesktopFileName("ryzen-master-commander")
    app = QApplication(sys.argv)
    app.setApplicationName("ryzen-master-commander") # Match StartupWMClass and Icon name
    
    # Set application icon
    icon_paths = [
        "/usr/share/icons/hicolor/128x128/apps/ryzen-master-commander.png",
        "./share/icons/hicolor/128x128/apps/ryzen-master-commander.png",
        "./img/icon.png"
    ]
    
    for path in icon_paths:
        if os.path.exists(path):
            app.setWindowIcon(QIcon(path))
            break
    
    # Configure PyQtGraph for dark/light mode
    try:
        import pyqtgraph as pg
        import subprocess # Added for KDE theme detection
        # Check for KDE dark mode
        is_dark_mode = False
        
        if os.environ.get('XDG_CURRENT_DESKTOP') == 'KDE':
            try:
                result = subprocess.run(
                    ["kreadconfig5", "--group", "General", "--key", "ColorScheme"],
                    capture_output=True, text=True
                )
                is_dark_mode = "dark" in result.stdout.strip().lower()
            except Exception as e:
                print(f"Error detecting KDE theme: {e}")
        
        # Another approach for dark mode detection
        if not is_dark_mode:
            try:
                from PyQt5.QtGui import QPalette
                app_palette = app.palette()
                # If text is lighter than background, we're likely in dark mode
                bg_color = app_palette.color(QPalette.Window).lightness()
                text_color = app_palette.color(QPalette.WindowText).lightness()
                is_dark_mode = text_color > bg_color
            except Exception as e:
                print(f"Error using palette for theme detection: {e}")
        
        print(f"Dark mode detected: {is_dark_mode}")
        
        # Set PyQtGraph theme
        if is_dark_mode:
            pg.setConfigOption('background', 'k')
            pg.setConfigOption('foreground', 'w')
        else:
            pg.setConfigOption('background', 'w')
            pg.setConfigOption('foreground', 'k')
    except ImportError:
        print("PyQtGraph not available")
    
    # Create and show the main window
    main_window = MainWindow()
    main_window.show()
    
    # Start the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
```
---
