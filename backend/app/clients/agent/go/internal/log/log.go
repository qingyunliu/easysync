package log

import (
	"io"
	"log"
	"os"
	"path/filepath"
	"sync"
)

var (
	InfoLogger  *log.Logger
	ErrorLogger *log.Logger
	logFile     *os.File
	mutex       sync.Mutex
)

func Init(logPath string) error {
	mutex.Lock()
	defer mutex.Unlock()

	// 确保日志目录存在
	if err := os.MkdirAll(logPath, 0755); err != nil {
		return err
	}

	// 打开日志文件
	file, err := os.OpenFile(
		filepath.Join(logPath, "agent.log"),
		os.O_APPEND|os.O_CREATE|os.O_WRONLY,
		0644,
	)
	if err != nil {
		return err
	}

	// 设置日志输出
	InfoLogger = log.New(io.MultiWriter(os.Stdout, file), "INFO: ", log.Ldate|log.Ltime|log.Lshortfile)
	ErrorLogger = log.New(io.MultiWriter(os.Stderr, file), "ERROR: ", log.Ldate|log.Ltime|log.Lshortfile)

	logFile = file
	return nil
}

func Close() {
	mutex.Lock()
	defer mutex.Unlock()
	
	if logFile != nil {
		logFile.Close()
	}
}
