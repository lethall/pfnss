import sqlite3
from shutil import copy

with sqlite3.connect("pfnss.db") as db:
    marked = db.execute('''select name, mark from files, marks
    where mark <> '' and files.id = file_id order by mark''').fetchall()

for fn, mark in marked:
    if mark == "save":
        subdir = "Save"
    elif mark == "delete":
        subdir = "Delete"
    else:
        subdir = "Edit"
    print(f"{fn} is marked {mark}")
    copy(fn, f"c:/Users/phall/OneDrive/Desktop/Marked Pictures/{subdir}")
