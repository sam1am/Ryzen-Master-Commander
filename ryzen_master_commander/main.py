import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ryzen_master_commander.app.main_window import MainWindow

def main():
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Ryzen Master Commander")
    
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