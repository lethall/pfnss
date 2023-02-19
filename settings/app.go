package main

import (
	"context"
	"image"
	_ "image/jpeg"
	"io/ioutil"
	"os"
	"strings"

	"github.com/wailsapp/wails/v2/pkg/runtime"
)

// App struct
type App struct {
	ctx context.Context
}

type ImageInfo struct {
	FileName string `json:"fileName"`
	Width    int    `json:"w"`
	Height   int    `json:"h"`
	Favor    string `json:"favor"`
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

func (a *App) LoadImage(imageIndex int) (imageInfo ImageInfo) {
	imageIndex = imageIndex % len(fileName)
	imageInfo.FileName = fileName[imageIndex]
	runtime.LogDebug(a.ctx, imageInfo.FileName)
	file, err := os.Open(imageInfo.FileName)
	if err != nil {
		runtime.LogWarningf(a.ctx, "Failed to load image [%d] %s", imageIndex, imageInfo.FileName)
		return
	}
	defer file.Close()
	config, _, _ := image.DecodeConfig(file)
	imageInfo.Width = config.Width
	imageInfo.Height = config.Height
	screenW, screenH := runtime.WindowGetSize(a.ctx)
	imageRatio := float32(config.Width) / float32(config.Height)
	screenRatio := float32(screenW) / float32(screenH)
	if imageRatio > screenRatio {
		imageInfo.Favor = "width"
	} else {
		imageInfo.Favor = "height"
	}
	runtime.LogInfof(a.ctx, "screen: %dx%d %v image: %v favor: %s",
		screenW, screenH, screenRatio, imageRatio, imageInfo.Favor)
	return
}
