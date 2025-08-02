# 系统监控API文档

## 概述

系统监控API提供了获取系统性能指标和历史数据的功能，支持实时监控和历史数据分析。

## API接口

### 1. 获取系统监控历史数据

**接口地址：** `GET /api/monitor/system/metrics`

**功能描述：** 获取系统监控历史数据，支持时间范围查询和数据点限制。

**请求参数：**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| start_time | string | 否 | - | 开始时间（ISO格式） |
| end_time | string | 否 | - | 结束时间（ISO格式） |
| interval | string | 否 | 1m | 时间间隔（1m, 5m, 15m, 1h, 1d） |
| limit | integer | 否 | 24 | 返回数据点数量限制 |

**请求示例：**
```bash
GET /api/monitor/system/metrics?start_time=2024-01-01T00:00:00Z&end_time=2024-01-02T00:00:00Z&limit=24
```

**响应示例：**
```json
{
  "status": "success",
  "message": "系统监控数据获取成功",
  "data": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "cpu_usage": 45.2,
      "memory_usage": 68.5,
      "disk_usage": 72.1,
      "network_in": 1024000,
      "network_out": 512000,
      "load_average": 1.2
    }
  ]
}
```

### 2. 获取当前系统状态

**接口地址：** `GET /api/monitor/system/current`

**功能描述：** 获取当前系统状态，包括最新的监控指标。

**请求参数：** 无

**请求示例：**
```bash
GET /api/monitor/system/current
```

**响应示例：**
```json
{
  "status": "success",
  "message": "当前系统状态获取成功",
  "data": {
    "timestamp": "2024-01-01T12:00:00Z",
    "cpu_usage": 45.2,
    "memory_usage": 68.5,
    "disk_usage": 72.1,
    "network_in": 1024000,
    "network_out": 512000,
    "load_average": 1.2
  }
}
```

### 3. 手动触发系统指标收集

**接口地址：** `POST /api/monitor/system/collect`

**功能描述：** 手动触发系统指标收集，立即获取当前系统状态并存储到数据库。

**请求参数：** 无

**请求示例：**
```bash
POST /api/monitor/system/collect
```

**响应示例：**
```json
{
  "status": "success",
  "message": "系统指标收集成功",
  "data": {
    "timestamp": "2024-01-01T12:00:00Z",
    "metrics": {
      "cpu_usage": 45.2,
      "memory_usage": 68.5,
      "disk_usage": 72.1,
      "network_in": 1024000,
      "network_out": 512000,
      "load_average": 1.2
    }
  }
}
```

## 数据模型

### MonitorData 模型

系统监控数据存储在 `MonitorData` 表中，对于系统级别的监控数据，`node_id` 和 `client_id` 字段为 `None`。

**数据结构：**
```json
{
  "id": "uuid",
  "user_id": "user_uuid",
  "node_id": null,
  "client_id": null,
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "system": {
      "cpu_usage": 45.2,
      "memory_usage": 68.5,
      "disk_usage": 72.1,
      "network_in": 1024000,
      "network_out": 512000,
      "load_average": 1.2
    }
  }
}
```

## 定时任务

系统监控数据通过定时任务自动收集：

- **频率：** 每分钟收集一次
- **任务ID：** `system_monitoring_collection`
- **任务名称：** 系统监控数据收集

## 前端集成

### 更新图表数据

```javascript
const updateCharts = async () => {
  try {
    const now = new Date()
    const endTime = now.toISOString()
    const startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString()
    
    const response = await axios.get('/api/monitor/system/metrics', {
      params: {
        start_time: startTime,
        end_time: endTime,
        limit: 24
      }
    })
    
    if (response.data.status === 'success') {
      const monitorData = response.data.data
      
      // 提取时间标签和数据
      const timeLabels = monitorData.map(item => {
        const date = new Date(item.timestamp)
        return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      })
      
      const cpuData = monitorData.map(item => item.cpu_usage || 0)
      const memoryData = monitorData.map(item => item.memory_usage || 0)
      const networkInData = monitorData.map(item => item.network_in || 0)
      const networkOutData = monitorData.map(item => item.network_out || 0)
      
      // 更新图表
      updateChartsWithData(timeLabels, cpuData, memoryData, networkInData, networkOutData)
    }
  } catch (error) {
    console.error('获取监控数据失败:', error)
  }
}
```

### 更新当前状态

```javascript
const updateCurrentStatus = async () => {
  try {
    const response = await axios.get('/api/monitor/system/current')
    
    if (response.data.status === 'success') {
      const currentData = response.data.data
      
      // 更新状态显示
      systemStatus.cpu_usage = currentData.cpu_usage || 0
      systemStatus.memory_usage = currentData.memory_usage || 0
      systemStatus.disk_usage = currentData.disk_usage || 0
      systemStatus.network_in = currentData.network_in || 0
      systemStatus.network_out = currentData.network_out || 0
    }
  } catch (error) {
    console.error('获取当前状态失败:', error)
  }
}
```

## 错误处理

所有API接口都包含统一的错误处理：

```json
{
  "status": "error",
  "message": "错误描述信息"
}
```

常见错误码：
- `400`：请求参数错误
- `401`：未授权访问
- `500`：服务器内部错误

## 性能优化

1. **数据分页：** 支持 `limit` 参数限制返回数据量
2. **时间范围：** 支持时间范围查询，避免获取过多历史数据
3. **数据库索引：** 在 `timestamp` 字段上建立索引，提高查询性能
4. **数据清理：** 定期清理旧数据，保持数据库性能

## 监控指标说明

| 指标名称 | 单位 | 说明 |
|----------|------|------|
| cpu_usage | % | CPU使用率 |
| memory_usage | % | 内存使用率 |
| disk_usage | % | 磁盘使用率 |
| network_in | bytes/s | 网络入流量 |
| network_out | bytes/s | 网络出流量 |
| load_average | - | 系统负载平均值 | 