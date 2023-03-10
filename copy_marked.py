import sqlite3
from shutil import copy
import os
import sys
import re

if len(sys.argv) not in [3, 5]:
    print(f"Usage: {sys.argv[0]} <db> <dest dir> [<replace pattern> <replacement>]", file=sys.stderr)
    raise SystemExit()

db_name = sys.argv[1]
destdir = sys.argv[2]

repl_pattern = None
if len(sys.argv) == 5:
    repl_pattern = re.compile(sys.argv[3])
    replacement = sys.argv[4]

with sqlite3.connect(db_name) as db:
    marked = db.execute('''select name, mark from files, marks
    where mark <> '' and files.id = file_id order by mark''').fetchall()

for fn, mark in marked:
    if mark == "save":
        subdir = "Save"
    elif mark == "delete":
        subdir = "Delete"
    else:
        subdir = "Edit"
    if repl_pattern:
        fn = re.sub(repl_pattern, replacement, fn)
    print(f"{fn} is marked {mark}")
    dir = f"{destdir}/{subdir}"
    os.makedirs(dir, exist_ok=True)
    copy(fn, dir)
