package main

import (
	"database/sql"
	"os"
	"strings"

	"github.com/wailsapp/wails/v2/pkg/runtime"
)

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
