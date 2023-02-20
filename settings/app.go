package main

import (
	"context"
	_ "image/jpeg"
	"io/ioutil"
	"strings"

	"github.com/wailsapp/wails/v2/pkg/runtime"
)

// App struct
type App struct {
	ctx context.Context
}

var fileName []string

// NewApp creates a new App application struct
func NewApp() *App {
	return &App{}
}

// startup is called when the app starts. The context is saved
// so we can call the runtime methods
func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
	fileNames, err := ioutil.ReadFile("files.txt")
	if err != nil {
		runtime.LogFatal(a.ctx, "Failed to read filenames")
		return
	}
	fileName = strings.Split(string(fileNames), "\n")
}

func (a *App) LoadImage(imageIndex int) string {
	imageIndex = imageIndex % len(fileName)
	return fileName[imageIndex]
}
