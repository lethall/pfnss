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
            last_ts, last_seen = db.execute(
                """select ts, file_id from log
                where ts = (select max(ts) from log)
                """).fetchone()
            print(f"{last_seen} was seen at {last_ts}")
        return last_seen
    
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
            fname = db.execute("select name from files where id = ?", (id,)).fetchone()[0]
            if (".jpg" not in fname) and (".jpeg" not in fname):
                return None
            ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            db.execute("insert into log (ts, file_id) values (?,?)", (ts, id))
            db.commit()        
        return fname
