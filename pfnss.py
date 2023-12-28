from datetime import datetime, UTC
import configparser
import json
from random import shuffle, seed
import sqlite3
import sys
import time
from tkinter import Canvas, Tk, Button, Label, Frame

from PIL import Image, ImageTk
import requests

win32gui = None
try:
    # pip install pywin32 -> This will install the libs that are required
    import win32gui, win32con
except:
    print("No win32 support")

class PictureFileNameSaver:
    db_file_name = None
    file_ids = None
    last_seen = None
    current_id = None
    current_idx = 0
    paused = False
    info = None
    info_paused = None
    info_fname = None
    info_ids = None
    looping = False
    reverse = False

    log_url = None
    max_skip_count = None
    switch_secs = None
    terminate = False

    root = None
    canvas = None
    img = None
    screen_width = None
    screen_height = None
    screen_ratio = None
    prefix = None

    def __init__(self):
        self.root = root = Tk()
        root.attributes("-fullscreen", True)
        self.canvas = Canvas(root, bg="black", highlightthickness=0)
        self.canvas.pack(expand=1, fill="both")
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        self.screen_ratio = self.screen_width / self.screen_height

        config = configparser.ConfigParser()
        config.read(sys.argv[1])
        self.log_url = config["server"].get("logUrl", "")
        self.max_skip_count = int(config["server"].get("maxSkipCount", "5"))
        self.switch_secs = int(config["saver"].get("switchSeconds", "30"))

        do_hide = True if config["saver"].get("doHide", "True") == "True" else False
        if win32gui and do_hide:
            hide = win32gui.GetForegroundWindow()
            win32gui.ShowWindow(hide, win32con.SW_HIDE)

        self.db_file_name = config["data"].get("dbFileName", "c:/work/git/pfnss/pfnss.db")
        self.prefix = config["saver"].get("prefix", "")
        self.file_ids = [i for i in range(1, int(config["data"].get("maxFileId", "10")))]
        shuffle_seed = int(config["data"].get("seed", "31056"))
        seed(shuffle_seed)
        shuffle(self.file_ids)
        self.last_seen = self.file_ids[0]
        try:
            with sqlite3.connect(self.db_file_name) as db:
                last_ts, self.last_seen = db.execute("select ts, file_id from log where ts = (select max(ts) from log)").fetchone()
                print(f"{self.last_seen} was seen at {last_ts}")
        except Exception as ex:
            print(f"No log check: {ex}")

        root.bind_all('<Key>', self.keyboard_event)
        root.bind_all('<Motion>', self.motion_event)

        self.info = Frame(self.canvas)
        self.info_paused = Label(self.info, text="Paused", fg="white", bg="red", font="TkTextFont 10")
        self.info_fname = Label(self.info, text="fname", fg="black", bg="lightgrey", font="TkTextFont 10")
        self.info_fname.grid(column=2,row=1)
        self.info_ids = Label(self.info, text="ids", fg="blue", bg="lightgrey", font="TkTextFont 10")
        self.info_ids.grid(column=3,row=1)

    def get_file_id(self):
        try:
            self.current_id = self.file_ids[self.current_idx]
        except:
            self.current_id = 1
        return self.current_id
    
    def prepare_image(self, fname):
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
        x = int((screen_width - w) / 2) if w < screen_width else 0
        y = int((screen_height - h) / 2) if h < screen_height else 0

        self.img = ImageTk.PhotoImage(jpg.resize((int(w), int(h))))
        return self.canvas.create_image(x, y, image=self.img, anchor="nw")       

    def display(self, fname):
        c_image = self.prepare_image(fname)

        canvas = self.canvas
        self.info_fname["text"] = fname
        self.info_ids["text"] = f"{self.current_id} [{self.current_idx}]"
        c_info = canvas.create_window(self.screen_width / 2, 0, anchor="n", window=self.info)

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
                if self.paused:
                    break
            if not self.paused:
                loop = False
                self.info_paused.grid_forget()
            else:
                self.info_paused.grid(column=1,row=1)
        self.info_paused.grid_forget()
        canvas.delete(c_info, c_image)

    def end_loop(self, ev=None):
        if ev:
            print(f"Ending event type {ev.type}")
        self.looping = False
        self.terminate = True
        try:
            if self.root:
                self.root.destroy()
                self.root = None
                print("Clean finish")
        except:
            print("Messy finish")

    def keyboard_event(self, ev):
        if ev.keysym in ["Left", "Up"] or ev.char == 'p':
            self.previous()
        elif ev.keysym in ["Right", "Down"] or ev.char == 'n':
            self.next()
        elif ev.keycode == 27 or ev.char == 'q' or ev.keysym == "Escape":
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
            print(f"keycode: {ev.keycode} char: '{ev.char}' keysym: {ev.keysym}")

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

    scan_to_start = True
    skip_count = 0
    app.looping = True
    while app.looping:
        app.current_idx = 0
        file_count = len(app.file_ids)
        while app.current_idx < file_count:
            if app.terminate or not app.looping:
                app.end_loop()
                break
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
            if app.log_url and skip_count < app.max_skip_count:
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
    app.end_loop()
