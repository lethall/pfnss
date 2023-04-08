package main

import (
	"context"
	_ "image/jpeg"
	"os"
	"regexp"
	"strings"
	"time"

	"github.com/wailsapp/wails/v2/pkg/runtime"
	_ "modernc.org/sqlite"
)

// App struct
type App struct {
	ctx           context.Context
	settings      Settings
	conditioner   regexp.Regexp
	files         []FileItem
	imageTicker   *time.Ticker
	viewDelay     time.Duration
	paused        bool
	absPrefix     string
	onlyConfigure bool
}

type FileItem struct {
	Id   int    `json:"id"`
	Name string `json:"name"`
	Ix   int    `json:"ix"`
	Mark string `json:"mark"`
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
	if err := a.readConfig(); err != nil {
		runtime.LogErrorf(a.ctx, "failed to read ini file %v\n", err)
	} else {
		if len(os.Args) > 1 && strings.ToLower(os.Args[1]) == "/c" {
			runtime.LogDebug(a.ctx, "requesting configure")
			a.onlyConfigure = true
		} else {
			a.configure()
		}
	}
}

func (a *App) conditionFileName(item FileItem) FileItem {
	newItem := FileItem{
		Id:   item.Id,
		Ix:   a.settings.CurrentIndex,
		Mark: actionFromKey(a.lastFileMark(item.Id)),
	}

	s := item.Name
	if a.conditioner.String() != "" {
		s = a.conditioner.ReplaceAllString(item.Name, a.settings.ReplaceWith)
	}
	requestedFilename := a.absPrefix + s
	if len(requestedFilename) > 1 && string(requestedFilename[1]) == ":" {
		requestedFilename = requestedFilename[2:]
	}
	newItem.Name = strings.ReplaceAll(requestedFilename, `\`, "/")

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
		runtime.EventsEmit(a.ctx, "announce", actionFromKey(key))
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
	case "m":
		a.moveMarkedFiles()
	default:
		runtime.LogDebugf(a.ctx, "Key: %v", key)
	}
}

func (a *App) moveMarkedFiles() {

}

func actionFromKey(key string) (action string) {
	if key == "" {
		return
	}
	switch key[0] {
	case 's':
		action = "Save"
	case 'd':
		action = "Delete"
	case 'e':
		action = "Edit"
	}
	return
}
