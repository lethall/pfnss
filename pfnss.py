from datetime import datetime
import configparser
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


class PictureFileNameSaver:
    config = None
    db_file_name = None
    file_ids = None
    last_seen = None
    log_url = None
    switch_secs = None
    do_hide = None
    terminate = False

    root = None
    canvas = None
    screen_width = None
    screen_height = None
    screen_ratio = None

    def __init__(self):
        self.config = config = configparser.ConfigParser()
        config.read(sys.argv[1])
        self.db_file_name = config["data"].get("dbFileName", "c:/work/git/pfnss/pfnss.db")
        self.file_ids = [i for i in range(1, int(config["data"].get("maxFileId", "10")))]
        seed(int(config["server"].get("seed", "31056")))
        self.log_url = config["server"].get("logUrl", "http://192.168.1.189:8800/pfnss")
        self.switch_secs = int(config["saver"].get("switchSeconds", "30"))
        self.do_hide = True if config["saver"].get("doHide", "True") == "True" else False

        shuffle(self.file_ids)
        self.last_seen = self.file_ids[0]
        try:
            with sqlite3.connect(self.db_file_name) as db:
                last_ts, self.last_seen = db.execute("select ts, file_id from log where ts = (select max(ts) from log)").fetchone()
                print(f"{self.last_seen} was seen at {last_ts}")
        except Exception as ex:
            print(f"No log check: {ex}")

        self.root = Tk()
        self.root.bind_all('<Key>', self.end_loop)
        self.root.bind_all('<Motion>', self.end_loop)
        self.root.attributes("-fullscreen", True)
        self.canvas = canvas = Canvas(self.root, bg="black", borderwidth=0, relief="flat")
        canvas.pack(expand=1, fill="both")
        self.screen_width = canvas.winfo_screenwidth()
        self.screen_height = canvas.winfo_screenheight()
        self.screen_ratio = self.screen_width / self.screen_height

    def display(self, fname, file_no):
        global terminate
        jpg = Image.open(fname)
        w, h = jpg.size
        img_ratio = w / h
        screen_height = self.screen_height
        screen_width = self.screen_width
        if img_ratio < self.screen_ratio:
            h = screen_height
            w = h * img_ratio
        else:
            w = screen_width
            h = w / img_ratio
        img = ImageTk.PhotoImage(jpg.resize((int(w), int(h))))
        x = int((screen_width - w) / 2) if w < screen_width else 0
        y = int((screen_height - h) / 2) if h < screen_height else 0
        canvas = self.canvas
        c_i = canvas.create_image(x, y, image=img, anchor="nw")
        # fname = f"{file_no} - {fname}"
        half_width = screen_width / 2
        c_t1 = canvas.create_text(half_width, 15, text=fname, justify="left", fill="black", font="Courier 12")
        c_t2 = canvas.create_text(half_width + 2, 17, text=fname, justify="left", fill="lime", font="Courier 12")
        c_t3 = canvas.create_text(half_width, 35, text=str(file_no), justify="left", fill="black", font="Courier 12")
        c_t4 = canvas.create_text(half_width + 2, 37, text=str(file_no), justify="left", fill="lime", font="Courier 12")
        for i in range(self.switch_secs * 10):
            self.root.update()
            if self.terminate:
                exit()
            time.sleep(0.1)
        canvas.delete(c_t1, c_t2, c_i)

    def end_loop(self, code):
        print(f"Ending pfnss {code}")
        self.terminate = True
        self.root.destroy()

print(f"got these args: {' '.join(sys.argv[1:])}")


if __name__ == '__main__':
    app = PictureFileNameSaver()
    if app.do_hide:
        hide = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(hide, win32con.SW_HIDE)

    while True:
        scan_to_start = True
        for file_no in app.file_ids:
            if scan_to_start and file_no != app.last_seen:
                continue
            if scan_to_start:
                print(f"Starting with {file_no}")
                scan_to_start = False
            with sqlite3.connect(app.db_file_name) as db:
                fname = db.execute("select name from files where id = ?", (file_no,)).fetchone()[0]
                if (".jpg" not in fname) and (".jpeg" not in fname):
                    continue
                ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
                db.execute("insert into log (ts, file_id) values (?,?)", (ts, file_no))
                db.commit()
                try:
                    o = json.dumps({"ts": ts, "file_no": file_no, "name": fname})
                    requests.post(app.log_url, headers={"Content-Type": "application/json"}, data=o)
                except:
                    pass
                try:
                    app.display(f"{fname}", file_no)
                except Exception as ex:
                    print(ex)
