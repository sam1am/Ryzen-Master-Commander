import ttkbootstrap as ttk
from ryzen_master_commander.app.main_window import MainWindow
import time

def main():
    theme = detect_system_theme()
    root = ttk.Window(themename=theme)
    root.title("Ryzen Master and Commander")
    root.geometry("500x950")
    
    # Center the window on the screen
    center_window(root, 500, 950)
    
    app = MainWindow(root)
    
    # Use after method to ensure window visibility after initialization
    root.after(100, lambda: ensure_window_visible(root))
    
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