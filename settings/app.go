package main

import (
	"context"
	"database/sql"
	_ "image/jpeg"
	"log"
	"math/rand"
	"os"
	"regexp"
	"time"

	"github.com/wailsapp/wails/v2/pkg/runtime"
	_ "modernc.org/sqlite"
)

// App struct
type App struct {
	ctx         context.Context
	settings    Settings
	conditioner regexp.Regexp
	files       []FileItem
	imageTicker *time.Ticker
	viewDelay   time.Duration
	paused      bool
	absPrefix   string
}

type FileItem struct {
	Id   int    `json:"id"`
	Name string `json:"name"`
	Ix   int    `json:"ix"`
}

// NewApp creates a new App application struct
func NewApp() *App {
	app := &App{}
	workDir, _ := os.Getwd()
	app.settings.DbFileName = workDir + string(os.PathSeparator) + "pfnss.db"
	app.settings.PicDir = workDir
	app.settings.ShuffleSeed = 31056
	app.settings.SwitchSeconds = 10
	return app
}

// startup is called when the app starts. The context is saved
// so we can call the runtime methods
func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
	if err := readConfig(a); err != nil {
		log.Printf("failed to read ini file %v\n", err)
	} else {
		a.configure()
	}
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
		log.Printf("Failed to query files from %v - initializing", a.settings.DbFileName)
		db.Exec(`
		CREATE TABLE files (id integer primary key autoincrement, name);
		CREATE TABLE log(ts,file_id integer not null);
		CREATE TABLE marks(ts,file_id integer not null,mark);
		`)
		tx, err := db.Begin()
		if err != nil {
			log.Fatalf("starting rebuild %v", err)
		}
		a.rebuildData(db, a.settings.PicDir)
		err = tx.Commit()
		if err != nil {
			log.Fatalf("committing rebuild %v", err)
		}
	} else {
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
	lastShown := a.findLastShown(db)
	a.settings.CurrentIndex = 0
	for ix, item := range a.files {
		item.Ix = ix
		if item.Id == lastShown {
			a.settings.CurrentIndex = ix
		}
	}

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
				a.settings.CurrentIndex++
				runtime.EventsEmit(a.ctx, "loadimage", a.settings.CurrentIndex)
			}
		}
	}()
}

func (a *App) mark(action string) {
	fileId := a.files[a.settings.CurrentIndex].Id
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
	fileId := a.files[a.settings.CurrentIndex].Id
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
		Ix: a.settings.CurrentIndex,
	}

	s := item.Name
	if a.conditioner.String() != "" {
		s = a.conditioner.ReplaceAllString(item.Name, a.settings.ReplaceWith)
	}
	newItem.Name = a.absPrefix + s

	return newItem
}

func (a *App) LoadImage() FileItem {
	if len(a.files) == 0 {
		return FileItem{}
	}
	imageIndex := a.settings.CurrentIndex
	if imageIndex < 0 {
		imageIndex = len(a.files) - 1
	}
	if imageIndex >= len(a.files) {
		imageIndex = 0
	}
	a.settings.CurrentIndex = imageIndex
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
		a.settings.CurrentIndex++
		a.imageTicker.Reset(a.viewDelay)
		runtime.EventsEmit(a.ctx, "loadimage", a.settings.CurrentIndex)
	case "p", "ArrowLeft", "ArrowUp":
		a.settings.CurrentIndex--
		a.imageTicker.Reset(a.viewDelay)
		runtime.EventsEmit(a.ctx, "loadimage", a.settings.CurrentIndex)
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
		if a.imageTicker != nil {
			a.imageTicker.Reset(a.viewDelay)
		}
		runtime.EventsEmit(a.ctx, "announce", "")
	case "c":
		if a.imageTicker != nil {
			a.imageTicker.Stop()
		}
		a.paused = true
		runtime.EventsEmit(a.ctx, "configure")
	default:
		runtime.LogDebugf(a.ctx, "Key: %v", key)
	}
}
