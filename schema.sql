CREATE TABLE files (id integer primary key autoincrement, name);
CREATE TABLE log(ts,file_id integer not null);
CREATE TABLE marks(ts,file_id integer not null,mark);