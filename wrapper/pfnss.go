package main

import (
	"fmt"
	"github.com/graniticio/inifile"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

const logFileNameKey = "logFileName"
const scriptFileNameKey = "scriptFileName"
const alternateIniFileNameKey = "iniFileName"

func main() {
	iniFileName, e := os.Open("pfnss.ini")
	if e != nil {
		fmt.Fprintln(os.Stderr, fmt.Errorf("could not the ini file - %q", e))
		os.Exit(1)
	}

	ini, e := inifile.NewIniConfigFromFile(iniFileName)
	if e != nil {
		fmt.Fprintln(os.Stderr, fmt.Errorf("failed to read the ini file - %q", e))
		os.Exit(2)
	}

	w, e := ini.Section("wrapper")
	if e != nil {
		fmt.Fprintln(os.Stderr, fmt.Errorf("failed to read the wrapper section - %q", e))
		os.Exit(3)
	}

	var logFileName string
	logFileName, e = w.Value(logFileNameKey)
	if e != nil {
		logFileName = "c:/work/git/pfnss/pfnss_wrapper.log"
		fmt.Fprintln(os.Stderr, fmt.Errorf("failed to get the %s using default %s - %q", logFileNameKey, logFileName, e))
	}

	var scriptFileName string
	scriptFileName, e = w.Value(scriptFileNameKey)
	if e != nil {
		scriptFileName = "c:/work/git/pfnss/pfnss.py"
		fmt.Fprintln(os.Stderr, fmt.Errorf("failed to get the %s using default %s - %q", scriptFileNameKey, scriptFileName, e))
	}

	var alternateIniFileName string
	alternateIniFileName, e = w.Value(alternateIniFileNameKey)
	if e != nil {
		alternateIniFileName, _ = filepath.Abs(iniFileName.Name())
		fmt.Fprintln(os.Stderr, fmt.Errorf("failed to get the %s using default %s - %q", alternateIniFileNameKey, alternateIniFileName, e))
	}

	args := os.Args
	logger := log.Default()
	logFile, err := os.OpenFile(logFileName, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0666)
	if err != nil {
		logger.Fatal(err)
	}
	defer func() {
		logFile.Close()
	}()
	logger.SetOutput(logFile)
	pythonCmd := append([]string{scriptFileName, alternateIniFileName}, args[1:]...)
	logger.Println(strings.Join(pythonCmd, " "))
	cmd := exec.Command("python", pythonCmd...)
	cmd.Stderr = logFile
	cmd.Stdout = logFile
	err = cmd.Run()
	if err != nil {
		logger.Fatal(err)
	}
}
