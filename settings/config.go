package main

import (
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"os"
	"regexp"

	"github.com/graniticio/inifile"
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
}

// Names of the config keys
const ALTERNATE_INIFILENAME_KEY = "iniFileName"
const ABSOLUTE_PATH_PREFIX_KEY = "absolutePathPrefix"
const CONDITIONER_REGEXP_KEY = "conditionerRegexp"
const CONDITIONER_REPLACEMENT_KEY = "conditionerReplacement"
const SHUFFLE_SEED_KEY = "shuffleSeed"
const SWITCH_SEC_KEY = "switchSeconds"
const DB_FILE_NAME_KEY = "dbFileName"

func readConfig(a *App) (err error) {
	iniFile, e := os.Open("pfnss.ini")
	if e != nil {
		return fmt.Errorf(fmt.Sprintf("could not open the ini file - %q", e))
	}

	ini, e := inifile.NewIniConfigFromFile(iniFile)
	if e != nil {
		return fmt.Errorf("failed to read the ini file - %q", e)
	}

	main, e := ini.Section("")
	if e != nil {
		return fmt.Errorf("failed to read the main section - %q", e)
	}

	alternateIniFileName, e := main.Value(ALTERNATE_INIFILENAME_KEY)
	if e == nil {
		iniFile, e = os.Open(alternateIniFileName)
		if e != nil {
			return fmt.Errorf("failed to read the alternate ini file - %q", e)
		}
		log.Printf("Using alternate ini file %v\n", alternateIniFileName)
		iniData, e := io.ReadAll(iniFile)
		if e == nil {
			e = json.Unmarshal(iniData, &a.settings)
			if e != nil || a.settings.DbFileName == "" {
				log.Println("Not a saved settings file, reading as a .ini")
				iniFile, _ = os.Open(alternateIniFileName)
			} else {
				log.Println("Using saved settings")
				return nil
			}
		}
		ini, e = inifile.NewIniConfigFromFile(iniFile)
		if e != nil {
			return fmt.Errorf("failed to intrepret the alternate ini - %q", e)
		}
	}

	saver, e := ini.Section("saver")
	if e != nil {
		return fmt.Errorf("failed to read the saver section - %q", e)
	}

	a.absPrefix, _ = saver.Value(ABSOLUTE_PATH_PREFIX_KEY)
	a.settings.ReplacePattern = ""
	a.settings.ReplacePattern, _ = saver.Value(CONDITIONER_REGEXP_KEY)
	c, e := regexp.Compile(a.settings.ReplacePattern)
	if e == nil {
		a.conditioner = *c
	}

	a.settings.ReplaceWith, _ = saver.Value(CONDITIONER_REPLACEMENT_KEY)

	a.settings.ShuffleSeed, e = saver.ValueAsInt64(SHUFFLE_SEED_KEY)
	if e != nil {
		a.settings.ShuffleSeed = 1234
	}

	n, e := saver.ValueAsInt64(SWITCH_SEC_KEY)
	if e != nil {
		a.settings.SwitchSeconds = 20
	}
	a.settings.SwitchSeconds = int(n)

	data, e := ini.Section("data")
	if e != nil {
		return fmt.Errorf("failed to read the data section - %q", e)
	}
	a.settings.DbFileName, e = data.Value(DB_FILE_NAME_KEY)
	if e != nil {
		return fmt.Errorf("failed to read dbFileName - %q", e)
	}

	a.settings.FindType = "byAll"

	a.settings.ShowId = true
	a.settings.ShowSeq = true
	a.settings.ShowName = true

	return nil
}

/*
; alternate configuration... if this is not provided, use this one
iniFileName = ../pfnss.ini

[data]
dbFileName = ../pfnss.db

[saver]
absolutePathPrefix = /
; conditionerRegexp = ""
; conditionerReplacement = ""
switchSeconds = 2
*/
// func writeConfig() {
// }

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
	ioutil.WriteFile("pfnss.local", newSettings, 0644)
	a.configure()
}

func (a *App) GetSettings() (settings Settings) {
	return a.settings
}
