from datetime import datetime
import json
import os
from random import shuffle, seed
import sqlite3
import sys
import time
from tkinter import Canvas, Tk
from tkinter import ttk

from PIL import Image, ImageTk
import requests

# pip install pywin32 -> This will install the libs that are required
import win32gui, win32con

seed(31056)
file_ids = [i for i in range(1,35357)]
log_url = "http://192.168.1.189:8800/pfnss"
switch_secs = 20

hide = win32gui.GetForegroundWindow()
win32gui.ShowWindow(hide, win32con.SW_HIDE)

root = Tk()
root.attributes("-fullscreen", True)
canvas = Canvas(root)
canvas.pack(expand=1, fill="both")

screenWidth = canvas.winfo_screenwidth()
screenHeight = canvas.winfo_screenheight()
screenRatio = screenWidth / screenHeight
terminate = False

# home = os.getenv('HOME')
# with open("c:/work/git/pfnss/ss.log", "a") as f:
home = "c:"
with open(f"{home}/work/git/pfnss/ss.log", "a") as f:
    print(f"got these args: {' '.join(sys.argv[1:])}", file=f)

shuffle(file_ids)
last_seen = file_ids[0]
try:
    with sqlite3.connect(f"{home}/work/git/pfnss/pfnss.db") as db:
        last_ts, last_seen = db.execute("select ts, file_id from log where ts = (select max(ts) from log)").fetchone()
        print(f"{last_seen} was seen at {last_ts}")
except Exception as ex:
    print(f"No log check: {ex}")


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
    for i in range(switch_secs * 10):
        root.update()
        if terminate:
            exit()
        time.sleep(0.1)
    canvas.delete(c_t1, c_t2, c_i)


def end_loop(code):
    global terminate
    print(f"Ending pfnss {code}")
    terminate = True
    root.destroy()


if __name__ == '__main__':
    root.bind_all('<Key>', end_loop)
    root.bind_all('<Motion>', end_loop)

    while True:
        scan_to_start = True
        for file_no in file_ids:
            if scan_to_start and file_no != last_seen:
                continue
            if scan_to_start:
                print(f"Starting with {file_no}")
                scan_to_start = False
            with sqlite3.connect(f"{home}/work/git/pfnss/pfnss.db") as db:
                fname = db.execute("select name from files where id = ?", (file_no,)).fetchone()[0]
                if (".jpg" not in fname) and (".jpeg" not in fname):
                    continue
                ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
                db.execute("insert into log (ts, file_id) values (?,?)", (ts, file_no))
                db.commit()
                try:
                    o = json.dumps({"ts": ts, "file_no": file_no, "name": fname})
                    requests.post(log_url, headers={"Content-Type": "application/json"}, data=o)
                except:
                    pass
                try:
                    display(f"{fname}", file_no)
                except Exception as ex:
                    print(ex)
