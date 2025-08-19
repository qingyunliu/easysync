<template>
  <div class="dashboard-container">
    <!-- 系统状态卡片 -->
    <el-card class="system-card">
      <template #header>
        <div class="card-header">
          <span>{{ $t('dashboard.systemStatus') }}</span>
        </div>
      </template>
      <div class="system-content">
        <div class="system-status">
          <div class="status-value" :class="getSystemStatusClass(stats.system.systemStatus)">
            {{ stats.system.systemStatus }}
          </div>
          <div class="status-label">{{ $t('dashboard.currentSystemStatus') }}</div>
        </div>
        <div class="system-metrics">
          <div class="metric-item">
            <div class="metric-icon">
              <el-icon>
                <Cpu />
              </el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-value">{{ stats.system.cpuUsage }}%</div>
              <div class="metric-label">{{ $t('dashboard.cpuUsage') }}</div>
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-icon">
              <el-icon>
                <Memory />
              </el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-value">{{ stats.system.memoryUsage }}%</div>
              <div class="metric-label">{{ $t('dashboard.memoryUsage') }}</div>
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-icon">
              <el-icon>
                <Monitor />
              </el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-value">{{ stats.system.diskUsage }}%</div>
              <div class="metric-label">{{ $t('dashboard.diskUsage') }}</div>
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-icon">
              <el-icon>
                <Connection />
              </el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-value">{{ formatSize(stats.system.networkTraffic) }}/s</div>
              <div class="metric-label">{{ $t('dashboard.networkTraffic') }}</div>
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
              <span>{{ $t('dashboard.clients') }}</span>
              <el-button type="text" @click="$router.push('/clients')">{{ $t('dashboard.viewAll') }}</el-button>
            </div>
          </template>
          <div class="resource-content">
            <div class="resource-value">{{ stats.clients.clientCount }}</div>
            <div class="resource-label">{{ $t('dashboard.configuredClients') }}</div>
            <div class="resource-detail">
              <div class="detail-item">
                <span class="label">{{ $t('dashboard.online') }}:</span>
                <span class="value success">{{ stats.clients.onlineClients }}</span>
              </div>
              <div class="detail-item">
                <span class="label">{{ $t('dashboard.offline') }}:</span>
                <span class="value warning">{{ stats.clients.offlineClients }}</span>
              </div>
              <div class="detail-item">
                <span class="label">{{ $t('dashboard.installed') }}:</span>
                <span class="value">{{ stats.clients.installedAgents }}</span>
              </div>
              <div class="detail-item">
                <span class="label">{{ $t('dashboard.uninstalled') }}:</span>
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
              <span>{{ $t('dashboard.nodes') }}</span>
              <el-button type="text" @click="$router.push('/nodes')">{{ $t('dashboard.viewAll') }}</el-button>
            </div>
          </template>
          <div class="resource-content">
            <div class="resource-value">{{ stats.nodes.nodeCount }}</div>
            <div class="resource-label">{{ $t('dashboard.configuredNodes') }}</div>
            <div class="resource-detail">
              <div class="detail-item">
                <span class="label">{{ $t('dashboard.online') }}:</span>
                <span class="value success">{{ stats.nodes.onlineNodes }}</span>
              </div>
              <div class="detail-item">
                <span class="label">{{ $t('dashboard.offline') }}:</span>
                <span class="value warning">{{ stats.nodes.offlineNodes }}</span>
              </div>
              <div class="detail-item">
                <span class="label">{{ $t('dashboard.proxyInstalled') }}:</span>
                <span class="value">{{ stats.nodes.installedNodes }}</span>
              </div>
              <div class="detail-item">
                <span class="label">{{ $t('dashboard.proxyUninstalled') }}:</span>
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
              <span>{{ $t('dashboard.storages') }}</span>
              <el-button type="text" @click="$router.push('/storages')">{{ $t('dashboard.viewAll') }}</el-button>
            </div>
          </template>
          <div class="resource-content">
            <div class="resource-value">{{ stats.storages.storageCount }}</div>
            <div class="resource-label">{{ $t('dashboard.configuredStorages') }}</div>
            <div class="resource-detail">
              <div class="detail-item">
                <span class="label">{{ $t('dashboard.mounted') }}:</span>
                <span class="value success">{{ stats.storages.mountedCount }}</span>
              </div>
              <div class="detail-item">
                <span class="label">{{ $t('dashboard.unmounted') }}:</span>
                <span class="value warning">{{ stats.storages.unmountedCount }}</span>
              </div>
              <div class="detail-item">
                <span class="label">{{ $t('dashboard.totalCapacity') }}:</span>
                <span class="value">{{ formatSize(stats.storages.totalStorageSize) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">{{ $t('dashboard.usedCapacity') }}:</span>
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
          <span>{{ $t('dashboard.tasks') }}</span>
          <el-button type="text" @click="$router.push('/tasks')">{{ $t('dashboard.viewAll') }}</el-button>
        </div>
      </template>
      <div class="task-content">
        <div class="task-overview">
          <div class="overview-item">
            <div class="overview-value">{{ stats.tasks.taskCount }}</div>
            <div class="overview-label">{{ $t('dashboard.totalTasks') }}</div>
          </div>
          <div class="overview-item">
            <div class="overview-value success">{{ stats.tasks.runningCount }}</div>
            <div class="overview-label">{{ $t('dashboard.running') }}</div>
          </div>
          <div class="overview-item">
            <div class="overview-value">{{ stats.tasks.stoppedCount }}</div>
            <div class="overview-label">{{ $t('dashboard.stopped') }}</div>
          </div>
          <div class="overview-item">
            <div class="overview-value">{{ stats.tasks.todaySyncCount }}</div>
            <div class="overview-label">{{ $t('dashboard.todaySync') }}</div>
          </div>
          <div class="overview-item">
            <div class="overview-value" :class="getSuccessRateClass(calculateSuccessRate())">
              {{ calculateSuccessRate() }}%
            </div>
            <div class="overview-label">{{ $t('dashboard.successRate') }}</div>
          </div>
        </div>
        <div class="task-detail">
          <el-table :data="recentTasks" style="width: 100%" :max-height="300">
            <el-table-column prop="name" :label="$t('dashboard.taskName')" min-width="150" />
            <el-table-column prop="status" :label="$t('dashboard.status')" width="100">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">
                  {{ getStatusText(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="start_time" :label="$t('dashboard.startTime')" width="180">
              <template #default="scope">
                {{ formatDateTime(scope.row.start_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="end_time" :label="$t('dashboard.endTime')" width="180">
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
            <el-icon class="header-icon">
              <Bell />
            </el-icon>
            <span class="header-title">{{ $t('dashboard.systemNotifications') }}</span>
            <el-badge v-if="unreadNotificationCount > 0" :value="unreadNotificationCount" class="notification-badge" />
          </div>
          <div class="header-actions">
            <el-button type="text" @click="markAllAsRead" v-if="unreadNotificationCount > 0" size="small">
              {{ $t('dashboard.markAllAsRead') }}
            </el-button>
            <el-button type="text" @click="$router.push('/notifications')" size="small">
              {{ $t('dashboard.viewAll') }}
            </el-button>
          </div>
        </div>
      </template>

      <div class="notification-content">
        <div v-if="recentNotifications.length === 0" class="empty-notifications">
          <el-icon class="empty-icon">
            <ChatDotSquare />
          </el-icon>
          <p class="empty-text">{{ $t('dashboard.noNotifications') }}</p>
          <p class="empty-desc">{{ $t('dashboard.systemMessagesWillShowHere') }}</p>
        </div>

        <div v-else class="notification-list">
          <div v-for="(notification, index) in recentNotifications" :key="notification.id || index"
            class="notification-item" :class="{ 'unread': !notification.is_read }"
            @click="handleNotificationClick(notification)">
            <div class="notification-icon">
              <el-icon :class="getNotificationIconClass(notification.type)"
                :style="{ color: getNotificationColor(notification.level) }">
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
                <el-tag :type="getNotificationTagType(notification.level)" size="small">
                  {{ getNotificationLevelText(notification.level) }}
                </el-tag>
                <span class="notification-type">{{ getNotificationTypeText(notification.type) }}</span>
              </div>
            </div>

            <div class="notification-actions">
              <el-button v-if="!notification.is_read" type="text" size="small" @click.stop="markAsRead(notification.id)"
                class="mark-read-btn">
                {{ $t('dashboard.markAsRead') }}
              </el-button>
              <el-dropdown @command="handleNotificationAction" trigger="click">
                <el-button type="text" size="small">
                  <el-icon>
                    <MoreFilled />
                  </el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="{ action: 'delete', id: notification.id }">
                      {{ $t('dashboard.deleteNotification') }}
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </div>

        <div v-if="recentNotifications.length > 0" class="notification-footer">
          <el-button type="text" @click="loadMoreNotifications" :loading="loadingMore" class="load-more-btn">
            {{ $t('dashboard.loadMore') }}
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
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

const { t } = useI18n()

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
    ElMessage.error(t('dashboard.fetchDataFailed'))
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
      return t('dashboard.success')
    case 'failed':
      return t('dashboard.failed')
    case 'running':
      return t('dashboard.running')
    default:
      return t('dashboard.unknown')
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

  if (diffMins < 1) return t('dashboard.justNow')
  if (diffMins < 60) return `${diffMins} ${t('dashboard.minutesAgo')}`
  if (diffHours < 24) return `${diffHours} ${t('dashboard.hoursAgo')}`
  if (diffDays < 7) return `${diffDays} ${t('dashboard.daysAgo')}`
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
    'info': t('dashboard.info'),
    'success': t('dashboard.success'),
    'warning': t('dashboard.warning'),
    'error': t('dashboard.error'),
    'critical': t('dashboard.critical')
  }
  return textMap[level] || t('dashboard.info')
}

const getNotificationTypeText = (type) => {
  const textMap = {
    'task_completed': t('dashboard.taskCompleted'),
    'task_failed': t('dashboard.taskFailed'),
    'task_started': t('dashboard.taskStarted'),
    'system_error': t('dashboard.systemError'),
    'storage_mounted': t('dashboard.storageMounted'),
    'storage_unmounted': t('dashboard.storageUnmounted')
  }
  return textMap[type] || t('dashboard.systemNotification')
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
    ElMessage.success(t('dashboard.markAsReadSuccess'))
  } catch (error) {
    ElMessage.error(t('dashboard.markAsReadFailed'))
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

    ElMessage.success(t('dashboard.markAllAsReadSuccess'))
  } catch (error) {
    ElMessage.error(t('dashboard.markAllAsReadFailed'))
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
      ElMessage.success(t('dashboard.deleteSuccess'))
    } catch (error) {
      ElMessage.error(t('dashboard.deleteFailed'))
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

    const newNotifications = response.data.filter(newNotification =>
      !recentNotifications.value.some(existingNotification =>
        existingNotification.id === newNotification.id
      )
    )

    if (newNotifications.length > 0) {
      recentNotifications.value.push(...newNotifications)
    }

    if (newNotifications.length === 0) {
      ElMessage.info(t('dashboard.allNotificationsLoaded'))
    }
  } catch (error) {
    ElMessage.error(t('dashboard.loadMoreFailed'))
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
    case t('dashboard.statuses.normal'):
      return 'success'
    case t('dashboard.statuses.attention'):
      return 'warning'
    case t('dashboard.statuses.warning'):
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

    &.success {
      color: #67C23A;
    }

    &.warning {
      color: #E6A23C;
    }

    &.danger {
      color: #F56C6C;
    }

    &.info {
      color: var(--text-secondary);
    }
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

        &.success {
          color: #67C23A;
        }

        &.warning {
          color: #E6A23C;
        }

        &.danger {
          color: #F56C6C;
        }
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

        &.success {
          color: #67C23A;
        }

        &.warning {
          color: #E6A23C;
        }

        &.danger {
          color: #F56C6C;
        }
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