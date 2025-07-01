package sync

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/fsnotify/fsnotify"
	"easysync/agent/internal/websocket"
	"easysync/agent/internal/log"
)

// 同步任务结构体
type SyncTask struct {
	ID          string        `json:"id"`
	Source      string        `json:"source"`      // 源路径
	Destination string        `json:"destination"` // 目标路径
	Options     SyncOptions   `json:"options"`     // 同步选项
	Schedule    TaskSchedule  `json:"schedule"`    // 调度配置
	Status      TaskStatus    `json:"status"`      // 任务状态
	cmd         *exec.Cmd     // 用于存储当前执行的命令
}

// 同步选项
type SyncOptions struct {
	ExcludePatterns   []string `json:"exclude_patterns"` // 排除模式
	IncludePatterns   []string `json:"include_patterns"` // 包含模式
	Delete            bool     `json:"delete"`           // 是否删除目标端多余文件
	Compress          bool     `json:"compress"`         // 是否压缩传输
	BandwidthLimit    int      `json:"bandwidth_limit"`  // 带宽限制(KB/s)
	Timeout           int      `json:"timeout"`          // 超时时间(分钟)
	ImmediateSync     bool     `json:"immediate_sync"`   // 是否立即同步文件变更
}

// 任务调度配置
type TaskSchedule struct {
	Type     string `json:"type"`      // 调度类型: manual, interval, cron
	Interval int    `json:"interval"`   // 间隔时间(秒)
	Cron     string `json:"cron"`       // cron表达式
}

// 任务状态
type TaskStatus struct {
	State       string    `json:"state"`        // 状态: pending, running, completed, failed
	LastRun     time.Time `json:"last_run"`     // 上次运行时间
	NextRun     time.Time `json:"next_run"`     // 下次运行时间
	Error       string    `json:"error"`        // 错误信息
	Progress    float64     `json:"progress"`     // 进度(0-100)
	Stats       SyncStats   `json:"stats"`        // 统计信息
}

// 同步统计信息
type SyncStats struct {
	FilesTransferred int   `json:"files_transferred"`
	BytesTransferred int64 `json:"bytes_transferred"`
	TimeElapsed      int64 `json:"time_elapsed"` // 毫秒
	TransferRate     float64 `json:"transfer_rate"` // 传输速率 (bytes/sec)
	TotalSize        int64 `json:"total_size"` // 总大小 (bytes)
}

// TaskQueue 任务队列
type TaskQueue struct {
	tasks  []*SyncTask
	mutex  sync.Mutex
	cond   *sync.Cond
}

// NewTaskQueue 创建新的任务队列
func NewTaskQueue() *TaskQueue {
	q := &TaskQueue{
		tasks: make([]*SyncTask, 0),
	}
	q.cond = sync.NewCond(&q.mutex)
	return q
}

// Push 添加任务到队列
func (q *TaskQueue) Push(task *SyncTask) {
	q.mutex.Lock()
	defer q.mutex.Unlock()
	
	q.tasks = append(q.tasks, task)
	q.cond.Signal() // 通知等待的goroutine有新任务
}

// Pop 从队列中取出任务
func (q *TaskQueue) Pop() *SyncTask {
	q.mutex.Lock()
	defer q.mutex.Unlock()
	
	// 如果队列为空，等待新任务
	for len(q.tasks) == 0 {
		q.cond.Wait()
	}
	
	// 取出第一个任务
	task := q.tasks[0]
	q.tasks = q.tasks[1:]
	return task
}

// Len 获取队列长度
func (q *TaskQueue) Len() int {
	q.mutex.Lock()
	defer q.mutex.Unlock()
	return len(q.tasks)
}

// Clear 清空队列
func (q *TaskQueue) Clear() {
	q.mutex.Lock()
	defer q.mutex.Unlock()
	q.tasks = q.tasks[:0]
}

type Syncer struct {
	tasks       map[string]*SyncTask
	wsClient    *websocket.Client
	taskQueue   *TaskQueue
	stopChan    chan struct{}
	wg          sync.WaitGroup
	running     bool
	mutex       sync.RWMutex
}

// NewSyncer 创建新的同步器
func NewSyncer(wsClient *websocket.Client) *Syncer {
	return &Syncer{
		tasks:     make(map[string]*SyncTask),
		wsClient:  wsClient,
		taskQueue: NewTaskQueue(),
		stopChan:  make(chan struct{}),
	}
}

// Start 启动同步器
func (s *Syncer) Start() error {
	s.mutex.Lock()
	if s.running {
		s.mutex.Unlock()
		return fmt.Errorf("同步器已经在运行")
	}
	s.running = true
	s.mutex.Unlock()

	// 注册WebSocket消息处理器
	s.wsClient.RegisterHandler("sync_task", s.handleSyncTask)
	s.wsClient.RegisterHandler("cancel_task", s.handleCancelTask)
	
	// 启动任务调度器
	go s.runScheduler()
	
	// 启动任务处理goroutine
	s.wg.Add(1)
	go s.processTasks()

	return nil
}

// 处理同步任务消息
func (s *Syncer) handleSyncTask(msg []byte) error {
	var task SyncTask
	if err := json.Unmarshal(msg, &task); err != nil {
		return fmt.Errorf("解析同步任务失败: %v", err)
	}

	// 验证任务
	if err := s.validateTask(&task); err != nil {
		return err
	}

	// 添加到任务队列
	s.taskQueue.Push(&task)
	return nil
}

// 处理取消任务消息
func (s *Syncer) handleCancelTask(msg []byte) error {
	var taskID string
	if err := json.Unmarshal(msg, &taskID); err != nil {
		return fmt.Errorf("解析取消任务消息失败: %v", err)
	}
	
	s.mutex.Lock()
	if task, exists := s.tasks[taskID]; exists {
		if task.cmd != nil && task.cmd.Process != nil {
			task.cmd.Process.Kill()
		}
		delete(s.tasks, taskID)
	}
	s.mutex.Unlock()
	
	return nil
}

// 运行任务调度器
func (s *Syncer) runScheduler() {
	ticker := time.NewTicker(time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			now := time.Now()
			s.mutex.RLock()
			for _, task := range s.tasks {
				if shouldRun(task, now) {
					s.taskQueue.Push(task)
				}
			}
			s.mutex.RUnlock()
		case <-s.stopChan:
			return
		}
	}
}

// 判断任务是否应该运行
func shouldRun(task *SyncTask, now time.Time) bool {
	if task.Status.State == "running" {
		return false
	}

	switch task.Schedule.Type {
	case "manual":
		return false
	case "interval":
		return now.After(task.Status.NextRun)
	case "cron":
		// TODO: 实现cron表达式解析
		return false
	default:
		return false
	}
}

// 执行同步任务
func (s *Syncer) executeTask(task *SyncTask) {
	// 更新任务状态
	task.Status.State = "running"
	task.Status.LastRun = time.Now()
	task.Status.Error = ""
	task.Status.Progress = 0

	// 构建rsync命令
	args := buildRsyncArgs(task)
	task.cmd = exec.Command("rsync", args...)

	// 执行命令
	output, err := task.cmd.CombinedOutput()
	if err != nil {
		task.Status.State = "failed"
		task.Status.Error = fmt.Sprintf("执行失败: %v\n%s", err, string(output))
		return
	}

	// 解析输出
	stats := parseRsyncOutput(string(output))
	task.Status.Stats = *stats
	task.Status.State = "completed"
	task.Status.Progress = 100

	// 计算下次运行时间
	task.Status.NextRun = calculateNextRun(task)
}

// 构建rsync命令参数
func buildRsyncArgs(task *SyncTask) []string {
	args := []string{"-avz"}
	
	if task.Options.Compress {
		args = append(args, "-z")
	}
	
	if task.Options.Delete {
		args = append(args, "--delete")
	}
	
	if task.Options.BandwidthLimit > 0 {
		args = append(args, fmt.Sprintf("--bwlimit=%d", task.Options.BandwidthLimit))
	}
	
	// 添加排除模式
	for _, pattern := range task.Options.ExcludePatterns {
		args = append(args, "--exclude", pattern)
	}
	
	// 添加包含模式
	for _, pattern := range task.Options.IncludePatterns {
		args = append(args, "--include", pattern)
	}
	
	args = append(args, task.Source, task.Destination)
	return args
}

// 发送任务状态更新
func (s *Syncer) sendTaskStatus(task *SyncTask) {
	status := struct {
		TaskID string     `json:"task_id"`
		Status TaskStatus `json:"status"`
	}{
		TaskID: task.ID,
		Status: task.Status,
	}
	
	data, _ := json.Marshal(status)
	s.wsClient.Send("task_status", data)
}

// processTasks 处理任务队列中的任务
func (s *Syncer) processTasks() {
	defer s.wg.Done()

	for {
		select {
		case <-s.stopChan:
			return
		default:
			// 从队列中获取任务
			task := s.taskQueue.Pop()
			
			// 执行任务
			s.wg.Add(1)
			go func(t *SyncTask) {
				defer s.wg.Done()
				s.executeTask(t)
			}(task)
		}
	}
}

// AddTask 添加同步任务
func (s *Syncer) AddTask(task *SyncTask) error {
	if err := s.validateTask(task); err != nil {
		return err
	}

	s.mutex.Lock()
	defer s.mutex.Unlock()

	s.tasks[task.ID] = task
	return nil
}

// Stop 停止同步器
func (s *Syncer) Stop() {
	s.mutex.Lock()
	if !s.running {
		s.mutex.Unlock()
		return
	}
	s.running = false
	s.mutex.Unlock()

	close(s.stopChan)
	s.wg.Wait()
	s.taskQueue.Clear()
}

// IsRunning 检查同步器是否在运行
func (s *Syncer) IsRunning() bool {
	s.mutex.RLock()
	defer s.mutex.RUnlock()
	return s.running
}

func (s *Syncer) ValidateConfig() error {
	s.mutex.RLock()
	defer s.mutex.RUnlock()

	for _, task := range s.tasks {
		if !filepath.IsAbs(task.Source) {
			return fmt.Errorf("源目录路径必须是绝对路径: %s", task.Source)
		}
		if !filepath.IsAbs(task.Destination) {
			return fmt.Errorf("目标目录路径必须是绝对路径: %s", task.Destination)
		}
		if _, err := os.Stat(task.Source); os.IsNotExist(err) {
			return fmt.Errorf("源目录不存在: %s", task.Source)
		}
		if _, err := os.Stat(task.Destination); os.IsNotExist(err) {
			return fmt.Errorf("目标目录不存在: %s", task.Destination)
		}
	}
	return nil
}

func (s *Syncer) GetSyncStatus() map[string]interface{} {
	s.mutex.RLock()
	defer s.mutex.RUnlock()

	status := make(map[string]interface{})
	for id, task := range s.tasks {
		status[id] = task.Status
	}
	return status
}

// watchDirs 监视目录变化
func (s *Syncer) watchDirs() error {
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		return err
	}

	for _, task := range s.tasks {
		err = filepath.Walk(task.Source, func(path string, info os.FileInfo, err error) error {
			if info.IsDir() {
				return watcher.Add(path)
			}
			return nil
		})
		if err != nil {
			return err
		}
	}

	go func() {
		for {
			select {
			case event := <-watcher.Events:
				s.handleFileEvent(event)
			case err := <-watcher.Errors:
				log.ErrorLogger.Printf("文件监控错误: %v", err)
			}
		}
	}()

	return nil
}

func (s *Syncer) handleFileEvent(event fsnotify.Event) {
	// 获取事件相关的任务
	var relatedTask *SyncTask
	for _, task := range s.tasks {
		if strings.HasPrefix(event.Name, task.Source) {
			relatedTask = task
			break
		}
	}
	
	if relatedTask == nil {
		return
	}

	// 根据事件类型处理
	switch event.Op {
	case fsnotify.Create:
		// 新文件创建，检查是否需要立即同步
		if relatedTask.Options.ImmediateSync {
			go s.executeTask(relatedTask)
		}
	case fsnotify.Write:
		// 文件修改，检查是否需要立即同步
		if relatedTask.Options.ImmediateSync {
			go s.executeTask(relatedTask)
		}
	case fsnotify.Remove:
		// 文件删除，如果启用了删除选项，立即同步
		if relatedTask.Options.Delete {
			go s.executeTask(relatedTask)
		}
	case fsnotify.Rename:
		// 文件重命名，需要同步
		go s.executeTask(relatedTask)
	}
}

// parseRsyncOutput 解析rsync输出
func parseRsyncOutput(output string) *SyncStats {
	stats := &SyncStats{}
	
	// 使用正则表达式解析rsync输出
	re := regexp.MustCompile(`sent\s+([\d,]+)\s+bytes\s+received\s+([\d,]+)\s+bytes\s+([\d.]+)\s+bytes/sec`)
	matches := re.FindStringSubmatch(output)
	
	if len(matches) >= 4 {
		// 解析发送的字节数
		sentBytes := strings.ReplaceAll(matches[1], ",", "")
		stats.BytesTransferred, _ = strconv.ParseInt(sentBytes, 10, 64)
		
		// 解析接收的字节数
		receivedBytes := strings.ReplaceAll(matches[2], ",", "")
		received, _ := strconv.ParseInt(receivedBytes, 10, 64)
		stats.BytesTransferred += received
		
		// 解析传输速率
		rate, _ := strconv.ParseFloat(matches[3], 64)
		stats.TransferRate = rate
	}
	
	// 解析文件数量
	re = regexp.MustCompile(`Number of files:\s+([\d,]+)`)
	matches = re.FindStringSubmatch(output)
	if len(matches) >= 2 {
		files := strings.ReplaceAll(matches[1], ",", "")
		stats.FilesTransferred, _ = strconv.Atoi(files)
	}
	
	// 解析总大小
	re = regexp.MustCompile(`total size is\s+([\d,]+)`)
	matches = re.FindStringSubmatch(output)
	if len(matches) >= 2 {
		totalSize := strings.ReplaceAll(matches[1], ",", "")
		stats.TotalSize, _ = strconv.ParseInt(totalSize, 10, 64)
	}
	
	// 解析耗时
	re = regexp.MustCompile(`total time is\s+([\d.]+)`)
	matches = re.FindStringSubmatch(output)
	if len(matches) >= 2 {
		timeElapsed, _ := strconv.ParseFloat(matches[1], 64)
		stats.TimeElapsed = int64(timeElapsed * 1000) // 转换为毫秒
	}
	
	return stats
}

// calculateNextRun 计算下次运行时间
func calculateNextRun(task *SyncTask) time.Time {
	// 实现计算下次运行时间的逻辑
	return time.Now().Add(time.Duration(task.Schedule.Interval) * time.Second)
}

// 添加任务验证方法
func (s *Syncer) validateTask(task *SyncTask) error {
	if !filepath.IsAbs(task.Source) {
		return fmt.Errorf("源路径必须是绝对路径: %s", task.Source)
	}
	if !filepath.IsAbs(task.Destination) {
		return fmt.Errorf("目标路径必须是绝对路径: %s", task.Destination)
	}
	// 检查源目录是否存在
	if _, err := os.Stat(task.Source); os.IsNotExist(err) {
		return fmt.Errorf("源目录不存在: %s", task.Source)
	}
	return nil
}
