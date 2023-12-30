from sqlite3 import connect
from datetime import datetime, UTC

class Data:
    db_file_name = None
    def __init__(self, db_file_name) -> None:
        self.db_file_name = db_file_name

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

    def get_file_name(self, id):
        fname = None
        with connect(self.db_file_name) as db:
            try:
                fname = db.execute("select name from files where id = ?", (id,)).fetchone()[0]
            except:
                return None
            if (".jpg" not in fname) and (".jpeg" not in fname):
                return None
            ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            db.execute("insert into log (ts, file_id) values (?,?)", (ts, id))
            db.commit()        
        return fname

    def save_photo_info(self, id, name, description, categories):
        print(f"Got name '{name}' desc '{description}' [{", ".join(categories)}] for {id}")
