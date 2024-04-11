import ttkbootstrap as ttk
from app.main_window import MainWindow

def main():
    root = ttk.Window(themename="darkly")
    root.title("Ryzen Master and Commander")
    root.geometry("300x640")  # Set the initial window size to 800x600 pixels
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()