package main

import (
	"context"
	"database/sql"
	_ "image/jpeg"
	"log"
	"math/rand"
	"regexp"
	"time"

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
	Ix   int    `json:"ix"`
}

var files []FileItem
var absPrefix = ""
var conditioner regexp.Regexp
var replacement = ""
var shuffleSeed int64
var currentIndex int
var imageTicker *time.Ticker
var viewDelay time.Duration = 10 * time.Second
var paused bool
var dbFileName string

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

	db, err := sql.Open("sqlite", dbFileName)
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
		log.Fatalf("Failed to query files from %v", dbFileName)
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

	imageTicker = time.NewTicker(viewDelay)
	go func() {
		for {
			select {
			case <-imageTicker.C:
				currentIndex++
				runtime.EventsEmit(a.ctx, "loadimage", currentIndex)
			}
		}
	}()
}

func mark(indx int, action string) {
	fileId := files[indx].Id
	db, err := sql.Open("sqlite", dbFileName)
	if err != nil {
		log.Fatalf("Failed to read DB")
	}

	defer func() {
		err = db.Close()
		if err != nil {
			log.Fatalf("Could not close DB")
		}
	}()

	_, err = db.Exec("insert into marks (ts, file_id, mark) values (?,?,?)",
		time.Now().Format("2006-01-02T15:04:05.999"), fileId, action)
	if err != nil {
		log.Fatalf("Failed to insert mark %s for %d", action, fileId)
	}

}

func logView(indx int) {
	fileId := files[indx].Id
	db, err := sql.Open("sqlite", dbFileName)
	if err != nil {
		log.Fatalf("Failed to read DB")
	}

	defer func() {
		err = db.Close()
		if err != nil {
			log.Fatalf("Could not close DB")
		}
	}()

	_, err = db.Exec("insert into log (ts, file_id) values (?,?)",
		time.Now().Format("2006-01-02T15:04:05.999"), fileId)
	if err != nil {
		log.Fatalf("Failed to insert log for %d", fileId)
	}

}

func conditionFileName(ctx context.Context, item FileItem, ix int) FileItem {
	newItem := FileItem{
		Id: item.Id,
		Ix: ix,
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
	if imageIndex < 0 {
		imageIndex = len(files) - 1
	}
	if imageIndex >= len(files) {
		imageIndex = 0
	}
	currentIndex = imageIndex
	logView(currentIndex)
	return conditionFileName(a.ctx, files[imageIndex], currentIndex)
}

func (a *App) DoKey(key string) {
	runtime.LogDebugf(a.ctx, "key: %v\n", key)
	switch key {
	case "q", "Escape":
		runtime.Quit(a.ctx)
	case "f":
		if runtime.WindowIsFullscreen(a.ctx) {
			runtime.WindowUnfullscreen(a.ctx)
		} else {
			runtime.WindowFullscreen(a.ctx)
		}
	case "n", "ArrowRight", "ArrowDown":
		currentIndex++
		imageTicker.Reset(viewDelay)
		runtime.EventsEmit(a.ctx, "loadimage", currentIndex)
	case "p", "ArrowLeft", "ArrowUp":
		currentIndex--
		imageTicker.Reset(viewDelay)
		runtime.EventsEmit(a.ctx, "loadimage", currentIndex)
	case "s", "d", "e":
		mark(currentIndex, key)
		action := ""
		switch key {
		case "s":
			action = "Save"
		case "d":
			action = "Delete"
		case "e":
			action = "Edit"
		}
		runtime.EventsEmit(a.ctx, "announce", action)
	case " ", "Enter":
		paused = !paused
		if paused {
			imageTicker.Stop()
			runtime.EventsEmit(a.ctx, "announce", "Paused")
		} else {
			imageTicker.Reset(viewDelay)
			runtime.EventsEmit(a.ctx, "announce", "")
		}
	case "c":
		imageTicker.Stop()
		paused = true
		runtime.EventsEmit(a.ctx, "configure")
	default:
		runtime.LogDebugf(a.ctx, "Key: %v", key)
	}
}
