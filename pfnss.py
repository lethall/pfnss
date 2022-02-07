import os
from random import shuffle
import sqlite3
import sys
from time import sleep
from tkinter import *
from tkinter import ttk

from PIL import Image, ImageTk

# pip install pywin32 -> This will install the libs that are required
import win32gui, win32con

hide = win32gui.GetForegroundWindow()
#win32gui.ShowWindow(hide , win32con.SW_HIDE)

#home = os.getenv('HOME')
#with open("c:/work/git/pfnss/ss.log", "a") as f:
home = "c:"
with open(f"{home}/work/git/pfnss/ss.log", "a") as f:
    print(f"got these args: {' '.join(sys.argv[1:])}", file=f)

root = Tk()
root.attributes("-fullscreen", True)
canvas = Canvas(root)
canvas.pack(expand=1, fill="both")

screenWidth = canvas.winfo_screenwidth()
screenHeight = canvas.winfo_screenheight()
screenRatio = screenWidth / screenHeight
terminate = False

def display(fname, file_no):
    global terminate
    jpg = Image.open(fname)
    w, h = jpg.size
    img_ratio = w / h
    if img_ratio < screenRatio:
        h = screenHeight
        w = h * img_ratio
    else:
        w = screenWidth
        h = w / screenRatio
    img = ImageTk.PhotoImage(jpg.resize((int(w), int(h))))
    x = int((screenWidth - w) / 2) if w < screenWidth else 0
    y = int((screenHeight - h) / 2) if h < screenHeight else 0
    c_i = canvas.create_image(x, y, image=img, anchor="nw")
    #fname = f"{file_no} - {fname}"
    c_t1 = canvas.create_text(screenWidth / 2, 15, text=fname, justify="left", fill="black", font="Courier 12")
    c_t2 = canvas.create_text(screenWidth / 2 + 2, 17, text=fname, justify="left", fill="lime", font="Courier 12")
    c_t3 = canvas.create_text(screenWidth / 2, 35, text=str(file_no), justify="left", fill="black", font="Courier 12")
    c_t4 = canvas.create_text(screenWidth / 2 + 2, 37, text=str(file_no), justify="left", fill="lime", font="Courier 12")
    for i in range(300):
        root.update()
        if terminate:
            exit()
        sleep(0.1)
    canvas.delete(c_t1, c_t2, c_i)

def end_loop(code):
    global terminate
    print(f"Ending pfnss {code}")
    terminate = True
    root.destroy()

root.bind_all('<Key>', end_loop)
root.bind_all('<Motion>', end_loop)

while True:
    file_ids = [i for i in range(1,35357)]
    shuffle(file_ids)
    for file_no in file_ids:
        with sqlite3.connect(f"{home}/work/git/pfnss/pfnss.db") as db:
            fname = db.execute("select name from files where id = ?", (file_no,)).fetchone()[0]
            try:
                display(f"{fname}", file_no)
            except Exception as ex:
                print(ex)
