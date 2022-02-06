import os
import sys
from tkinter import *

from PIL import Image, ImageTk

# pip install pywin32 -> This will install the libs that are required
# import win32gui, win32con

# hide = win32gui.GetForegroundWindow()
# win32gui.ShowWindow(hide , win32con.SW_HIDE)

#with open("c:/work/git/pfnss/ss.log", "a") as f:
with open(f"{os.getenv('HOME')}/work/git/pfnss/ss.log", "a") as f:
    print(f"got these args: {' '.join(sys.argv[1:])}", file=f)

root = Tk()
root.attributes("-fullscreen", True)
#root.attributes("-alpha", 0.3)
canvas = Canvas(root)
canvas.pack(expand=1, fill="both")

screenWidth = canvas.winfo_screenwidth()
screenHeight = canvas.winfo_screenheight()

# canvas.create_oval(100, 100, 200, 200, fill="red")
img = ImageTk.PhotoImage(
    Image.open("/Users/leehall/Pictures/2003/12/Unknown Location/2003-12-31_05-06-55-dsc00097.jpg")
    .resize((screenWidth, screenHeight)))
canvas.create_image(0, 0, image=img, anchor="nw")

def end_loop(code):
    print(f"Ending pfnss {code}")
    root.destroy()

root.bind_all('<Key>', end_loop)
root.bind_all('<Motion>', end_loop)
root.mainloop()
