package main

import (
	"fmt"
	"log"
	"os"
	"regexp"

	"github.com/graniticio/inifile"
)

// Names of the config keys
const ALTERNATE_INIFILENAME_KEY = "iniFileName"
const ABSOLUTE_PATH_PREFIX_KEY = "absolutePathPrefix"
const CONDITIONER_REGEXP_KEY = "conditionerRegexp"
const CONDITIONER_REPLACEMENT_KEY = "conditionerReplacement"

func readConfig() (err error) {
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
		if e == nil {
			log.Printf("Using alternate ini file %v\n", alternateIniFileName)
			ini, e = inifile.NewIniConfigFromFile(iniFile)
			if e != nil {
				return fmt.Errorf("failed to read the alternate ini file - %q", e)
			}
		}
	}

	saver, e := ini.Section("saver")
	if e != nil {
		return fmt.Errorf("failed to read the saver section - %q", e)
	}

	absPrefix, e = saver.Value(ABSOLUTE_PATH_PREFIX_KEY)
	if e != nil {
		return fmt.Errorf("failed to read the prefix - %q", e)
	}

	conditionerSource := ""
	conditionerSource, _ = saver.Value(CONDITIONER_REGEXP_KEY)
	c, err := regexp.Compile(conditionerSource)
	if err == nil {
		conditioner = *c
	}

	replacement, _ = saver.Value(CONDITIONER_REPLACEMENT_KEY)

	return nil
}

/*
[wrapper]
; defaults
logFileName = ../pfnss_wrapper.log
scriptFileName = ../pfnss.py

; alternate configuration... if this is not provided, use this one
iniFileName = ../pfnss.ini

[data]
dbFileName = ../pfnss.db
maxFileId = 10

[server]
logUrl = http://192.168.1.189:8800/pfnss
maxSkipCount = 2

[saver]
absolutePathPrefix = /
; conditionerRegexp = ""
; conditionerReplacement = ""
switchSeconds = 2
doHide = True
*/
// func writeConfig() {
// }
