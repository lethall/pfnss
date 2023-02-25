package main

import (
	"context"
	"database/sql"
	_ "image/jpeg"

	"github.com/wailsapp/wails/v2/pkg/runtime"
	_ "modernc.org/sqlite"
)

// App struct
type App struct {
	ctx context.Context
}

type FileItem struct {
	Id   int    `json:"id"`
	Name string `json:"name"`
}

var files []FileItem
var absPrefix string = "/Users/leehall/"

// NewApp creates a new App application struct
func NewApp() *App {
	return &App{}
}

// startup is called when the app starts. The context is saved
// so we can call the runtime methods
func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
	db, err := sql.Open("sqlite", "pfnss.db")
	if err != nil {
		runtime.LogFatal(a.ctx, "Failed to read DB")
		return
	}

	rows, err := db.Query("select id, name from files;")
	if err != nil {
		runtime.LogFatal(a.ctx, "Failed to query files")
		return
	}

	for rows.Next() {
		fi := FileItem{}
		if err = rows.Scan(&fi.Id, &fi.Name); err != nil {
			runtime.LogFatalf(a.ctx, "Failed to scan fileName %v", err)
			return
		}

		files = append(files, fi)
	}

	if err = rows.Err(); err != nil {
		runtime.LogFatal(a.ctx, "Could not use result set")
		return
	}

	if err = db.Close(); err != nil {
		runtime.LogFatal(a.ctx, "Could not close DB")
		return
	}
}

func (a *App) LoadImage(imageIndex int) FileItem {
	item := files[imageIndex%len(files)]
	item.Name = absPrefix + item.Name
	return item
}

func (a *App) DoKey(key string) {
	runtime.LogDebugf(a.ctx, "key: %v\n", key)
	if key == "q" {
		runtime.Quit(a.ctx)
	}
}
