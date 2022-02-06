package main

import (
	"log"
	"os"
	"os/exec"
	"strings"
)

func main() {
	args := os.Args
	logger := log.Default()
	logFile, err := os.OpenFile("c:/work/git/pfnss/pfnss_wrapper.log", os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0666)
	if err != nil {
		logger.Fatal(err)
	}
	defer func() {
		logFile.Close()
	}()
	logger.SetOutput(logFile)
	pythonCmd := append([]string{"c:/work/git/pfnss/pfnss.py"}, args[1:]...)
	logger.Println(strings.Join(pythonCmd, " "))
	cmd := exec.Command("python", pythonCmd...)
	cmd.Stderr = logFile
	cmd.Stdout = logFile
	err = cmd.Run()
	if err != nil {
		logger.Fatal(err)
	}
}
