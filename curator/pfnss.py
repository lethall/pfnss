import configparser
# import json
from pathlib import Path
from random import shuffle, seed
import shutil
import sys
import time
from tkinter import Canvas, Tk, Label, Frame, W, E

from PIL import Image, ImageTk
# import requests

from .db import Data
from .photo_info import PhotoInfo
from .search import Search
from .help import Help
from . import CATEGORIES

win32gui = None
try:
    # pip install pywin32 -> This will install the libs that are required
    import win32gui, win32con
except:
    print("No win32 support")

class PictureFileNameSaver:
    db_file_name: str = None
    save_folder: Path = None
    data: Data = None
    shuffle_seed: int = 0
    search_params: Search = None
    file_ids: list = None
    last_seen: int = 0
    current_id: int = 0
    current_idx: int = 0
    current_info: PhotoInfo = None
    paused: bool = False
    looping: bool = False
    reverse: bool = False

    # server logging
    log_url = None
    max_skip_count = None
    switch_secs = None
    terminate = False

    # ui
    root = None
    canvas = None
    img = None
    screen_width = None
    screen_height = None
    screen_ratio = None
    prefix = None
    font = "TkTextFont 10"
    desc_font = "TkTextFont 16"
    key_func_id = None
    motion_func_id = None
    motion_enabled = False
    motion_time = 0.0

    # info display widgets
    info = None
    info_paused = None
    info_fname = None
    info_ids = None
    info_mark = None
    info_name = None
    info_desc = None
    info_cats = None

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

        if len(sys.argv) > 2 and sys.argv[2].lower() == "/s":
            self.motion_enabled = True
        self.motion_enabled = config["saver"].getboolean("stopOnMotion", self.motion_enabled)
        if not self.motion_enabled:
            self.canvas["bg"] = "darkgreen"
        self.switch_secs = config["saver"].getint("switchSeconds", 30)
        self.show_fname = config["saver"].getboolean("showFileName", True)
        self.show_id = config["saver"].getboolean("showId", True)
        self.show_seq = config["saver"].getboolean("showSequence", True)

        do_hide = True if config["saver"].get("doHide", "True") == "True" else False
        if win32gui and do_hide:
            hide = win32gui.GetForegroundWindow()
            win32gui.ShowWindow(hide, win32con.SW_HIDE)

        self.prefix = config["data"].get("prefix", "")
        self.save_folder = Path(config["data"].get("saveDirectory", "~/Desktop")).resolve()
        self.db_file_name = config["data"].get("dbFileName", "c:/work/git/pfnss/pfnss.db")
        self.data = Data(self.db_file_name)
        file_count = self.data.get_file_count()
        if not file_count:
            pic_dir = config["data"].get("pictureDirectory", "/Pictures")
            self.data.load_files(pic_dir)
            file_count = self.data.get_file_count()
            if not file_count:
                raise SystemExit(f"No photos in {pic_dir}")
        self.shuffle_seed = config["data"].getint("seed", 31056)
        self.read_data()
        self.info = Frame(self.canvas, bg="black")
        self.info_paused = Label(self.info, text="Paused", fg="white", bg="red", font=self.font)
        if self.show_fname:
            self.info_fname = Label(self.info, text="fname", fg="white", bg="black", font=self.font)
            self.info_fname.grid(column=2,row=1)
        if self.show_id or self.show_seq:
            self.info_ids = Label(self.info, text="ids", fg="white", bg="blue", font=self.font)
            self.info_ids.grid(column=3,row=1)
        self.info_mark = Label(self.info, font=self.font)

        self.info_name = Label(self.info, text="name", fg="red", bg="black", font=self.desc_font, anchor=W)
        self.info_desc = Label(self.info, text="name", fg="white", bg="black", font=self.desc_font, anchor=W)
        self.info_cats = Label(self.info, text="name", fg="yellow", bg="black", font=self.desc_font, anchor=W)
        self.enable_events()

    def read_data(self):
        self.file_ids = self.data.get_file_ids()
        if self.shuffle_seed:
            seed(self.shuffle_seed)
            shuffle(self.file_ids)
        else:
            print("shuffling is disabled")
        self.last_seen = self.file_ids[0]
        self.last_seen = self.data.get_last_seen()
    
    def enable_events(self) -> None:
        self.key_func_id = self.root.bind('<Key>', self.keyboard_event)
        if self.motion_enabled:
            self.motion_time = time.time() + 3
            self.motion_func_id = self.root.bind('<Motion>', self.motion_event)

    def disable_events(self) -> None:
        self.root.unbind('<Key>', self.key_func_id)
        self.root.unbind('<Motion>', self.motion_func_id)

    def get_file_id(self) -> int:
        if self.current_idx >= len(self.file_ids):
            self.current_idx = 0
        self.current_id = self.file_ids[self.current_idx]
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
            self.info_mark.grid(column=4, row=1, sticky=[W, E])
        else:
            self.info_mark.grid_forget()
    
    def display_info(self):
        self.info_name.grid_forget()
        self.info_desc.grid_forget()
        self.info_cats.grid_forget()
        info = self.current_info
        if info.photo_name:
            self.info_name["text"] = info.photo_name
            self.info_name.grid(column=1, row=2, sticky=[W, E])
        if info.description:
            self.info_desc["text"] = info.description
            self.info_desc.grid(column=2, columnspan=2, row=2, sticky=[W, E])
        if info.categories:
            self.info_cats["text"] = info.categories
            self.info_cats.grid(column=4, row=2, sticky=[W, E])


    def display(self) -> None:
        fname = self.current_info.file_name
        c_image = self.prepare_image(fname)
        self.display_mark()
        self.display_info()

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

    def save(self):
        from_file_name = self.current_info.file_name
        to_file_name = self.save_folder / Path(from_file_name).name
        shutil.copyfile(from_file_name, to_file_name)
            
    
    def keyboard_event(self, ev) -> None:
        if ev.keysym in ["Left", "Up"] or ev.char == 'p':
            self.previous()
        elif ev.keysym in ["Right", "Down"] or ev.char == 'n':
            self.next()
        elif ev.keycode == 27 or ev.char == 'q' or ev.keysym == "Escape":
            self.end_loop(ev)
        elif ev.char == 's':
            self.mark(ev.char)
            self.save()
        elif ev.char == 'd':
            self.mark(ev.char)
        elif ev.char == 'r':
            self.mark(' ')
        elif ev.char == ' ' or ev.keycode == 13:
            self.resume()
        elif ev.char == 'i':
            self.disable_events()
            try:
                info = self.current_info
                info.dialog(self.root)
                if not info.photo_name:
                    self.enable_events()
                    return
                self.data.save_photo_info(self.current_id, info)
            except Exception as exc:
                print(exc)
            self.enable_events()
        elif ev.char == "/":
            self.disable_events()
            if not self.search_params:
                self.search_params = Search()
            self.search_params.dialog(self.root)
            self.data.do_search(self.search_params)
            self.read_data()
            self.enable_events()
        else:
            print(f"keycode: {ev.keycode} char: '{ev.char}' keysym: {ev.keysym}")
            self.disable_events()
            help = Help()
            help.dialog(self.root, ev.keysym)
            self.enable_events()
            if help.key_event:
                self.root.after(100, self.keyboard_event(help.key_event))

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
            self.info_paused.grid(column=1, row=1, sticky=[W, E])

    def motion_event(self, ev) -> None:
        if time.time() > self.motion_time:
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
                current_info = self.data.get_file_info(current_id)
                if not current_info:
                    self.next()
                    continue

                if self.log_url and skip_count < self.max_skip_count:
                    try:
                        # o = json.dumps({"ts": ts, "file_no": current_id, "name": current_info.file_name})
                        # requests.post(self.log_url, headers={"Content-Type": "application/json"}, data=o)
                        print("reset skip count")
                        skip_count = 0
                    except Exception as e:
                        print(f"{skip_count} < {self.max_skip_count} - {e}")
                        skip_count += 1
                try:
                    self.current_info = current_info
                    self.display()
                except Exception as ex:
                    self.data.delete_file(current_id)
                    del self.file_ids[self.current_idx]
                    file_count -= 1
                    self.current_idx -= 1
                if self.reverse:
                    self.reverse = False
                else:
                    self.current_idx += 1
        self.end_loop()
