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
		runtime.LogInfo(a.ctx, "Nothing in directory "+dirName)
		return
	}
	shortDirName := dirName[len(a.settings.PicDir):]
	if shortDirName != "" {
		shortDirName = shortDirName[1:]
	}
	runtime.LogInfof(a.ctx, "%d entries in %s", len(entries), dirName)
	for _, entry := range entries {
		fileName := entry.Name()
		runtime.LogInfo(a.ctx, "Entry: "+fileName)
		if entry.IsDir() {
			fileName = dirName + string(os.PathSeparator) + fileName
			runtime.LogInfo(a.ctx, "Searching "+fileName)
			a.rebuildData(db, fileName)
		} else {
			runtime.LogInfo(a.ctx, "Considering "+fileName)
			if strings.HasSuffix(strings.ToLower(fileName), ".jpg") {
				fileName = shortDirName + string(os.PathSeparator) + fileName
				runtime.LogInfo(a.ctx, "Inserting "+fileName)
				a.files = append(a.files, FileItem{len(a.files), fileName, 0})
				db.Exec("insert into files (name) values (?)", fileName)
			}
		}
	}
}

func (a *App) closeDb(db *sql.DB, where string) {
	runtime.LogDebugf(a.ctx, "closing db in %s", where)
	err := db.Close()
	if err != nil {
		runtime.LogFatalf(a.ctx, "Could not close DB")
	}
}

func (a *App) selectFiles() {
	db := a.openDb()
	defer a.closeDb(db, "select")

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

func (a *App) findLastShown() (fileId int) {
	db := a.openDb()
	defer a.closeDb(db, "lasst shown")

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
	defer a.closeDb(db, "mark")

	_, err := db.Exec("insert into marks (ts, file_id, mark) values (?,?,?)",
		time.Now().Format("2006-01-02T15:04:05.999"), fileId, action)
	if err != nil {
		runtime.LogFatalf(a.ctx, "Failed to insert mark %s for %d - %v", action, fileId, err)
	}

}

func (a *App) logView() {
	fileId := a.files[a.settings.CurrentIndex].Id
	db := a.openDb()
	defer a.closeDb(db, "log")

	_, err := db.Exec("insert into log (ts, file_id) values (?,?)",
		time.Now().Format("2006-01-02T15:04:05.999"), fileId)
	if err != nil {
		runtime.LogFatalf(a.ctx, "Failed to insert log for %d - %v", fileId, err)
	}

}
