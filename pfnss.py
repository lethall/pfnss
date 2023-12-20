from datetime import datetime, UTC
import configparser
import json
from random import shuffle, seed
import sqlite3
import sys
import time
from tkinter import Canvas, Tk

from PIL import Image, ImageTk
import requests

win32gui = None
try:
    # pip install pywin32 -> This will install the libs that are required
    import win32gui, win32con
except:
    print("No win32 support")

class PictureFileNameSaver:
    config = None
    db_file_name = None
    file_ids = None
    last_seen = None
    current_id = None
    current_idx = 0
    paused = False
    looping = False
    reverse = False
    display_timer = None

    log_url = None
    max_skip_count = None
    switch_secs = None
    do_hide = None
    terminate = False

    root = None
    canvas = None
    screen_width = None
    screen_height = None
    screen_ratio = None
    prefix = None

    def __init__(self):
        self.config = config = configparser.ConfigParser()
        config.read(sys.argv[1])
        self.db_file_name = config["data"].get("dbFileName", "c:/work/git/pfnss/pfnss.db")
        self.file_ids = [i for i in range(1, int(config["data"].get("maxFileId", "10")))]
        seed(int(config["server"].get("seed", "31056")))
        self.log_url = config["server"].get("logUrl", "http://192.168.1.189:8800/pfnss")
        self.max_skip_count = int(config["server"].get("maxSkipCount", "5"))
        self.switch_secs = int(config["saver"].get("switchSeconds", "30"))
        self.prefix = config["saver"].get("prefix", "")
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
        self.root.bind_all('<Key>', self.keyboard_event)
        self.root.bind_all('<Motion>', self.motion_event)
        self.root.attributes("-fullscreen", True)
        self.canvas = canvas = Canvas(self.root, bg="black", highlightthickness=0)
        canvas.pack(expand=1, fill="both")
        self.screen_width = canvas.winfo_screenwidth()
        self.screen_height = canvas.winfo_screenheight()
        self.screen_ratio = self.screen_width / self.screen_height

    def get_file_id(self):
        try:
            self.current_id = self.file_ids[self.current_idx]
        except:
            self.current_id = 1
        return self.current_id

    def display(self, fname):
        jpg = Image.open(self.prefix + fname)
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
        c_t2 = canvas.create_text(half_width + 2, 17, text=fname, justify="left", fill="green", font="Courier 12")
        c_t3 = canvas.create_text(half_width, 35, text=f"{self.current_id} [{self.current_idx}]", justify="left", fill="black", font="Courier 12")
        c_t4 = canvas.create_text(half_width + 2, 37, text=f"{self.current_id} [{self.current_idx}]", justify="left", fill="green", font="Courier 12")
        c_paused = None
        loop = True
        showing_id = self.current_id
        while loop:
            for i in range(self.switch_secs * 10):
                self.root.update()
                if self.terminate:
                    return
                time.sleep(0.1)
                if showing_id != self.get_file_id():
                    loop = False
                    break
                if (self.paused and not c_paused) or (c_paused and not self.paused):
                    break
            if not self.paused:
                loop = False
                if c_paused:
                    print(f"clearing pause {c_paused}")
                    canvas.itemconfigure(c_paused, state="hidden")
                    canvas.delete(c_paused)
                    c_paused = None
            else:
                if not c_paused:
                    c_paused = canvas.create_text(0, 0, text="PAUSED", anchor="nw", fill="red", font="Courier 12")
        canvas.delete(c_t1, c_t2, c_t3, c_t4, c_i)

    def end_loop(self, ev=None):
        if ev:
            print(f"Ending pfnss {ev.type}")
        self.looping = False
        self.terminate = True
        try:
            self.root.destroy()
        except:
            print("Ending")

    def keyboard_event(self, ev):
        if ev.keycode in [37, 38] or ev.char == 'p':
            self.previous()
        elif ev.keycode in [39, 40] or ev.char == 'n':
            self.next()
        elif ev.keycode == 27 or ev.char == 'q':
            self.end_loop(ev)
        elif ev.char == 's':
            self.save()
        elif ev.char == 'd':
            self.delete()
        elif ev.char == ' ' or ev.keycode == 13:
            self.resume()
        elif ev.char == 'e':
            self.edit()
        elif ev.char == 'm':
            self.mail()
        else:
            print(f"keycode: {ev.keycode} char: '{ev.char}'")

    def save(self, mark="save"):
        with sqlite3.connect(self.db_file_name) as db:
            ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            db.execute("insert into marks (ts, file_id, mark) values (?,?,?)", (ts, self.current_id, mark))
            db.commit()

    def delete(self):
        self.save("delete")

    def resume(self):
        if self.paused:
            print(f"resume {self.current_id}")
            self.paused = False
        else:
            print(f"pause {self.current_id}")
            self.paused = True


    def edit(self):
        print(f"edit {self.current_id}")

    def mail(self):
        print(f"mail {self.current_id}")

    def motion_event(self, ev):
        self.end_loop(ev)

    def previous(self):
        self.reverse = True
        if self.current_idx > 0:
            self.current_idx -= 1
        else:
            self.current_idx = len(self.file_ids) - 1
        print(f"reversed to {self.get_file_id()} [{self.current_idx}]")

    def next(self):
        if self.current_idx < (len(self.file_ids) - 1):
            self.current_idx += 1
        else:
            self.current_idx = 0
        print(f"advanced to {self.get_file_id()} [{self.current_idx}]")


print(f"got these args: {' '.join(sys.argv[1:])}")


if __name__ == '__main__':
    app = PictureFileNameSaver()
    if win32gui and app.do_hide:
        hide = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(hide, win32con.SW_HIDE)

    scan_to_start = True
    skip_count = 0
    app.looping = True
    while True:
        app.current_idx = 0
        file_count = len(app.file_ids)
        while app.current_idx < file_count:
            if app.terminate or not app.looping:
                print("Not looping")
                app.end_loop()
                exit(0)
            if scan_to_start:
                last_seen = app.last_seen
                idx = 0
                for file_no in app.file_ids:
                    if file_no == last_seen:
                        break
                    idx += 1
                    continue
                print(f"Starting with {file_no} [{idx}]")
                scan_to_start = False
                app.current_idx = idx
            current_id = app.get_file_id()
            with sqlite3.connect(app.db_file_name) as db:
                fname = db.execute("select name from files where id = ?", (current_id,)).fetchone()[0]
                if (".jpg" not in fname) and (".jpeg" not in fname):
                    app.next()
                    continue
                ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
                db.execute("insert into log (ts, file_id) values (?,?)", (ts, current_id))
                db.commit()
            if skip_count < app.max_skip_count:
                try:
                    o = json.dumps({"ts": ts, "file_no": current_id, "name": fname})
                    requests.post(app.log_url, headers={"Content-Type": "application/json"}, data=o)
                    print("reset skip count")
                    skip_count = 0
                except Exception as e:
                    print(f"{skip_count} < {app.max_skip_count} - {e}")
                    skip_count += 1
            try:
                app.display(f"{fname}")
            except Exception as ex:
                print(ex)
            if app.reverse:
                app.reverse = False
            else:
                app.current_idx += 1