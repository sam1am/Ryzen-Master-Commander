import ttkbootstrap as ttk
from ryzen_master_commander.app.main_window import MainWindow
import os
from ryzen_master_commander.singleton import SingleInstance
# import matplotlib
# matplotlib.use('TkAgg')

_singleton = None

def main():
    global _singleton
    
    # Create the singleton at the very beginning of main
    # This will exit the program if another instance is already running
    _singleton = SingleInstance("ryzen-master-commander")
    
    # The rest of your main function continues as normal
    theme = detect_system_theme()
    root = ttk.Window(themename=theme)
    root.title("Ryzen Master and Commander")

    root.geometry("500x950")
    
    # Set the window icon immediately
    try:
        icon_paths = [
            "/usr/share/icons/hicolor/128x128/apps/ryzen-master-commander.png",
            "./share/icons/hicolor/128x128/apps/ryzen-master-commander.png",
            "./img/icon.png"
        ]
        
        for path in icon_paths:
            if os.path.exists(path):
                from PIL import Image, ImageTk
                icon = ImageTk.PhotoImage(Image.open(path))
                root.iconphoto(False, icon)  # Changed to False to not affect future windows
                break
                
        # Set window class for KDE
        root.tk.call('wm', 'class', root._w, "ryzen-master-commander")
    except Exception as e:
        print(f"Error setting application icon: {e}")
    
    # Center window first, before adding any content
    center_window(root, 500, 950)
    
    # Ensure the window is visible and drawn before creating MainWindow
    root.update_idletasks()
    
    # Now create the main window using our already configured root
    app = MainWindow(root)
    
    # Start the main loop with the fully configured window
    root.mainloop()

def center_window(window, width, height):
    """Center the window on the screen."""
    # Get screen dimensions
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # Calculate position coordinates
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    
    # Set window position
    window.geometry(f"{width}x{height}+{x}+{y}")

def ensure_window_visible(root):
    if not root.winfo_viewable():
        root.deiconify()
    root.attributes('-topmost', True)
    root.update()
    root.attributes('-topmost', False)
    root.state('normal')
    root.focus_force()

def detect_system_theme():
    """Detect if system is using dark or light theme and return appropriate ttkbootstrap theme"""
    import os
    import subprocess
    
    # Default fallback theme
    default_theme = "darkly"
    
    try:
        # For KDE Plasma
        if os.environ.get('XDG_CURRENT_DESKTOP') == 'KDE':
            result = subprocess.run(
                ["kreadconfig5", "--group", "General", "--key", "ColorScheme"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                kde_theme = result.stdout.strip().lower()
                return "darkly" if "dark" in kde_theme else "cosmo"
                
        # For GNOME
        elif os.environ.get('XDG_CURRENT_DESKTOP') in ['GNOME', 'Unity']:
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                capture_output=True, text=True
            )
            if result.returncode == 0 and "dark" in result.stdout.lower():
                return "darkly"
            else:
                return "cosmo"
    except Exception as e:
        print(f"Error detecting system theme: {e}")
    
    return default_theme


if __name__ == "__main__":
    app.main()