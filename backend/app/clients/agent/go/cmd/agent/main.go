package main

import (
	"flag"
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"easysync/agent/internal/agent"
	"easysync/agent/internal/config"
	"easysync/agent/internal/log"
)

var (
	configPath string
	clientID   string
)

func init() {
	flag.StringVar(&configPath, "config", "config.yaml", "配置文件路径")
	flag.StringVar(&clientID, "client-id", "", "客户端ID")
}

func main() {
	flag.Parse()

	// 初始化日志
	if err := log.Init("logs"); err != nil {
		fmt.Printf("初始化日志失败: %v\n", err)
		os.Exit(1)
	}
	defer log.Close()

	// 加载配置
	cfg, err := config.LoadConfig(configPath)
	if err != nil {
		log.ErrorLogger.Printf("加载配置失败: %v", err)
		os.Exit(1)
	}

	// 创建Agent
	agent, err := agent.NewAgent(cfg)
	if err != nil {
		log.ErrorLogger.Printf("创建Agent失败: %v", err)
		os.Exit(1)
	}

	// 连接到服务器
	if err := agent.Connect(clientID); err != nil {
		log.ErrorLogger.Printf("连接服务器失败: %v", err)
		os.Exit(1)
	}

	// 启动Agent
	if err := agent.Start(); err != nil {
		log.ErrorLogger.Printf("启动Agent失败: %v", err)
		os.Exit(1)
	}

	// 等待中断信号
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	// 停止Agent
	agent.Stop()
}
