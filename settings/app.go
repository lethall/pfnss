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
	ctx          context.Context
	settings     Settings
	conditioner  regexp.Regexp
	files        []FileItem
	currentIndex int
	imageTicker  *time.Ticker
	viewDelay    time.Duration
	paused       bool
	absPrefix    string
}

type FileItem struct {
	Id   int    `json:"id"`
	Name string `json:"name"`
	Ix   int    `json:"ix"`
}

// NewApp creates a new App application struct
func NewApp() *App {
	return &App{}
}

// startup is called when the app starts. The context is saved
// so we can call the runtime methods
func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
	if err := readConfig(a); err != nil {
		log.Fatalf("failed to read ini file %v\n", err)
	}
	a.configure()
}

func (a *App) configure() {
	db, err := sql.Open("sqlite", a.settings.DbFileName)
	if err != nil {
		log.Fatalf("Failed to read DB")
	}

	defer func() {
		err = db.Close()
		if err != nil {
			log.Fatalf("Could not close DB")
		}
	}()

	a.files = []FileItem{}
	rows, err := db.Query("select id, name from files order by id;")
	if err != nil {
		log.Fatalf("Failed to query files from %v", a.settings.DbFileName)
	}

	for rows.Next() {
		fi := FileItem{}
		if err = rows.Scan(&fi.Id, &fi.Name); err != nil {
			log.Fatalf("Failed to scan fileName %v", err)
		}

		a.files = append(a.files, fi)
	}

	if err = rows.Err(); err != nil {
		log.Fatalf("Could not use result set")
	}

	if a.settings.ReplacePattern == "" {
		a.absPrefix = a.settings.PicDir + "/"
	} else {
		a.absPrefix = ""
		a.conditioner = *regexp.MustCompile(a.settings.ReplacePattern)
	}

	rand.Seed(a.settings.ShuffleSeed)
	runtime.LogInfof(a.ctx, "Shuffle seed: %d", a.settings.ShuffleSeed)
	rand.Shuffle(len(a.files), func(i int, j int) {
		a.files[i], a.files[j] = a.files[j], a.files[i]
	})
	a.currentIndex = 0

	if a.imageTicker != nil {
		a.imageTicker.Stop()
	}

	a.viewDelay = time.Duration(a.settings.SwitchSeconds) * time.Second
	a.paused = false
	a.imageTicker = time.NewTicker(a.viewDelay)
	go func() {
		for {
			select {
			case <-a.imageTicker.C:
				a.currentIndex++
				runtime.EventsEmit(a.ctx, "loadimage", a.currentIndex)
			}
		}
	}()
}

func (a *App) mark(action string) {
	fileId := a.files[a.currentIndex].Id
	db, err := sql.Open("sqlite", a.settings.DbFileName)
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

func (a *App) logView() {
	fileId := a.files[a.currentIndex].Id
	db, err := sql.Open("sqlite", a.settings.DbFileName)
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

func (a *App) conditionFileName(item FileItem) FileItem {
	newItem := FileItem{
		Id: item.Id,
		Ix: a.currentIndex,
	}

	s := item.Name
	if a.conditioner.String() != "" {
		s = a.conditioner.ReplaceAllString(item.Name, a.settings.ReplaceWith)
	}
	newItem.Name = a.absPrefix + s

	return newItem
}

func (a *App) LoadImage(imageIndex int) FileItem {
	if len(a.files) == 0 {
		return FileItem{}
	}
	if imageIndex < 0 {
		imageIndex = len(a.files) - 1
	}
	if imageIndex >= len(a.files) {
		imageIndex = 0
	}
	a.currentIndex = imageIndex
	a.logView()
	return a.conditionFileName(a.files[imageIndex])
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
		a.currentIndex++
		a.imageTicker.Reset(a.viewDelay)
		runtime.EventsEmit(a.ctx, "loadimage", a.currentIndex)
	case "p", "ArrowLeft", "ArrowUp":
		a.currentIndex--
		a.imageTicker.Reset(a.viewDelay)
		runtime.EventsEmit(a.ctx, "loadimage", a.currentIndex)
	case "s", "d", "e":
		a.mark(key)
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
		a.paused = !a.paused
		if a.paused {
			a.imageTicker.Stop()
			runtime.EventsEmit(a.ctx, "announce", "Paused")
		} else {
			a.imageTicker.Reset(a.viewDelay)
			runtime.EventsEmit(a.ctx, "announce", "")
		}
	case "!":
		a.paused = false
		a.imageTicker.Reset(a.viewDelay)
		runtime.EventsEmit(a.ctx, "announce", "")
	case "c":
		a.imageTicker.Stop()
		a.paused = true
		runtime.EventsEmit(a.ctx, "configure")
	default:
		runtime.LogDebugf(a.ctx, "Key: %v", key)
	}
}
