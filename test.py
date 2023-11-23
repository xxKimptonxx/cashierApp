import tkinter as tk
from tkinter import font

root = tk.Tk()

# Get a list of available font families
available_fonts = font.families()

for font_family in available_fonts:
    print(font_family)

root.mainloop()  # This is optional as we're just printing font families without creating any GUI elements
