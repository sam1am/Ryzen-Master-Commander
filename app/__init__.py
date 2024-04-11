import ttkbootstrap as ttk
from app.main_window import MainWindow

def main():
    root = ttk.Window(themename="darkly")
    root.title("Ryzen Master and Commander")
    root.geometry("300x640")
    app = MainWindow(root)
    root.mainloop()