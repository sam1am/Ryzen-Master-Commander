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
        |-- ryzen-master-commander-1.0.5.tar.gz
        |-- ryzen-master-commander-1.0.6-1-any.pkg.tar.zst
        |-- ryzen-master-commander-1.0.6.tar.gz
        |-- ryzen-master-commander-1.0.7-1-any.pkg.tar.zst
        |-- ryzen-master-commander-1.0.7.tar.gz
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
## File: setup.py

```py
from setuptools import setup, find_packages
import os

# All paths for data_files must be relative to this setup.py file.

fan_profiles_source_dir = 'share/ryzen-master-commander/fan_profiles'
tdp_profiles_source_dir = 'share/ryzen-master-commander/tdp_profiles'

data_files = [
    # Target installation directory, [list of source files relative to setup.py]
    ('share/applications', ['share/applications/ryzen-master-commander.desktop']),
    (fan_profiles_source_dir, # Target dir is same as source for these
     [os.path.join(fan_profiles_source_dir, f) for f in os.listdir(fan_profiles_source_dir) if os.path.isfile(os.path.join(fan_profiles_source_dir, f))]),
    (tdp_profiles_source_dir, # Target dir is same as source for these
     [os.path.join(tdp_profiles_source_dir, f) for f in os.listdir(tdp_profiles_source_dir) if os.path.isfile(os.path.join(tdp_profiles_source_dir, f))]),
    # REMOVED 'bin/ryzen-master-commander' from here.
    # Keep ryzen-master-commander-helper if it's a separate script not managed by entry_points
    ('bin', ['bin/ryzen-master-commander-helper']), # Assuming helper is still needed as a separate file
    ('share/polkit-1/actions', ['polkit/com.merrythieves.ryzenadj.policy']),
]

# Add icon files using relative paths
for size in ['16x16', '32x32', '64x64', '128x128']:
    icon_source_file_rel = os.path.join('share/icons/hicolor', size, 'apps', 'ryzen-master-commander.png')
    icon_target_dir = os.path.join('share/icons/hicolor', size, 'apps')
    if os.path.isfile(icon_source_file_rel):
        data_files.append((icon_target_dir, [icon_source_file_rel]))

setup(
    #get version from ./ver.txt
    version = open('version.txt').read().strip(),
    name="ryzen-master-commander",
    author="sam1am",
    author_email="noreply@merrythieves.com",
    description="TDP and fan control for AMD Ryzen processors",
    url="https://github.com/sam1am/Ryzen-Master-Commander",
    packages=['ryzen_master_commander', 'ryzen_master_commander.app'],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    license_files=('LICENSE',),
    install_requires=[
        "PyQt5",
        "pyqtgraph",
        "numpy",
        "Pillow",
        "pystray",
    ],
    python_requires=">=3.8",
    data_files=data_files,
    entry_points={
        'console_scripts': [
            'ryzen-master-commander=ryzen_master_commander.main:main', # This will create /usr/bin/ryzen-master-commander
        ],
    },
)
```
---
## File: share/applications/ryzen-master-commander.desktop

```desktop
[Desktop Entry]
Name=Ryzen Master Commander
Comment=AMD Ryzen TDP and Fan Control
GenericName=Hardware Control
Exec=ryzen-master-commander %U
Icon=ryzen-master-commander
Terminal=false
Type=Application
Categories=System;Settings;HardwareSettings;
Keywords=AMD;Ryzen;TDP;Fan;Control;
StartupNotify=true
StartupWMClass=ryzen-master-commander
Path=/usr/share/ryzen-master-commander
```
---
