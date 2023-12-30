import configparser
import json
from random import shuffle, seed
import sys
import time
from tkinter import Canvas, Tk, Label, Frame

from PIL import Image, ImageTk
import requests

from .db import Data
from .config import Configure
from .photo_info import PhotoInfo
from . import CATEGORIES

win32gui = None
try:
    # pip install pywin32 -> This will install the libs that are required
    import win32gui, win32con
except:
    print("No win32 support")

class PictureFileNameSaver:
    db_file_name = None
    data = None
    file_ids = None
    last_seen = None
    current_id = None
    current_idx = 0
    paused = False
    info = None
    info_paused = None
    info_fname = None
    info_ids = None
    info_mark = None
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
    font = "TkTextFont 10"
    key_func_id = None
    motion_func_id = None

    def __init__(self) -> None:
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
        self.max_skip_count = config["server"].getint("maxSkipCount", 5)
        self.switch_secs = config["saver"].getint("switchSeconds", 30)
        self.show_fname = config["saver"].getboolean("showFileName", True)
        self.show_id = config["saver"].getboolean("showId", True)
        self.show_seq = config["saver"].getboolean("showSequence", True)

        do_hide = True if config["saver"].get("doHide", "True") == "True" else False
        if win32gui and do_hide:
            hide = win32gui.GetForegroundWindow()
            win32gui.ShowWindow(hide, win32con.SW_HIDE)

        self.db_file_name = config["data"].get("dbFileName", "c:/work/git/pfnss/pfnss.db")
        self.data = Data(self.db_file_name)
        self.prefix = config["saver"].get("prefix", "")
        max_file_id = 10
        try:
            max_file_id = config["data"].getint("maxFileId", 10)
            if max_file_id < 1:
                max_file_id = self.data.get_file_count()
        except:
            raise SystemExit("Failed to get file IDs")
        self.file_ids = [i for i in range(1, max_file_id + 1)]
        shuffle_seed = config["data"].getint("seed", 31056)
        seed(shuffle_seed)
        shuffle(self.file_ids)
        self.last_seen = self.file_ids[0]
        try:
            self.last_seen = self.data.get_last_seen()
        except Exception as ex:
            print(f"No log check: {ex}")

        self.info = Frame(self.canvas)
        self.info_paused = Label(self.info, text="Paused", fg="white", bg="red", font=self.font)
        if self.show_fname:
            self.info_fname = Label(self.info, text="fname", fg="white", bg="black", font=self.font)
            self.info_fname.grid(column=2,row=1)
        if self.show_id or self.show_seq:
            self.info_ids = Label(self.info, text="ids", fg="white", bg="blue", font=self.font)
            self.info_ids.grid(column=3,row=1)
        self.info_mark = Label(self.info, font=self.font)
        
        self.enable_events()
    
    def enable_events(self) -> None:
        self.key_func_id = self.root.bind('<Key>', self.keyboard_event)
        self.motion_func_id = self.root.bind('<Motion>', self.motion_event)

    def disable_events(self) -> None:
        self.root.unbind('<Key>', self.key_func_id)
        self.root.unbind('<Motion>', self.motion_func_id)

    def get_file_id(self) -> int:
        try:
            self.current_id = self.file_ids[self.current_idx]
        except:
            self.current_id = 1
        return self.current_id
    
    def prepare_image(self, fname) -> int:
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

    def display_mark(self):
        mark = self.data.get_last_mark(self.current_id)
        if mark and mark != " ":
            if mark[0] == "s":
                msg = "Save"
                fg_color = "white"
                bg_color = "darkgreen"
            elif mark[0] == "d":
                msg = "Delete"
                fg_color = "darkred"
                bg_color = "yellow"
            self.info_mark["bg"] = bg_color
            self.info_mark["fg"] = fg_color
            self.info_mark["text"] = msg
            self.info_mark.grid(column=4, row=1)
        else:
            self.info_mark.grid_forget()

    def display(self, fname) -> None:
        c_image = self.prepare_image(fname)
        self.display_mark()

        canvas = self.canvas
        if self.show_fname:
            self.info_fname["text"] = fname
        ids = []
        if self.show_id:
            ids.append(f"{self.current_id}")
        if self.show_seq:
            ids.append(f"[{self.current_idx}]")
        if ids:
            self.info_ids["text"] = " ".join(ids)
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
        canvas.delete(c_info, c_image)

    def end_loop(self, ev=None) -> None:
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

    def keyboard_event(self, ev) -> None:
        if ev.keysym in ["Left", "Up"] or ev.char == 'p':
            self.previous()
        elif ev.keysym in ["Right", "Down"] or ev.char == 'n':
            self.next()
        elif ev.keycode == 27 or ev.char == 'q' or ev.keysym == "Escape":
            self.end_loop(ev)
        elif ev.char == 's':
            self.mark(ev.char)
        elif ev.char == 'd':
            self.mark(ev.char)
        elif ev.char == 'r':
            self.mark(' ')
        elif ev.char == ' ' or ev.keycode == 13:
            self.resume()
        elif ev.char == 'e':
            self.edit()
        elif ev.char == 'm':
            self.mail()
        elif ev.char == 'i':
            self.disable_events()
            try:
                info_dialog = PhotoInfo(self.root)
                if not info_dialog.photo_name:
                    self.enable_events()
                    return
                selected_cats = [CATEGORIES[selected] for selected in info_dialog.chosen_categories]
                self.data.save_photo_info(self.current_id, info_dialog.photo_name,
                                          info_dialog.photo_description, selected_cats)
            except Exception as exc:
                print(exc)
            self.enable_events()
        else:
            print(f"keycode: {ev.keycode} char: '{ev.char}' keysym: {ev.keysym}")

    def mark(self, mark="save") -> None:
        self.data.save(self.current_id, mark[0])
        self.display_mark()

    def resume(self):
        if self.paused:
            print(f"resume {self.current_id}")
            self.info_paused.grid_forget()
            self.paused = False
        else:
            print(f"pause {self.current_id}")
            self.paused = True
            self.info_paused.grid(column=1, row=1)


    def edit(self) -> None:
        print(f"edit {self.current_id}")

    def mail(self) -> None:
        print(f"mail {self.current_id}")

    def motion_event(self, ev) -> None:
        self.end_loop(ev)

    def previous(self) -> None:
        self.reverse = True
        if self.current_idx > 0:
            self.current_idx -= 1
        else:
            self.current_idx = len(self.file_ids) - 1
        print(f"reversed to {self.get_file_id()} [{self.current_idx}]")

    def next(self) -> None:
        if self.current_idx < (len(self.file_ids) - 1):
            self.current_idx += 1
        else:
            self.current_idx = 0
        print(f"advanced to {self.get_file_id()} [{self.current_idx}]")

    def run(self) -> None:
        scan_to_start = True
        skip_count = 0
        self.looping = True
        while self.looping:
            self.current_idx = 0
            file_count = len(self.file_ids)
            while self.current_idx < file_count:
                if self.terminate or not self.looping:
                    self.end_loop()
                    break
                if scan_to_start:
                    last_seen = self.last_seen
                    idx = 0
                    for file_no in self.file_ids:
                        if file_no == last_seen:
                            break
                        idx += 1
                        continue
                    print(f"Starting with {file_no} [{idx}]")
                    scan_to_start = False
                    self.current_idx = idx
                current_id = self.get_file_id()
                fname = self.data.get_file_name(current_id)
                if not fname:
                    self.next()
                    continue

                if self.log_url and skip_count < self.max_skip_count:
                    try:
                        o = json.dumps({"ts": ts, "file_no": current_id, "name": fname})
                        requests.post(self.log_url, headers={"Content-Type": "application/json"}, data=o)
                        print("reset skip count")
                        skip_count = 0
                    except Exception as e:
                        print(f"{skip_count} < {self.max_skip_count} - {e}")
                        skip_count += 1
                try:
                    self.display(f"{fname}")
                except Exception as ex:
                    print(ex)
                if self.reverse:
                    self.reverse = False
                else:
                    self.current_idx += 1
        self.end_loop()
