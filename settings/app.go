package main

import (
	"context"
	"database/sql"
	_ "image/jpeg"
	"log"
	"math/rand"
	"regexp"

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
var absPrefix string
var conditioner regexp.Regexp
var replacement string = ""
var shuffleSeed int64

// NewApp creates a new App application struct
func NewApp() *App {
	return &App{}
}

// startup is called when the app starts. The context is saved
// so we can call the runtime methods
func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
	if err := readConfig(); err != nil {
		log.Fatalf("failed to read ini file %v\n", err)
	}

	db, err := sql.Open("sqlite", "pfnss.db")
	if err != nil {
		log.Fatalf("Failed to read DB")
	}

	defer func() {
		err = db.Close()
		if err != nil {
			log.Fatalf("Could not close DB")
		}
	}()

	rows, err := db.Query("select id, name from files;")
	if err != nil {
		log.Fatalf("Failed to query files")
	}

	for rows.Next() {
		fi := FileItem{}
		if err = rows.Scan(&fi.Id, &fi.Name); err != nil {
			log.Fatalf("Failed to scan fileName %v", err)
		}

		files = append(files, fi)
	}

	if err = rows.Err(); err != nil {
		log.Fatalf("Could not use result set")
	}
	rand.Seed(shuffleSeed)
	log.Println("shuffle seed: ", shuffleSeed)
	rand.Shuffle(len(files), func(i int, j int) {
		files[i], files[j] = files[j], files[i]
	})
}

func conditionFileName(ctx context.Context, item FileItem) FileItem {
	newItem := FileItem{
		Id: item.Id,
	}

	s := item.Name
	if conditioner.String() != "" {
		s = conditioner.ReplaceAllString(item.Name, replacement)
	}
	runtime.LogDebugf(ctx, "AbsPrefix: %s FileName: %s", absPrefix, s)
	newItem.Name = absPrefix + s
	return newItem
}

func (a *App) LoadImage(imageIndex int) FileItem {
	if len(files) == 0 {
		return FileItem{}
	}
	return conditionFileName(a.ctx, files[imageIndex])
}

func (a *App) DoKey(key string) {
	runtime.LogDebugf(a.ctx, "key: %v\n", key)
	if key == "q" {
		runtime.Quit(a.ctx)
	}
}
