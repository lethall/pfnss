import sys
from tkinter import *

with open("c:/work/git/pfnss/ss.log", "a") as f:
    print(f"got these args: {' '.join(sys.argv[1:])}", file=f)

root = Tk()
root.attributes("-fullscreen", True)
root.attributes("-alpha", 0.3)
canvas = Canvas(root)
canvas.pack(expand=1, fill="both")

screenWidth = canvas.winfo_screenwidth()
screenHeight = canvas.winfo_screenheight()

canvas.create_oval(100, 100, 200, 200, fill="red")
# canvas.create_image()

def end_loop(code):
    print(f"Ending pfnss {code}")
    root.destroy()

root.bind_all('<Key>', end_loop)
root.bind_all('<Motion>', end_loop)
root.mainloop()
