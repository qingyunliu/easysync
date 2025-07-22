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
    <el-card class="notification-card modern-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><Bell /></el-icon>
            <span class="header-title">系统通知</span>
            <el-badge 
              v-if="unreadNotificationCount > 0" 
              :value="unreadNotificationCount" 
              class="notification-badge"
            />
          </div>
          <div class="header-actions">
            <el-button 
              type="text" 
              @click="markAllAsRead" 
              v-if="unreadNotificationCount > 0"
              size="small"
            >
              全部已读
            </el-button>
            <el-button 
              type="text" 
              @click="$router.push('/notifications')" 
              size="small"
            >
              查看全部
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="notification-content">
        <div v-if="recentNotifications.length === 0" class="empty-notifications">
          <el-icon class="empty-icon"><ChatDotSquare /></el-icon>
          <p class="empty-text">暂无通知消息</p>
          <p class="empty-desc">系统消息将在此处显示</p>
        </div>
        
        <div v-else class="notification-list">
          <div
            v-for="(notification, index) in recentNotifications"
            :key="index"
            class="notification-item"
            :class="{ 'unread': !notification.is_read }"
            @click="handleNotificationClick(notification)"
          >
            <div class="notification-icon">
              <el-icon 
                :class="getNotificationIconClass(notification.type)"
                :style="{ color: getNotificationColor(notification.level) }"
              >
                <component :is="getNotificationIcon(notification.type)" />
              </el-icon>
            </div>
            
            <div class="notification-body">
              <div class="notification-header">
                <h4 class="notification-title">{{ notification.title }}</h4>
                <span class="notification-time">{{ formatRelativeTime(notification.created_at) }}</span>
              </div>
              <p class="notification-message">{{ notification.content || notification.message }}</p>
              <div class="notification-meta">
                <el-tag 
                  :type="getNotificationTagType(notification.level)" 
                  size="small"
                >
                  {{ getNotificationLevelText(notification.level) }}
                </el-tag>
                <span class="notification-type">{{ getNotificationTypeText(notification.type) }}</span>
              </div>
            </div>
            
            <div class="notification-actions">
              <el-button 
                v-if="!notification.is_read"
                type="text" 
                size="small" 
                @click.stop="markAsRead(notification.id)"
                class="mark-read-btn"
              >
                标记已读
              </el-button>
              <el-dropdown @command="handleNotificationAction" trigger="click">
                <el-button type="text" size="small">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="{ action: 'delete', id: notification.id }">
                      删除通知
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </div>
        
        <div v-if="recentNotifications.length > 0" class="notification-footer">
          <el-button 
            type="text" 
            @click="loadMoreNotifications" 
            :loading="loadingMore"
            class="load-more-btn"
          >
            加载更多
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Cpu,
  Monitor,
  Connection,
  Bell,
  ChatDotSquare,
  MoreFilled,
  Warning,
  InfoFilled,
  CircleCheck,
  CircleClose,
  Notification
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
const loadingMore = ref(false)

// 计算属性
const unreadNotificationCount = computed(() => {
  return recentNotifications.value.filter(n => !n.is_read).length
})

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

// 格式化相对时间
const formatRelativeTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  return formatDateTime(dateStr)
}

// 通知相关方法
const getNotificationIcon = (type) => {
  const iconMap = {
    'task_completed': CircleCheck,
    'task_failed': CircleClose,
    'task_started': Notification,
    'system_error': Warning,
    'storage_mounted': InfoFilled,
    'storage_unmounted': Warning,
    default: InfoFilled
  }
  return iconMap[type] || iconMap.default
}

const getNotificationIconClass = (type) => {
  return `notification-icon-${type}`
}

const getNotificationColor = (level) => {
  const colorMap = {
    'info': '#409eff',
    'success': '#67c23a',
    'warning': '#e6a23c',
    'error': '#f56c6c',
    'critical': '#f56c6c'
  }
  return colorMap[level] || colorMap.info
}

const getNotificationTagType = (level) => {
  const typeMap = {
    'info': '',
    'success': 'success',
    'warning': 'warning',
    'error': 'danger',
    'critical': 'danger'
  }
  return typeMap[level] || ''
}

const getNotificationLevelText = (level) => {
  const textMap = {
    'info': '信息',
    'success': '成功',
    'warning': '警告',
    'error': '错误',
    'critical': '严重'
  }
  return textMap[level] || '信息'
}

const getNotificationTypeText = (type) => {
  const textMap = {
    'task_completed': '任务完成',
    'task_failed': '任务失败',
    'task_started': '任务开始',
    'system_error': '系统错误',
    'storage_mounted': '存储挂载',
    'storage_unmounted': '存储卸载'
  }
  return textMap[type] || '系统通知'
}

// 通知操作方法
const handleNotificationClick = async (notification) => {
  if (!notification.is_read) {
    await markAsRead(notification.id)
  }
}

const markAsRead = async (notificationId) => {
  try {
    await axios.post(`/api/notifications/${notificationId}/read`)
    const notification = recentNotifications.value.find(n => n.id === notificationId)
    if (notification) {
      notification.is_read = true
    }
    ElMessage.success('标记已读成功')
  } catch (error) {
    ElMessage.error('标记已读失败')
  }
}

const markAllAsRead = async () => {
  try {
    const unreadIds = recentNotifications.value
      .filter(n => !n.is_read)
      .map(n => n.id)
    
    await Promise.all(unreadIds.map(id => axios.post(`/api/notifications/${id}/read`)))
    
    recentNotifications.value.forEach(n => {
      n.is_read = true
    })
    
    ElMessage.success('全部标记已读成功')
  } catch (error) {
    ElMessage.error('标记已读失败')
  }
}

const handleNotificationAction = async ({ action, id }) => {
  if (action === 'delete') {
    try {
      await axios.delete(`/api/notifications/${id}`)
      const index = recentNotifications.value.findIndex(n => n.id === id)
      if (index > -1) {
        recentNotifications.value.splice(index, 1)
      }
      ElMessage.success('删除成功')
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }
}

const loadMoreNotifications = async () => {
  loadingMore.value = true
  try {
    const response = await axios.get('/api/notifications/list', {
      params: {
        offset: recentNotifications.value.length,
        limit: 10
      }
    })
    recentNotifications.value.push(...response.data.data)
  } catch (error) {
    ElMessage.error('加载更多失败')
  } finally {
    loadingMore.value = false
  }
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
  background: var(--bg-color);
  color: var(--text-color);
}

.system-card,
.resource-card,
.task-card,
.notification-card {
  transition: all 0.2s ease;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--card-bg);
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0;
  }
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .header-icon {
    color: #409eff;
    font-size: 16px;
  }
  
  .header-title {
    font-weight: 600;
    color: var(--text-color);
    font-size: 14px;
  }
  
  .notification-badge {
    margin-left: 8px;
  }
  
  .header-actions {
    display: flex;
    gap: 8px;
  }
  
  .notification-content {
    min-height: 180px;
    max-height: 350px;
    overflow-y: auto;
  }
  
  .empty-notifications {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    text-align: center;
  }
  
  .empty-icon {
    font-size: 40px;
    color: #c0c4cc;
    margin-bottom: 12px;
  }
  
  .empty-text {
    margin: 0 0 4px 0;
    font-size: 14px;
    color: var(--text-secondary);
    font-weight: 500;
  }
  
  .empty-desc {
    margin: 0;
    font-size: 12px;
    color: #c0c4cc;
  }
  
  .notification-list {
    padding: 0;
  }
  
  .notification-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 16px;
    border-bottom: 1px solid var(--border-lighter);
    cursor: pointer;
    transition: background-color 0.2s ease;
    position: relative;
    
    &:hover {
      background: var(--bg-secondary);
    }
    
    &.unread {
      background: var(--bg-secondary);
      border-left: 3px solid #409eff;
      
      &::before {
        content: '';
        position: absolute;
        left: 8px;
        top: 20px;
        width: 6px;
        height: 6px;
        background: #409eff;
        border-radius: 50%;
      }
    }
    
    &:last-child {
      border-bottom: none;
    }
  }
  
  .notification-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: var(--bg-color);
    flex-shrink: 0;
    
    .el-icon {
      font-size: 16px;
    }
  }
  
  .notification-body {
    flex: 1;
    min-width: 0;
  }
  
  .notification-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 6px;
  }
  
  .notification-title {
    margin: 0;
    font-size: 13px;
    font-weight: 600;
    color: var(--text-color);
    line-height: 1.4;
  }
  
  .notification-time {
    font-size: 11px;
    color: var(--text-secondary);
    white-space: nowrap;
    margin-left: 12px;
  }
  
  .notification-message {
    margin: 0 0 8px 0;
    font-size: 12px;
    color: var(--text-secondary);
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  
  .notification-meta {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .notification-type {
    font-size: 11px;
    color: var(--text-secondary);
  }
  
  .notification-actions {
    display: flex;
    flex-direction: column;
    gap: 4px;
    opacity: 0;
    transition: opacity 0.2s ease;
  }
  
  .notification-item:hover .notification-actions {
    opacity: 1;
  }
  
  .mark-read-btn {
    font-size: 11px;
    padding: 2px 6px;
    height: auto;
  }
  
  .notification-footer {
    padding: 12px 16px;
    text-align: center;
    border-top: 1px solid var(--border-lighter);
  }
  
  .load-more-btn {
    color: #409eff;
    font-size: 12px;
    
    &:hover {
      color: #66b1ff;
    }
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
    border-right: 1px solid var(--border-color);
  }
  .status-value {
    font-size: 36px;
    font-weight: bold;
    margin-bottom: 10px;
    &.success { color: #67C23A; }
    &.warning { color: #E6A23C; }
    &.danger { color: #F56C6C; }
    &.info { color: var(--text-secondary); }
  }
  .status-label {
    color: var(--text-secondary);
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
        color: var(--text-color);
      }
      .metric-label {
        font-size: 12px;
        color: var(--text-secondary);
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
    color: var(--text-secondary);
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
        color: var(--text-secondary);
        font-size: 12px;
      }
      .value {
        font-size: 14px;
        font-weight: bold;
        color: var(--text-color);
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
    border-bottom: 1px solid var(--border-color);
    .overview-item {
      text-align: center;
      .overview-value {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 5px;
        color: var(--text-color);
        &.success { color: #67C23A; }
        &.warning { color: #E6A23C; }
        &.danger { color: #F56C6C; }
      }
      .overview-label {
        font-size: 12px;
        color: var(--text-secondary);
      }
    }
  }
}


:deep(.el-timeline-item__content) {
  color: var(--text-secondary);
}

:deep(.el-timeline-item__timestamp) {
  color: var(--text-secondary);
  font-size: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style> 