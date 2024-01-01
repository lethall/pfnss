from sqlite3 import connect
from datetime import datetime, UTC
from pathlib import Path

from .photo_info import PhotoInfo

class Data:
    db_file_name = None
    def __init__(self, db_file_name) -> None:
        self.db_file_name = db_file_name
        with connect(self.db_file_name) as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS files (id integer primary key autoincrement, name);
                CREATE TABLE IF NOT EXISTS log(ts,file_id integer not null);
                CREATE TABLE IF NOT EXISTS marks(ts,file_id integer not null,mark);
                CREATE TABLE IF NOT EXISTS info(file_id integer primary key, name text, description text, categories text);
                """)
            db.commit()

    def get_file_count(self) -> int:
        count = 0
        with connect(self.db_file_name) as db:
            count = int(db.execute("select count(*) from files").fetchone()[0])
        return count
    
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

    def load_files(self, picture_dir):
        p = Path(picture_dir)
        print(f"Loading files from {p.name}")
        with connect(self.db_file_name) as db:
            for f in p.glob(pattern="**/*.jpg", case_sensitive=False):
                if not f.is_file:
                    continue
                db.execute("insert into files (name) values (?)", (str(f),))
            db.commit()
