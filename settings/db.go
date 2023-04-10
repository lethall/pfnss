package main

import (
	"database/sql"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/wailsapp/wails/v2/pkg/runtime"
)

func (a *App) openDb() *sql.DB {
	db, err := sql.Open("sqlite", a.settings.DbFileName)
	if err != nil {
		runtime.LogFatalf(a.ctx, "Failed to read DB")
	}
	return db
}

func (a *App) rebuildData(db *sql.DB, dirName string) {
	entries, err := os.ReadDir(dirName)
	if err != nil {
		return
	}
	shortDirName := dirName[len(a.settings.PicDir):]
	if shortDirName != "" {
		shortDirName = shortDirName[1:]
	}
	for _, entry := range entries {
		fileName := entry.Name()
		if fileName == saveFiles || fileName == deleteFiles {
			continue
		}
		if entry.IsDir() {
			fileName = dirName + string(os.PathSeparator) + fileName
			a.rebuildData(db, fileName)
		} else {
			if strings.HasSuffix(strings.ToLower(fileName), ".jpg") {
				fileName = shortDirName + string(os.PathSeparator) + fileName
				runtime.LogInfo(a.ctx, "Inserting "+fileName)
				a.files = append(a.files, FileItem{len(a.files), fileName, 0, ""})
				db.Exec("insert into files (name) values (?)", fileName)
			}
		}
	}
}

func (a *App) closeDb(db *sql.DB) {
	err := db.Close()
	if err != nil {
		runtime.LogFatalf(a.ctx, "Could not close DB")
	}
}

func (a *App) lastFileMark(fileId int) (mark string) {
	db := a.openDb()
	defer a.closeDb(db)

	rows, err := db.Query("select mark from marks where file_id = ? order by ts desc limit 1;", fileId)
	if err != nil {
		runtime.LogInfof(a.ctx, "Failed query marks from %v", a.settings.DbFileName)
		return
	}

	for rows.Next() {
		if err = rows.Scan(&mark); err != nil {
			runtime.LogFatalf(a.ctx, "failed to scan mark for %d - %v", fileId, err)
		}
	}

	return
}

func (a *App) findMarkedFiles() (markedFiles []FileItem) {
	db := a.openDb()
	defer a.closeDb(db)

	rows, err := db.Query("select m.file_id, m.mark, f.name from marks m join files f on (f.id = m.file_id) order by m.ts desc;")
	if err != nil {
		runtime.LogInfof(a.ctx, "Failed query marks from %v", a.settings.DbFileName)
		return
	}

	for rows.Next() {
		fi := FileItem{}
		if err = rows.Scan(&fi.Id, &fi.Mark, &fi.Name); err != nil {
			runtime.LogFatalf(a.ctx, "failed to scan marked file - %v", err)
		}
		markedFiles = append(markedFiles, fi)
	}

	return
}

func (a *App) clearMarks() {
	db := a.openDb()
	defer a.closeDb(db)

	db.Exec("delete from files where id in (select distinct file_id from marks);")
	db.Exec("delete from marks;")
	runtime.LogInfo(a.ctx, "Cleared marks")
}

func (a *App) selectFiles() {
	db := a.openDb()
	defer a.closeDb(db)

	a.files = []FileItem{}
	rows, err := db.Query("select id, name from files order by id;")
	if err != nil {
		runtime.LogInfof(a.ctx, "Failed to query files from %v - initializing", a.settings.DbFileName)
		db.Exec(`
		CREATE TABLE files (id integer primary key autoincrement, name);
		CREATE TABLE log(ts,file_id integer not null);
		CREATE TABLE marks(ts,file_id integer not null,mark);
		`)
		tx, err := db.Begin()
		if err != nil {
			runtime.LogFatalf(a.ctx, "starting rebuild %v", err)
		}
		a.rebuildData(db, a.settings.PicDir)
		err = tx.Commit()
		if err != nil {
			runtime.LogFatalf(a.ctx, "committing rebuild %v", err)
		}
		return
	}

	if a.settings.FindType == "byId" {
		rows.Close()
		startId, endId := a.getFindRange()
		rows, err = db.Query("select id, name from files where id >= ? and id <= ? order by id;", startId, endId)
		if err != nil {
			runtime.LogFatalf(a.ctx, "failed to query byId = %v", err)
		}
	} else if a.settings.FindType == "byShown" {
		rows.Close()
		startTs, endTs := a.getFindTsRange()
		rows, err = db.Query(`select distinct f.id, f.name
		from files f join log g on f.id = g.file_id
		where g.ts >= ? and g.ts <= ?
		order by g.ts;`, startTs, endTs)
		if err != nil {
			runtime.LogFatalf(a.ctx, "failed to query byShown = %v", err)
		}
	}

	for rows.Next() {
		fi := FileItem{}
		if err = rows.Scan(&fi.Id, &fi.Name); err != nil {
			runtime.LogFatalf(a.ctx, "failed to scan fileName %v", err)
		}

		a.files = append(a.files, fi)
	}

	if err = rows.Err(); err != nil {
		runtime.LogFatalf(a.ctx, "could not use result set")
	}
}

func (a *App) getFindRange() (int, int) {
	startId, err := strconv.Atoi(a.settings.FindFrom)
	if err != nil {
		startId = 1
		a.settings.FindFrom = strconv.Itoa(startId)
	}
	endId, err := strconv.Atoi(a.settings.FindTo)
	if err != nil {
		endId = 1
		a.settings.FindTo = strconv.Itoa(endId)
	}
	if startId > endId {
		startId, endId = endId, startId
		a.settings.FindFrom, a.settings.FindTo = a.settings.FindTo, a.settings.FindFrom
	}
	return startId, endId
}

func (a *App) getFindTsRange() (string, string) {
	startTs := a.settings.FindFrom
	endTs := a.settings.FindTo
	if startTs > endTs {
		startTs, endTs = endTs, startTs
		a.settings.FindFrom, a.settings.FindTo = a.settings.FindTo, a.settings.FindFrom
	}
	return startTs + ":00.000", endTs + ":59.999"
}

func (a *App) findLastShown() (fileId int) {
	db := a.openDb()
	defer a.closeDb(db)

	rows, err := db.Query("select file_id from log order by ts desc limit 1")
	if err != nil {
		runtime.LogDebugf(a.ctx, "failed to find last %v", err)
		return 0
	}
	for rows.Next() {
		rows.Scan(&fileId)
	}
	runtime.LogDebugf(a.ctx, "last seen: %v", fileId)
	return
}

func (a *App) mark(action string) {
	fileId := a.files[a.settings.CurrentIndex].Id
	db := a.openDb()
	defer a.closeDb(db)

	_, err := db.Exec("insert into marks (ts, file_id, mark) values (?,?,?)",
		time.Now().Format("2006-01-02T15:04:05.999"), fileId, action)
	if err != nil {
		runtime.LogFatalf(a.ctx, "Failed to insert mark %s for %d - %v", action, fileId, err)
	}

}

func (a *App) logView() {
	fileId := a.files[a.settings.CurrentIndex].Id
	db := a.openDb()
	defer a.closeDb(db)

	_, err := db.Exec("insert into log (ts, file_id) values (?,?)",
		time.Now().Format("2006-01-02T15:04:05.999"), fileId)
	if err != nil {
		runtime.LogFatalf(a.ctx, "Failed to insert log for %d - %v", fileId, err)
	}

}
