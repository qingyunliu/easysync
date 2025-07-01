package agent

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"easysync/agent/internal/config"
	"easysync/agent/internal/log"
	"easysync/agent/internal/monitor"
	syncer "easysync/agent/internal/sync"
	"easysync/agent/internal/websocket"
)

// Agent 代表一个Agent实例
type Agent struct {
	config     *config.Config
	monitor    *monitor.Monitor
	syncer     *syncer.Syncer
	wsClient   *websocket.Client
	ctx        context.Context
	cancel     context.CancelFunc
	wg         sync.WaitGroup
	running    bool
	mutex      sync.RWMutex
}

// NewAgent 创建新的Agent实例
func NewAgent(cfg *config.Config) (*Agent, error) {
	ctx, cancel := context.WithCancel(context.Background())
	
	// 创建WebSocket客户端
	wsClient := websocket.NewClient(cfg.ServerURL)
	
	// 创建监控器
	mon := monitor.NewMonitor()
	
	// 创建同步器
	sync := syncer.NewSyncer(wsClient)
	
	return &Agent{
		config:   cfg,
		monitor:  mon,
		syncer:   sync,
		wsClient: wsClient,
		ctx:      ctx,
		cancel:   cancel,
	}, nil
}

// Start 启动Agent
func (a *Agent) Start() error {
	a.mutex.Lock()
	if a.running {
		a.mutex.Unlock()
		return fmt.Errorf("Agent已经在运行")
	}
	a.running = true
	a.mutex.Unlock()

	// 连接WebSocket服务器
	if err := a.wsClient.Connect(); err != nil {
		return fmt.Errorf("连接WebSocket服务器失败: %v", err)
	}

	// 启动监控器
	a.monitor.Start()

	// 启动同步器
	if err := a.syncer.Start(); err != nil {
		return fmt.Errorf("启动同步器失败: %v", err)
	}

	// 启动监控数据收集
	a.wg.Add(1)
	go a.collectMonitorData()

	// 启动心跳
	a.wg.Add(1)
	go a.heartbeat()

	return nil
}

// Stop 停止Agent
func (a *Agent) Stop() {
	a.mutex.Lock()
	if !a.running {
		a.mutex.Unlock()
		return
	}
	a.running = false
	a.mutex.Unlock()

	// 取消上下文
	a.cancel()

	// 停止监控器
	a.monitor.Stop()

	// 停止同步器
	a.syncer.Stop()

	// 关闭WebSocket连接
	a.wsClient.Close()

	// 等待所有goroutine结束
	a.wg.Wait()
}

// collectMonitorData 收集监控数据
func (a *Agent) collectMonitorData() {
	defer a.wg.Done()

	ticker := time.NewTicker(a.config.MonitorInterval)
	defer ticker.Stop()

	for {
		select {
		case <-a.ctx.Done():
			return
		case <-ticker.C:
			data, err := a.monitor.Collect()
			if err != nil {
				log.ErrorLogger.Printf("收集监控数据失败: %v", err)
				continue
			}

			// 发送监控数据
			if err := a.wsClient.Send("monitor_data", data); err != nil {
				log.ErrorLogger.Printf("发送监控数据失败: %v", err)
			}
		}
	}
}

// heartbeat 发送心跳
func (a *Agent) heartbeat() {
	defer a.wg.Done()

	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-a.ctx.Done():
			return
		case <-ticker.C:
			// 发送心跳
			if err := a.wsClient.Send("heartbeat", map[string]interface{}{
				"timestamp": time.Now().Unix(),
			}); err != nil {
				log.ErrorLogger.Printf("发送心跳失败: %v", err)
			}
		}
	}
}

// IsRunning 检查Agent是否在运行
func (a *Agent) IsRunning() bool {
	a.mutex.RLock()
	defer a.mutex.RUnlock()
	return a.running
}

// GetStatus 获取Agent状态
func (a *Agent) GetStatus() map[string]interface{} {
	return map[string]interface{}{
		"running":    a.IsRunning(),
		"monitor":    a.monitor.IsRunning(),
		"syncer":     a.syncer.IsRunning(),
		"websocket":  a.wsClient.IsConnected(),
		"sync_tasks": a.syncer.GetSyncStatus(),
	}
}

// handleSyncTask 处理同步任务
func (a *Agent) handleSyncTask(msg []byte) error {
	var task syncer.SyncTask
	if err := json.Unmarshal(msg, &task); err != nil {
		return fmt.Errorf("解析同步任务失败: %v", err)
	}

	// 将任务添加到同步器的队列中
	if err := a.syncer.AddTask(&task); err != nil {
		return fmt.Errorf("添加同步任务失败: %v", err)
	}

	return nil
}

// Connect 连接到服务器
func (a *Agent) Connect(clientID string) error {
	// 连接WebSocket
	if err := a.wsClient.Connect(); err != nil {
		return err
	}

	// 发送join消息
	if err := a.wsClient.Send("join", map[string]interface{}{
		"client_id": clientID,
	}); err != nil {
		return fmt.Errorf("发送join消息失败: %v", err)
	}

	return nil
}
