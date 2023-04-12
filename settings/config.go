package main

import (
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"math/rand"
	"os"
	"regexp"
	"time"

	"github.com/wailsapp/wails/v2/pkg/runtime"
)

type Settings struct {
	ShuffleSeed    int64  `json:"shuffleSeed"`
	DbFileName     string `json:"dbFileName"`
	PicDir         string `json:"picDir"`
	ReplacePattern string `json:"replacePattern"`
	ReplaceWith    string `json:"replaceWith"`
	FindType       string `json:"findType"`
	FindFrom       string `json:"findFrom"`
	FindTo         string `json:"findTo"`
	SwitchSeconds  int    `json:"switchSeconds"`
	ShowId         bool   `json:"showId"`
	ShowSeq        bool   `json:"showSeq"`
	ShowName       bool   `json:"showName"`
	CurrentIndex   int    `json:"currentIndex"`
}

func (a *App) configure() {
	a.selectFiles()

	if a.settings.ReplacePattern == "" {
		a.absPrefix = a.settings.PicDir + "/"
	} else {
		a.absPrefix = ""
		a.conditioner = *regexp.MustCompile(a.settings.ReplacePattern)
	}

	runtime.LogInfof(a.ctx, "Shuffle seed: %d", a.settings.ShuffleSeed)
	if a.settings.ShuffleSeed > 0 {
		rand.Seed(a.settings.ShuffleSeed)
		rand.Shuffle(len(a.files), func(i int, j int) {
			a.files[i], a.files[j] = a.files[j], a.files[i]
		})
	}

	if a.settings.FindType == "bySequence" {
		seqStart, seqEnd := a.getFindRange()
		a.files = a.files[seqStart : seqEnd+1]
	}

	lastShown := a.findLastShown()
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

func (a *App) readConfig() (err error) {
	iniFile, e := os.Open(a.settingsFile)
	if e != nil {
		return fmt.Errorf("failed to read the alternate ini file - %q", e)
	}
	// log.Printf("Using alternate ini file %v\n", alternateIniFileName)
	iniData, e := io.ReadAll(iniFile)
	if e == nil {
		e = json.Unmarshal(iniData, &a.settings)
		if e != nil || a.settings.DbFileName == "" {
			return fmt.Errorf("failed to load settings - %q", e)
		}
	}
	runtime.LogInfo(a.ctx, "Using saved settings")
	return nil
}

func (a *App) GetProjectFile() (fileName string) {
	cwd, err := os.Getwd()
	if err != nil {
		runtime.LogError(a.ctx, "Couldn't get current directory")
	}
	fileName, err = runtime.SaveFileDialog(a.ctx, runtime.SaveDialogOptions{
		Title:            "Project File",
		DefaultDirectory: cwd,
		DefaultFilename:  "pfnss.db",
		Filters: []runtime.FileFilter{
			{
				DisplayName: "Project File",
				Pattern:     "*.db",
			},
		},
	})
	if err != nil {
		runtime.LogError(a.ctx, "Couldn't pick a file")
	}
	runtime.LogInfof(a.ctx, "Picked '%s'", fileName)
	return
}

func (a *App) GetPicDir() (picDir string) {
	picDir, err := runtime.OpenDirectoryDialog(a.ctx, runtime.OpenDialogOptions{
		Title:            "Picture Directory",
		DefaultDirectory: os.Getenv("HOME"),
	})
	if err != nil {
		runtime.LogError(a.ctx, "Couldn't pick a directory")
	}
	runtime.LogInfof(a.ctx, "Picked '%s'", picDir)
	return
}

func (a *App) SaveSettings(settings Settings) {
	runtime.LogInfof(a.ctx, "Update settings: %v", settings)
	a.settings = settings
	newSettings, _ := json.Marshal(a.settings)
	ioutil.WriteFile(a.settingsFile, newSettings, 0644)
	if a.onlyConfigure {
		runtime.Quit(a.ctx)
	}
	a.configure()
}

func (a *App) GetSettings() (settings Settings) {
	return a.settings
}
