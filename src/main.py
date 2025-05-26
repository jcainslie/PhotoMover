import tkinter as tk
from gui.main_window import PhotoMoverApp

def main():
    root = tk.Tk()
    app = PhotoMoverApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()