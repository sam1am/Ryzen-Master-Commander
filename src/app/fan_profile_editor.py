import os
import glob
import json
import subprocess
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QComboBox,
    QPushButton,
    QLineEdit,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QPointF, QEvent

# from PyQt6.QtGui import QCursor

import pyqtgraph as pg


class FanProfileEditor(QMainWindow):
    def __init__(self, current_nbfc_profile_name=None):
        super().__init__()
        self.current_nbfc_profile_name_from_main = current_nbfc_profile_name

        self.points = [(20, 0), (40, 30), (60, 60), (80, 100)]
        self.current_config = None

        self.hover_point_index = None
        self.drag_point_index = None
        self.is_dragging = False  # Explicit tracking of drag state

        self.nbfc_configs_dir = "/usr/share/nbfc/configs/"
        self.view_box = None

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Fan Curve Editor")
        self.resize(800, 650)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Title
        title_label = QLabel("Fan Curve Editor")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title_label.font()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        main_layout.addWidget(title_label)

        # Profile Selection Group
        profiles_group = QGroupBox("Available Profiles")
        profiles_layout = QHBoxLayout(profiles_group)
        profiles_layout.addWidget(QLabel("Select Profile:"))
        self.profiles_list = self.get_available_profiles()
        self.profile_dropdown = QComboBox()
        self.profile_dropdown.addItems(self.profiles_list)
        self.profile_dropdown.currentIndexChanged.connect(
            self.on_profile_selected
        )
        profiles_layout.addWidget(self.profile_dropdown, 1)
        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self.load_selected_profile)
        profiles_layout.addWidget(load_btn)
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_selected_profile)
        profiles_layout.addWidget(apply_btn)
        main_layout.addWidget(profiles_group)

        # Plot Widget Setup - Using direct PyQtGraph widget
        self.plot_widget = pg.PlotWidget()
        main_layout.addWidget(self.plot_widget)

        self.view_box = self.plot_widget.plotItem.vb
        self.view_box.setMouseMode(pg.ViewBox.PanMode)
        self.view_box.setMouseEnabled(x=False, y=False)  # Disable panning
        self.plot_widget.plotItem.setMenuEnabled(False)  # Disable context menu

        self.plot_widget.setLabel("left", "Fan Speed (%)")
        self.plot_widget.setLabel("bottom", "Temperature (°C)")
        self.plot_widget.setXRange(0, 100, padding=0.01)
        self.plot_widget.setYRange(0, 100, padding=0.01)
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setTitle("Fan Speed Curve")

        # Important: Enable mouse tracking for hover effects
        self.plot_widget.setMouseTracking(True)

        # Plot Items
        self.curve_item = self.plot_widget.plot(
            [], [], pen="b", symbol="o", symbolSize=8, symbolBrush="b"
        )
        self.selected_point_item = pg.ScatterPlotItem(
            [],
            [],
            size=12,
            pen=pg.mkPen("r", width=2),
            brush=pg.mkBrush(255, 0, 0, 120),
        )
        self.plot_widget.addItem(self.selected_point_item)
        self.coord_text_item = pg.TextItem(anchor=(0.5, 1.8))
        self.plot_widget.addItem(self.coord_text_item)
        self.coord_text_item.hide()

        # Install event filter for direct mouse event handling
        self.plot_widget.viewport().installEventFilter(self)

        # Curve Controls Group
        controls_group = QGroupBox("Curve Controls")
        controls_layout = QVBoxLayout(controls_group)

        # Instructions
        instructions_layout = QVBoxLayout()
        drag_instruction = QLabel(
            "<i>Drag to move. Double click to add. Right click to remove.</i>"
        )
        drag_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions_layout.addWidget(drag_instruction)

        # Reset button
        reset_layout = QHBoxLayout()
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_curve)
        reset_layout.addStretch()
        reset_layout.addWidget(reset_btn)
        reset_layout.addStretch()

        controls_layout.addLayout(instructions_layout)
        controls_layout.addLayout(reset_layout)
        main_layout.addWidget(controls_group)

        # Save Profile Group
        save_group = QGroupBox("Save Profile")
        save_layout = QHBoxLayout(save_group)
        save_layout.addWidget(QLabel("Profile Name:"))
        self.custom_profile_name = QLineEdit("MyCustomProfile")
        save_layout.addWidget(self.custom_profile_name, 1)
        save_btn = QPushButton("Save Custom Profile")
        save_btn.clicked.connect(self.save_custom_profile)
        save_layout.addWidget(save_btn)
        main_layout.addWidget(save_group)

        self.update_plot()
        self.select_initial_profile()

    def eventFilter(self, obj, event):
        """Direct event filter for mouse events on the plot widget viewport."""
        if obj is self.plot_widget.viewport():
            event_type = event.type()

            # Mouse press - start drag operation
            if (
                event_type == QEvent.Type.MouseButtonPress
                and event.button() == Qt.MouseButton.LeftButton
            ):
                scene_pos = self.plot_widget.mapToScene(event.pos())
                idx = self._get_point_at_scene_pos(scene_pos)
                if idx is not None:
                    self.drag_point_index = idx
                    self.is_dragging = True
                    self._update_hover_point(scene_pos)
                    return True  # Event handled
                # Check for double click to add point
                elif (
                    event.type() == QEvent.Type.MouseButtonDblClick
                ):  # Changed from doubleClick() method
                    data_pos = self.view_box.mapSceneToView(scene_pos)
                    self._add_point_at(data_pos.x(), data_pos.y())
                    return True

            # Mouse move - update point position during drag
            elif event_type == QEvent.Type.MouseMove:
                scene_pos = self.plot_widget.mapToScene(event.pos())
                if self.is_dragging and self.drag_point_index is not None:
                    data_pos = self.view_box.mapSceneToView(scene_pos)
                    self._update_point_position(
                        self.drag_point_index, data_pos.x(), data_pos.y()
                    )
                    return True
                else:
                    self._update_hover_point(scene_pos)

            # Mouse release - end drag operation
            elif (
                event_type == QEvent.Type.MouseButtonRelease
                and event.button() == Qt.MouseButton.LeftButton
            ):
                if self.is_dragging:
                    scene_pos = self.plot_widget.mapToScene(event.pos())
                    data_pos = self.view_box.mapSceneToView(scene_pos)

                    # Finalize position if still dragging
                    if self.drag_point_index is not None:
                        self._update_point_position(
                            self.drag_point_index, data_pos.x(), data_pos.y()
                        )

                    # Reset drag state
                    self.is_dragging = False
                    self.drag_point_index = None

                    # Update hover for current position
                    self._update_hover_point(scene_pos)
                    return True

            # Right-click to remove a point
            elif (
                event_type == QEvent.Type.MouseButtonPress
                and event.button() == Qt.MouseButton.RightButton
            ):
                scene_pos = self.plot_widget.mapToScene(event.pos())
                idx = self._get_point_at_scene_pos(scene_pos)
                if idx is not None:
                    self._remove_point_at_index(idx)
                    return True

        # For all other objects and events, pass to base implementation
        return super().eventFilter(obj, event)

    def _add_point_at(self, x, y):
        """Add a new point at the given coordinates."""
        new_temp = round(max(0, min(100, x)))
        new_speed = round(max(0, min(100, y)))
        if (new_temp, new_speed) not in self.points:
            self.points.append((new_temp, new_speed))
            self.update_plot()

    def _update_point_position(self, idx, x, y):
        """Update the position of a point at the given index."""
        if 0 <= idx < len(self.points):
            new_temp = round(max(0, min(100, x)))
            new_speed = round(max(0, min(100, y)))
            self.points[idx] = (new_temp, new_speed)

            # Update coordinate label
            self.coord_text_item.setText(f"({new_temp}, {new_speed})")
            self.coord_text_item.setPos(new_temp, new_speed)
            self.coord_text_item.show()

            self.update_plot()

    def _remove_point_at_index(self, idx):
        """Remove the point at the given index if possible."""
        if 0 <= idx < len(self.points):
            if len(self.points) > 2:
                self.points.pop(idx)

                # Update hover and drag indices
                if self.hover_point_index == idx:
                    self.hover_point_index = None
                if self.drag_point_index == idx:
                    self.drag_point_index = None
                    self.is_dragging = False

                self.coord_text_item.hide()
                self.update_plot()
            else:
                QMessageBox.information(
                    self,
                    "Can't Remove",
                    "Fan curve must have at least 2 points.",
                )

    def _update_hover_point(self, scene_pos):
        """Update the hover point based on cursor position."""
        idx = self._get_point_at_scene_pos(scene_pos)
        old_hover_idx = self.hover_point_index
        self.hover_point_index = idx

        if idx is not None and 0 <= idx < len(self.points):
            pt_x, pt_y = self.points[idx]
            self.coord_text_item.setText(f"({pt_x}, {pt_y})")
            self.coord_text_item.setPos(pt_x, pt_y)
            self.coord_text_item.show()
            # Change cursor to hand cursor to indicate draggable point
            self.plot_widget.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.coord_text_item.hide()
            # Reset cursor to default
            self.plot_widget.setCursor(Qt.CursorShape.ArrowCursor)

        if old_hover_idx != self.hover_point_index:
            self.update_plot()

    def _get_point_at_scene_pos(self, scene_pos, sensitivity_pixels=12):
        """Find the index of the point near the given scene position."""
        if not self.view_box:
            return None

        mouse_data_pos = self.view_box.mapSceneToView(scene_pos)

        # Convert sensitivity from pixels to data units
        offset_scene_pos = QPointF(
            scene_pos.x() + sensitivity_pixels, scene_pos.y()
        )
        offset_data_pos = self.view_box.mapSceneToView(offset_scene_pos)
        data_sensitivity = abs(offset_data_pos.x() - mouse_data_pos.x())

        mx, my = mouse_data_pos.x(), mouse_data_pos.y()

        # Find the closest point within sensitivity range
        closest_idx = None
        closest_dist = float("inf")

        for i, (px, py) in enumerate(self.points):
            # Calculate distance between mouse position and point
            dist = ((mx - px) ** 2 + (my - py) ** 2) ** 0.5
            if dist < data_sensitivity and dist < closest_dist:
                closest_dist = dist
                closest_idx = i

        return closest_idx

    def select_initial_profile(self):
        """Selects the initial profile in the dropdown, if applicable."""
        initial_profile_to_set = None
        if (
            self.current_nbfc_profile_name_from_main
            and self.current_nbfc_profile_name_from_main not in ["n/a", "--"]
        ):
            if self.current_nbfc_profile_name_from_main in self.profiles_list:
                initial_profile_to_set = (
                    self.current_nbfc_profile_name_from_main
                )

        if initial_profile_to_set:
            try:
                idx = self.profiles_list.index(initial_profile_to_set)
                self.profile_dropdown.setCurrentIndex(idx)
            except ValueError:
                if self.profiles_list:
                    self.profile_dropdown.setCurrentIndex(0)
        elif self.profiles_list:
            self.profile_dropdown.setCurrentIndex(0)

        if (
            self.profile_dropdown.currentIndex() == 0
            and self.profiles_list
            and not self.current_config
        ):
            self.load_selected_profile()

    def get_available_profiles(self):
        """Scans the NBFC configs directory for .json files and returns their names."""
        try:
            system_profiles = glob.glob(
                os.path.join(self.nbfc_configs_dir, "*.json")
            )
            profile_names = [
                os.path.splitext(os.path.basename(p))[0]
                for p in system_profiles
            ]
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
        if not profile_name:
            return

        self.custom_profile_name.setText(profile_name)
        file_path = os.path.join(self.nbfc_configs_dir, f"{profile_name}.json")

        if not os.path.exists(file_path):
            QMessageBox.critical(
                self,
                "Error",
                f"Profile '{profile_name}' not found at {file_path}.",
            )
            self.reset_curve(update_dropdown=False)
            self.update_plot()
            return

        try:
            with open(file_path, "r") as f:
                config = json.load(f)
            self.current_config = config

            curve_points = []
            if "FanConfigurations" in config and config["FanConfigurations"]:
                fan_config = config["FanConfigurations"][0]
                if (
                    "TemperatureThresholds" in fan_config
                    and fan_config["TemperatureThresholds"]
                ):
                    for threshold in fan_config["TemperatureThresholds"]:
                        if (
                            "UpThreshold" in threshold
                            and "FanSpeed" in threshold
                        ):
                            curve_points.append(
                                (
                                    threshold["UpThreshold"],
                                    threshold["FanSpeed"],
                                )
                            )
                elif (
                    "FanSpeedPercentageOverrides" in fan_config
                    and fan_config["FanSpeedPercentageOverrides"]
                ):
                    overrides = fan_config["FanSpeedPercentageOverrides"]
                    if (
                        overrides
                        and isinstance(overrides, list)
                        and len(overrides) > 0
                    ):
                        if (
                            isinstance(overrides[0], dict)
                            and "Temperature" in overrides[0]
                            and "FanSpeed" in overrides[0]
                        ):
                            for override in overrides:
                                curve_points.append(
                                    (
                                        override["Temperature"],
                                        override["FanSpeed"],
                                    )
                                )
                        elif (
                            isinstance(overrides[0], dict)
                            and "FanSpeedPercentage" in overrides[0]
                            and "FanSpeedValue" in overrides[0]
                        ):
                            min_temp, max_temp = 30, 90
                            step = (
                                (max_temp - min_temp) / (len(overrides) - 1)
                                if len(overrides) > 1
                                else 10
                            )
                            for i, override in enumerate(overrides):
                                curve_points.append(
                                    (
                                        min_temp + i * step,
                                        override["FanSpeedPercentage"],
                                    )
                                )

                if curve_points:
                    self.points = [
                        (round(p[0]), round(p[1])) for p in curve_points
                    ]
                else:
                    QMessageBox.information(
                        self,
                        "Note",
                        f"No fan curve data in '{profile_name}'. Using default.",
                    )
                    self.reset_curve(update_dropdown=False)
            else:
                QMessageBox.warning(
                    self,
                    "Warning",
                    f"Profile '{profile_name}' no fan config. Using default.",
                )
                self.reset_curve(update_dropdown=False)
            self.update_plot()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load profile '{profile_name}': {str(e)}",
            )
            self.reset_curve(update_dropdown=False)
            self.update_plot()

    def apply_selected_profile(self):
        """Applies the currently selected profile using 'nbfc' command with pkexec."""
        profile_name = self.profile_dropdown.currentText()
        if not profile_name:
            QMessageBox.warning(self, "Warning", "Please select a profile.")
            return
        try:
            subprocess.run(
                ["pkexec", "nbfc", "config", "-a", profile_name],
                check=True,
                capture_output=True,
                text=True,
            )
            QMessageBox.information(
                self, "Success", f"Applied fan profile '{profile_name}'."
            )
        except subprocess.CalledProcessError as e:
            error_details = f"Error: {e.stderr or e.stdout or str(e)}"
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to apply profile '{profile_name}'.\n{error_details}",
            )
        except FileNotFoundError:
            QMessageBox.critical(
                self, "Error", "pkexec or nbfc command not found."
            )

    def save_custom_profile(self):
        """Saves the current fan curve as a new NBFC profile .json file."""
        name = self.custom_profile_name.text().strip()
        if not name:
            QMessageBox.warning(
                self, "Warning", "Please enter a profile name."
            )
            return
        if any(c in name for c in '/\\:*?"<>|'):
            QMessageBox.warning(
                self, "Warning", "Profile name contains invalid characters."
            )
            return

        if self.current_config:
            config = self.current_config.copy()
            config["NotebookModel"] = name
        else:
            config = {
                "NotebookModel": name,
                "Author": "Ryzen Master Commander",
                "EcPollInterval": 5000,
                "ReadWriteWords": False,
                "CriticalTemperature": 85,
                "FanConfigurations": [
                    {
                        "ReadRegister": 122,
                        "WriteRegister": 122,
                        "MinSpeedValue": 0,
                        "MaxSpeedValue": 255,
                        "ResetRequired": True,
                        "FanSpeedResetValue": 0,
                        "FanDisplayName": "Fan",
                    }
                ],
            }
        if (
            "FanConfigurations" not in config
            or not config["FanConfigurations"]
        ):
            config["FanConfigurations"] = [
                {"ReadRegister": 122, "WriteRegister": 122}
            ]
        if not isinstance(config["FanConfigurations"], list):
            config["FanConfigurations"] = [config["FanConfigurations"]]
        if not config["FanConfigurations"]:
            config["FanConfigurations"].append({})

        thresholds = []
        if self.points:
            t_0, s_0 = self.points[0]
            thresholds.append(
                {
                    "UpThreshold": int(t_0),
                    "DownThreshold": int(max(0, t_0 - 5)),
                    "FanSpeed": float(s_0),
                }
            )
            for i in range(1, len(self.points)):
                t_curr, s_curr = self.points[i]
                t_prev, _ = self.points[i - 1]
                down_thresh = min(int(t_prev + 1), int(t_curr))
                down_thresh = max(0, down_thresh)
                thresholds.append(
                    {
                        "UpThreshold": int(t_curr),
                        "DownThreshold": down_thresh,
                        "FanSpeed": float(s_curr),
                    }
                )
        config["FanConfigurations"][0]["TemperatureThresholds"] = thresholds
        config["FanConfigurations"][0].pop("FanSpeedPercentageOverrides", None)

        try:
            temp_dir = os.path.expanduser(
                "~/.config/ryzen-master-commander/temp_profiles"
            )
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = os.path.join(temp_dir, f"{name}.json")
            with open(temp_file, "w") as f:
                json.dump(config, f, indent=2)
            target_file = os.path.join(self.nbfc_configs_dir, f"{name}.json")
            subprocess.run(
                ["pkexec", "cp", temp_file, target_file],
                check=True,
                capture_output=True,
                text=True,
            )
            QMessageBox.information(
                self, "Success", f"Saved profile to {target_file}"
            )
            self.refresh_ui_after_save(name)
        except subprocess.CalledProcessError as e:
            error_details = f"Error: {e.stderr or e.stdout or str(e)}"
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save profile with pkexec.\n{error_details}",
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save profile: {str(e)}"
            )

    def refresh_ui_after_save(self, saved_profile_name):
        """Refreshes the profile list and selects the newly saved profile."""
        self.profiles_list = self.get_available_profiles()
        self.profile_dropdown.clear()
        self.profile_dropdown.addItems(self.profiles_list)
        if saved_profile_name in self.profiles_list:
            self.profile_dropdown.setCurrentText(saved_profile_name)
        elif self.profiles_list:
            self.profile_dropdown.setCurrentIndex(0)

    def update_plot(self):
        """Updates the fan curve plot with current points and highlights."""
        self.points = sorted(
            [(round(p[0]), round(p[1])) for p in self.points],
            key=lambda p: p[0],
        )
        temps, speeds = zip(*self.points) if self.points else ([], [])
        self.curve_item.setData(temps, speeds)

        self.selected_point_item.clear()
        highlight_idx = (
            self.drag_point_index
            if self.drag_point_index is not None
            else self.hover_point_index
        )
        if highlight_idx is not None and 0 <= highlight_idx < len(self.points):
            px, py = self.points[highlight_idx]
            self.selected_point_item.addPoints([px], [py])

    def reset_curve(self, update_dropdown=True):
        """Resets the fan curve to a default state."""
        self.points = [(20, 0), (40, 30), (60, 60), (80, 100)]
        if update_dropdown:
            self.current_config = None
            self.custom_profile_name.setText("MyCustomProfile")
        self.hover_point_index = None
        self.drag_point_index = None
        self.is_dragging = False
        self.coord_text_item.hide()
        self.update_plot()
