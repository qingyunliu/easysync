package monitor

import (
	"fmt"
	"sync"
	"time"
	"github.com/shirou/gopsutil/v3/cpu"
	"github.com/shirou/gopsutil/v3/disk"
	"github.com/shirou/gopsutil/v3/mem"
	"github.com/shirou/gopsutil/v3/net"
)

// Monitor 代表系统监控器
type Monitor struct {
	running bool
	mutex   sync.RWMutex
}

// MonitorData 代表监控数据
type MonitorData struct {
	CPU      float64       `json:"cpu"`
	Memory   MemoryStats   `json:"memory"`
	Network  NetworkStats  `json:"network"`
	Disk     DiskStats     `json:"disk"`
	Time     time.Time     `json:"time"`
}

// MemoryStats 代表内存统计信息
type MemoryStats struct {
	Total     uint64  `json:"total"`
	Used      uint64  `json:"used"`
	Free      uint64  `json:"free"`
	UsageRate float64 `json:"usage_rate"`
}

// NetworkStats 代表网络统计信息
type NetworkStats struct {
	BytesSent    uint64 `json:"bytes_sent"`
	BytesRecv    uint64 `json:"bytes_recv"`
	PacketsSent  uint64 `json:"packets_sent"`
	PacketsRecv  uint64 `json:"packets_recv"`
}

// DiskStats 代表磁盘统计信息
type DiskStats struct {
	Total     uint64  `json:"total"`
	Used      uint64  `json:"used"`
	Free      uint64  `json:"free"`
	UsageRate float64 `json:"usage_rate"`
}

// NewMonitor 创建新的监控器
func NewMonitor() *Monitor {
	return &Monitor{
		running: false,
	}
}

// Start 启动监控
func (m *Monitor) Start() {
	m.mutex.Lock()
	defer m.mutex.Unlock()
	m.running = true
}

// Stop 停止监控
func (m *Monitor) Stop() {
	m.mutex.Lock()
	defer m.mutex.Unlock()
	m.running = false
}

// IsRunning 检查监控是否在运行
func (m *Monitor) IsRunning() bool {
	m.mutex.RLock()
	defer m.mutex.RUnlock()
	return m.running
}

// Collect 收集监控数据
func (m *Monitor) Collect() (*MonitorData, error) {
	m.mutex.Lock()
	defer m.mutex.Unlock()

	if !m.running {
		return nil, fmt.Errorf("监控器未运行")
	}

	data := &MonitorData{
		Time: time.Now(),
	}

	// 收集CPU使用率
	cpuPercent, err := cpu.Percent(time.Second, false)
	if err != nil {
		return nil, fmt.Errorf("获取CPU使用率失败: %v", err)
	}
	if len(cpuPercent) > 0 {
		data.CPU = cpuPercent[0]
	}

	// 收集内存信息
	memInfo, err := mem.VirtualMemory()
	if err != nil {
		return nil, fmt.Errorf("获取内存信息失败: %v", err)
	}
	data.Memory = MemoryStats{
		Total:     memInfo.Total,
		Used:      memInfo.Used,
		Free:      memInfo.Free,
		UsageRate: memInfo.UsedPercent,
	}

	// 收集网络信息
	netStats, err := net.IOCounters(false)
	if err != nil {
		return nil, fmt.Errorf("获取网络统计信息失败: %v", err)
	}
	if len(netStats) > 0 {
		data.Network = NetworkStats{
			BytesSent:   netStats[0].BytesSent,
			BytesRecv:   netStats[0].BytesRecv,
			PacketsSent: netStats[0].PacketsSent,
			PacketsRecv: netStats[0].PacketsRecv,
		}
	}

	// 收集磁盘信息
	diskStats, err := disk.Usage("/")
	if err != nil {
		return nil, fmt.Errorf("获取磁盘使用情况失败: %v", err)
	}
	data.Disk = DiskStats{
		Total:     diskStats.Total,
		Used:      diskStats.Used,
		Free:      diskStats.Free,
		UsageRate: diskStats.UsedPercent,
	}

	return data, nil
}
