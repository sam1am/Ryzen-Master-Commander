from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QSlider,
    QPushButton,
)
from PyQt6.QtCore import Qt


class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_refresh_interval=5):
        super().__init__(parent)
        
        self.setWindowTitle("Settings")
        self.resize(400, 250)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Refresh interval group
        refresh_group = QGroupBox("System Monitoring")
        refresh_layout = QVBoxLayout(refresh_group)
        
        refresh_label = QLabel("Refresh Interval (seconds):")
        refresh_layout.addWidget(refresh_label)
        
        self.refresh_slider = QSlider(Qt.Orientation.Horizontal)
        self.refresh_slider.setRange(1, 30)
        self.refresh_slider.setValue(current_refresh_interval)
        self.refresh_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.refresh_slider.setTickInterval(5)
        refresh_layout.addWidget(self.refresh_slider)
        
        # Value labels below slider
        slider_labels = QHBoxLayout()
        slider_labels.addWidget(QLabel("1"))
        slider_labels.addStretch()
        self.slider_value_label = QLabel(f"{current_refresh_interval}")
        slider_labels.addWidget(self.slider_value_label)
        slider_labels.addStretch()
        slider_labels.addWidget(QLabel("30"))
        refresh_layout.addLayout(slider_labels)
        
        # Update label when slider moves
        self.refresh_slider.valueChanged.connect(
            lambda value: self.slider_value_label.setText(str(value))
        )
        
        layout.addWidget(refresh_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
    def get_refresh_interval(self):
        return self.refresh_slider.value()