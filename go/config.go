package secureput

import (
	"bytes"
	"log"
	"os"
	"path/filepath"
	"runtime"

	"github.com/gookit/config/v2"
	"github.com/gookit/config/v2/yamlv3"
)

func DumpConfig(appName string) {
	file := filepath.Join(appConfigDir(appName), "prefs.yml")
	ensureDir(file)

	buf := new(bytes.Buffer)
	_, err := config.DumpTo(buf, config.Yaml)
	if err != nil {
		panic(err)
	}
	err = os.WriteFile(file, buf.Bytes(), 0755)
	if err != nil {
		panic(err)
	}
}

func InitConfig(appName string) {
	file := filepath.Join(appConfigDir(appName), "prefs.yml")
	if _, serr := os.Stat(file); serr != nil {
		if os.IsNotExist(serr) {
			ensureDir(file)
			file, err := os.Create(file)
			if err != nil {
				log.Fatal(err)
			}
			file.Close()
		}
	}

	config.WithOptions(config.ParseEnv)

	// add driver for support yaml content
	config.AddDriver(yamlv3.Driver)

	err := config.LoadFiles(file)
	if err != nil {
		panic(err)
	}
}

func rootConfigDir() string {
	homeDir, _ := os.UserHomeDir()

	switch runtime.GOOS {
	case "darwin":
		return filepath.Join(filepath.Join(homeDir, "Library"), "Application Support")
	case "linux":
		return filepath.Join(homeDir, ".config")
	case "windows":
		return filepath.Join(filepath.Join(homeDir, "AppData"), "Roaming")
	}

	return ""
}

func appConfigDir(appName string) string {
	return filepath.Join(rootConfigDir(), appName)
}

func ensureDir(fileName string) {
	dirName := filepath.Dir(fileName)
	if _, serr := os.Stat(dirName); serr != nil {
		merr := os.MkdirAll(dirName, os.ModePerm)
		if merr != nil {
			panic(merr)
		}
	}
}
