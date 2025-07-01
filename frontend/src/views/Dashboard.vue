<template>
  <div class="dashboard-container">
    <!-- 系统状态卡片 -->
    <el-card class="system-card">
      <template #header>
        <div class="card-header">
          <span>系统状态</span>
        </div>
      </template>
      <div class="system-content">
        <div class="system-status">
          <div class="status-value" :class="getSystemStatusClass(stats.system.systemStatus)">
            {{ stats.system.systemStatus }}
          </div>
          <div class="status-label">当前系统状态</div>
        </div>
        <div class="system-metrics">
          <div class="metric-item">
            <div class="metric-icon">
              <el-icon><Cpu /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-value">{{ stats.system.cpuUsage }}%</div>
              <div class="metric-label">CPU使用率</div>
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-icon">
              <el-icon><Memory /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-value">{{ stats.system.memoryUsage }}%</div>
              <div class="metric-label">内存使用率</div>
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-icon">
              <el-icon><Monitor /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-value">{{ stats.system.diskUsage }}%</div>
              <div class="metric-label">磁盘使用率</div>
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-icon">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-value">{{ formatSize(stats.system.networkTraffic) }}/s</div>
              <div class="metric-label">网络流量</div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 资源统计卡片 -->
    <el-row :gutter="20" class="resource-row">
      <el-col :span="8">
        <el-card class="resource-card">
          <template #header>
            <div class="card-header">
              <span>客户端</span>
              <el-button type="text" @click="$router.push('/clients')">查看全部</el-button>
            </div>
          </template>
          <div class="resource-content">
            <div class="resource-value">{{ stats.clients.clientCount }}</div>
            <div class="resource-label">已配置客户端</div>
            <div class="resource-detail">
              <div class="detail-item">
                <span class="label">在线:</span>
                <span class="value success">{{ stats.clients.onlineClients }}</span>
              </div>
              <div class="detail-item">
                <span class="label">离线:</span>
                <span class="value warning">{{ stats.clients.offlineClients }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Agent已安装:</span>
                <span class="value">{{ stats.clients.installedAgents }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Agent未安装:</span>
                <span class="value">{{ stats.clients.uninstalledAgents }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="resource-card">
          <template #header>
            <div class="card-header">
              <span>节点</span>
              <el-button type="text" @click="$router.push('/nodes')">查看全部</el-button>
            </div>
          </template>
          <div class="resource-content">
            <div class="resource-value">{{ stats.nodes.nodeCount }}</div>
            <div class="resource-label">已配置节点</div>
            <div class="resource-detail">
              <div class="detail-item">
                <span class="label">在线:</span>
                <span class="value success">{{ stats.nodes.onlineNodes }}</span>
              </div>
              <div class="detail-item">
                <span class="label">离线:</span>
                <span class="value warning">{{ stats.nodes.offlineNodes }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Proxy已安装:</span>
                <span class="value">{{ stats.nodes.installedNodes }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Proxy未安装:</span>
                <span class="value">{{ stats.nodes.uninstalledNodes }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="resource-card">
          <template #header>
            <div class="card-header">
              <span>存储节点</span>
              <el-button type="text" @click="$router.push('/storages')">查看全部</el-button>
            </div>
          </template>
          <div class="resource-content">
            <div class="resource-value">{{ stats.storages.storageCount }}</div>
            <div class="resource-label">已配置存储节点</div>
            <div class="resource-detail">
              <div class="detail-item">
                <span class="label">已挂载:</span>
                <span class="value success">{{ stats.storages.mountedCount }}</span>
              </div>
              <div class="detail-item">
                <span class="label">未挂载:</span>
                <span class="value warning">{{ stats.storages.unmountedCount }}</span>
              </div>
              <div class="detail-item">
                <span class="label">总容量:</span>
                <span class="value">{{ formatSize(stats.storages.totalStorageSize) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">已使用:</span>
                <span class="value">{{ formatSize(stats.storages.usedStorageSize) }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 任务统计卡片 -->
    <el-card class="task-card">
      <template #header>
        <div class="card-header">
          <span>同步任务</span>
          <el-button type="text" @click="$router.push('/tasks')">查看全部</el-button>
        </div>
      </template>
      <div class="task-content">
        <div class="task-overview">
          <div class="overview-item">
            <div class="overview-value">{{ stats.tasks.taskCount }}</div>
            <div class="overview-label">总任务数</div>
          </div>
          <div class="overview-item">
            <div class="overview-value success">{{ stats.tasks.runningCount }}</div>
            <div class="overview-label">运行中</div>
          </div>
          <div class="overview-item">
            <div class="overview-value">{{ stats.tasks.stoppedCount }}</div>
            <div class="overview-label">已停止</div>
          </div>
          <div class="overview-item">
            <div class="overview-value">{{ stats.tasks.todaySyncCount }}</div>
            <div class="overview-label">今日同步</div>
          </div>
          <div class="overview-item">
            <div class="overview-value" :class="getSuccessRateClass(calculateSuccessRate())">
              {{ calculateSuccessRate() }}%
            </div>
            <div class="overview-label">成功率</div>
          </div>
        </div>
        <div class="task-detail">
          <el-table :data="recentTasks" style="width: 100%" :max-height="300">
            <el-table-column prop="name" label="任务名称" min-width="150" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">
                  {{ getStatusText(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="start_time" label="开始时间" width="180">
              <template #default="scope">
                {{ formatDateTime(scope.row.start_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="end_time" label="结束时间" width="180">
              <template #default="scope">
                {{ scope.row.end_time ? formatDateTime(scope.row.end_time) : '-' }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>

    <!-- 系统通知卡片 -->
    <el-card class="notification-card">
      <template #header>
        <div class="card-header">
          <span>系统通知</span>
        </div>
      </template>
      <el-timeline>
        <el-timeline-item
          v-for="(notification, index) in recentNotifications"
          :key="index"
          :type="getNotificationType(notification.type)"
          :timestamp="formatDateTime(notification.created_at)"
        >
          {{ notification.message }}
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Cpu,
  Monitor,
  Connection
} from '@element-plus/icons-vue'
import { 
  DataLine as Memory
} from '@element-plus/icons-vue'
import axios from 'axios'

// 统计数据
const stats = ref({
  storages: {
    storageCount: 0,
    mountedCount: 0,
    unmountedCount: 0,
    totalStorageSize: 0,
    usedStorageSize: 0,
  },
  nodes: {
    nodeCount: 0,
    onlineNodes: 0,
    offlineNodes: 0,
    installedNodes: 0,
    uninstalledNodes: 0,
  },
  tasks: {
    taskCount: 0,
    runningCount: 0,
    stoppedCount: 0,
    todaySyncCount: 0,
    todaySuccessCount: 0,
    todayFailedCount: 0,
  },
  clients: {
    clientCount: 0,
    onlineClients: 0,
    offlineClients: 0,
    installedAgents: 0,
    uninstalledAgents: 0,
  },
  system: {
    systemStatus: 0,
    cpuUsage: 0,
    memoryUsage: 0,
    diskUsage: 0,
    networkTraffic: 0
  }
})

// 最近任务
const recentTasks = ref([])

// 最近通知
const recentNotifications = ref([])

// 获取仪表盘数据
const fetchDashboardData = async () => {
  try {
    const response = await axios.get('/api/dashboard')
    stats.value = response.data.data
    recentTasks.value = response.data.data.recent_tasks
    recentNotifications.value = response.data.data.recent_notifications
  } catch (error) {
    ElMessage.error('获取仪表盘数据失败')
  }
}

// 工具函数
const getStatusType = (status) => {
  switch (status) {
    case 'completed':
      return 'success'
    case 'failed':
      return 'danger'
    case 'running':
      return 'warning'
    default:
      return 'info'
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'completed':
      return '成功'
    case 'failed':
      return '失败'
    case 'running':
      return '运行中'
    default:
      return '未知'
  }
}

const getNotificationType = (type) => {
  switch (type) {
    case 'success':
      return 'success'
    case 'warning':
      return 'warning'
    case 'error':
      return 'danger'
    default:
      return 'info'
  }
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 格式化文件大小
const formatSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 计算同步成功率
const calculateSuccessRate = () => {
  const total = stats.value.todaySuccessCount + stats.value.todayFailedCount
  if (total === 0) return 0
  return ((stats.value.todaySuccessCount / total) * 100).toFixed(1)
}

// 获取系统状态样式
const getSystemStatusClass = (status) => {
  switch (status) {
    case '正常':
      return 'success'
    case '注意':
      return 'warning'
    case '警告':
      return 'danger'
    default:
      return 'info'
  }
}

// 获取成功率样式
const getSuccessRateClass = (rate) => {
  const numRate = parseFloat(rate)
  if (numRate >= 90) return 'success'
  if (numRate >= 70) return 'warning'
  return 'danger'
}

// 生命周期钩子
onMounted(() => {
  fetchDashboardData()
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.system-card,
.resource-card,
.task-card,
.notification-card {
  transition: all 0.3s ease;
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
}

.system-card {
  margin-bottom: 20px;
  .system-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px;
  }
  .system-status {
    text-align: center;
    padding-right: 40px;
    border-right: 1px solid #EBEEF5;
  }
  .status-value {
    font-size: 36px;
    font-weight: bold;
    margin-bottom: 10px;
    &.success { color: #67C23A; }
    &.warning { color: #E6A23C; }
    &.danger { color: #F56C6C; }
    &.info { color: #909399; }
  }
  .status-label {
    color: #909399;
    font-size: 14px;
  }
  .system-metrics {
    flex: 1;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    padding-left: 40px;
  }
  .metric-item {
    display: flex;
    align-items: center;
    .metric-icon {
      font-size: 24px;
      color: #409EFF;
      margin-right: 10px;
    }
    .metric-info {
      .metric-value {
        font-size: 20px;
        font-weight: bold;
        color: #303133;
      }
      .metric-label {
        font-size: 12px;
        color: #909399;
      }
    }
  }
}

.resource-row {
  margin-bottom: 20px;
}

.resource-card {
  height: 100%;
  .resource-content {
    text-align: center;
    padding: 15px 0;
  }
  .resource-value {
    font-size: 36px;
    font-weight: bold;
    color: #409EFF;
    margin-bottom: 10px;
  }
  .resource-label {
    font-size: 14px;
    color: #909399;
    margin-bottom: 15px;
  }
  .resource-detail {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    padding: 0 10px;
    .detail-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      .label {
        color: #909399;
        font-size: 12px;
      }
      .value {
        font-size: 14px;
        font-weight: bold;
        &.success { color: #67C23A; }
        &.warning { color: #E6A23C; }
        &.danger { color: #F56C6C; }
      }
    }
  }
}

.task-card {
  margin-bottom: 20px;
  .task-content {
    padding: 20px;
  }
  .task-overview {
    display: flex;
    justify-content: space-around;
    margin-bottom: 20px;
    padding-bottom: 20px;
    border-bottom: 1px solid #EBEEF5;
    .overview-item {
      text-align: center;
      .overview-value {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 5px;
        &.success { color: #67C23A; }
        &.warning { color: #E6A23C; }
        &.danger { color: #F56C6C; }
      }
      .overview-label {
        font-size: 12px;
        color: #909399;
      }
    }
  }
}

.notification-card {
  .el-timeline {
    padding: 20px;
    max-height: 300px;
    overflow-y: auto;
  }
}

:deep(.el-timeline-item__content) {
  color: #606266;
}

:deep(.el-timeline-item__timestamp) {
  color: #909399;
  font-size: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style> 