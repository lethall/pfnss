package main

import (
	"context"
	"fmt"
	_ "image/jpeg"
	"os"
	"path"
	"regexp"
	"strings"
	"time"

	"github.com/wailsapp/wails/v2/pkg/runtime"
	_ "modernc.org/sqlite"
)

const deleteFiles = string(os.PathSeparator) + "PFNSS_Delete"
const saveFiles = string(os.PathSeparator) + "PFNSS_Save"

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
	settingsFile  string
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
	workDir := path.Dir(os.Args[0])
	app.settings.DbFileName = path.Join(workDir, "pfnss.db")
	app.settings.PicDir = workDir
	app.settings.ShuffleSeed = 31056
	app.settings.SwitchSeconds = 10
	app.settingsFile = path.Join(workDir, "pfnss.local")
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

func (a *App) fixName(name string) string {
	if a.conditioner.String() != "" {
		name = a.conditioner.ReplaceAllString(name, a.settings.ReplaceWith)
	}
	requestedFilename := a.absPrefix + name
	if len(requestedFilename) > 1 && string(requestedFilename[1]) == ":" {
		requestedFilename = requestedFilename[2:]
	}
	return strings.ReplaceAll(requestedFilename, `\`, "/")
}

func (a *App) conditionFileName(item FileItem) FileItem {
	return FileItem{
		Name: a.fixName(item.Name),
		Id:   item.Id,
		Ix:   a.settings.CurrentIndex,
		Mark: actionFromKey(a.lastFileMark(item.Id)),
	}
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
	case "s", "d", "e", "r":
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
	markedFiles := a.findMarkedFiles()
	if len(markedFiles) > 0 {
		os.MkdirAll(a.settings.PicDir+deleteFiles, 0777)
		os.MkdirAll(a.settings.PicDir+saveFiles, 0777)
	}
	doRebuld := false
	for _, fi := range markedFiles {
		var destDir string
		switch fi.Mark[0] {
		case 'd', 'D':
			destDir = deleteFiles
		case 's', 'S':
			destDir = saveFiles
		default:
			runtime.LogErrorf(a.ctx, "%s is marked with %s", fi.Name, fi.Mark)
		}
		if destDir != "" {
			name := a.fixName(fi.Name)
			destName := fmt.Sprintf("%s%s%cid_%d.jpg", a.settings.PicDir, destDir, os.PathSeparator, fi.Id)
			runtime.LogInfof(a.ctx, "Moving %s to %s", name, destName)
			if err := os.Rename(name, destName); err != nil {
				runtime.LogErrorf(a.ctx, "could not move - %v", err)
			} else {
				doRebuld = true
			}
		}
	}
	if doRebuld {
		a.clearMarks()
		a.selectFiles()
	}
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
	case 'r':
		action = ""
	}
	return
}
