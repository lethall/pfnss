from sqlite3 import connect
from datetime import datetime, UTC
from pathlib import Path
import re

from .photo_info import PhotoInfo
from .search import Search


class Data:
    db_file_name = None
    searching = False
    last_reg : re.Pattern = None

    def __init__(self, db_file_name) -> None:
        self.db_file_name = db_file_name
        with connect(self.db_file_name) as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS files (id integer primary key autoincrement, name);
                CREATE TABLE IF NOT EXISTS found (id integer primary key);
                CREATE TABLE IF NOT EXISTS log(ts,file_id integer not null);
                CREATE TABLE IF NOT EXISTS marks(ts,file_id integer not null,mark);
                CREATE TABLE IF NOT EXISTS info(file_id integer primary key, name text, description text, categories text);
                """)
            db.commit()

    def get_file_count(self) -> int:
        count = 0
        with connect(self.db_file_name) as db:
            table_name = "found" if self.searching else "files"
            count = int(db.execute(f"select count(*) from {table_name}").fetchone()[0])
        return count
    
    def get_file_ids(self) -> list:
        ids = []
        with connect(self.db_file_name) as db:
            table_name = "found" if self.searching else "files"
            c = db.execute(f"select id from {table_name}")
            while True:
                r = c.fetchone()
                if not r:
                    break
                ids.append(int(r[0]))
        return ids
    
    def get_last_seen(self) -> int:
        last_seen = 0
        with connect(self.db_file_name) as db:
            result = db.execute(
                """select ts, file_id from log
                where ts = (select max(ts) from log)
                """).fetchone()
            if result:
                last_ts, last_seen = result
                print(f"{last_seen} was seen at {last_ts}")
            else:
                print("no log")
        return last_seen
    
    def get_last_mark(self, id) -> int:
        last_mark = ""
        with connect(self.db_file_name) as db:
            result = db.execute(
                """select mark, ts from marks
                where file_id = ? order by ts desc limit 1
                """, (id,)).fetchone()
            if result:
                last_mark, last_ts = result
                # print(f"{last_mark} was marked on {id} at {last_ts}")
            # else:
            #     print(f"no mark")
        return last_mark
    
    def save(self, current_id, mark) -> None:
        with connect(self.db_file_name) as db:
            ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            db.execute(
                """insert into marks (ts, file_id, mark) values (?,?,?)""",
                (ts, current_id, mark))
            db.commit()

    def get_file_info(self, id) -> PhotoInfo:
        with connect(self.db_file_name) as db:
            result = db.execute(
                    """select a.name, b.name, b.description, b.categories
                    from files a left outer join info b on (a.id = b.file_id)
                    where a.id = ?""", (id,)).fetchone()
            if not result:
                return None
            info = PhotoInfo(result)
            if not info.file_name.endswith(".jpg") and not info.file_name.endswith(".jpeg"):
                return None
            ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            db.execute("insert into log (ts, file_id) values (?,?)", (ts, id))
            db.commit()        
        return info

    def save_photo_info(self, id, info : PhotoInfo) -> None:
        name, description, cats = info.photo_name, info.description, info.categories
        with connect(self.db_file_name) as db:
            db.execute(
                """insert into info (file_id, name, description, categories) values (?,?,?,?)
                on conflict do update set name=?, description=?, categories=? where file_id=?
                """, (id, name, description, cats, name, description, cats, id))
            db.commit()
    
    def delete_file(self, id):
        with connect(self.db_file_name) as db:
            print(f"deleting file {id}")
            db.execute("delete from files where id = ?", (id,))
            db.commit()


    def load_files(self, picture_dir) -> None:
        p = Path(picture_dir)
        print(f"Loading files from {p.name}")
        with connect(self.db_file_name) as db:
            for f in p.glob(pattern="**/*.jpg", case_sensitive=False):
                if not f.is_file:
                    continue
                db.execute("insert into files (name) values (?)", (str(f),))
            db.commit()

    def do_search(self, search_params: Search) -> None:
        count = 0
        where = search_params.compile()
        if not where:
            where = ""
        with connect(self.db_file_name) as db:
            if "REGEXP" in where.upper():
                def regexp(expr, item):
                    last_reg = Data.last_reg
                    if not last_reg or last_reg.pattern != expr:
                        print(f"Data pattern set to {expr}")
                        Data.last_reg = last_reg = re.compile(expr)
                    return last_reg.search(item) is not None
                db.create_function("REGEXP", 2, regexp)
            count = int(db.execute(f"select count(*) from files {where}").fetchone()[0])
            if not count:
                self.searching = False
                return
            self.searching = True
            print(f"found {count} items, reloading")
            db.execute("delete from found")
            db.execute(f"insert into found (id) select id from files {where}")
            db.commit()
