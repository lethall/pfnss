package main

import (
	"fmt"
	"github.com/graniticio/inifile"
	"log"
	"os"
	"os/exec"
	"strings"
)

const logFileNameKey = "LOG_FILE_NAME"
const scriptFileNameKey = "SCRIPT_FILE_NAME"

func main() {
	ini, e := inifile.NewIniConfigFromPath("pfnss.ini")
	if e != nil {
		fmt.Fprintln(os.Stderr, fmt.Errorf("failed to read the ini file - %q", e))
		os.Exit(1)
	}

	w, e := ini.Section("wrapper")
	if e != nil {
		fmt.Fprintln(os.Stderr, fmt.Errorf("failed to read the wrapper section - %q", e))
		os.Exit(2)
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
	pythonCmd := append([]string{scriptFileName}, args[1:]...)
	logger.Println(strings.Join(pythonCmd, " "))
	cmd := exec.Command("python", pythonCmd...)
	cmd.Stderr = logFile
	cmd.Stdout = logFile
	err = cmd.Run()
	if err != nil {
		logger.Fatal(err)
	}
}
