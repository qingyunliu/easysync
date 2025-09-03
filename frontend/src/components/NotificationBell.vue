<template>
  <div class="notification-bell">
    <el-popover placement="bottom-end" :width="360" trigger="click" popper-class="notification-popover" @show="onShow">
      <template #reference>
        <div class="bell-container" @click="handleBellClick">
          <el-icon class="bell-icon" :class="{ shake: hasUnread }">
            <Bell />
          </el-icon>
          <el-badge v-if="unreadCount > 0" :value="unreadCount > 99 ? '99+' : unreadCount" class="notification-badge" />
        </div>
      </template>

      <div class="notification-dropdown">
        <div class="notification-header">
          <div class="header-left">
            <h4 class="header-title">{{ $t('notifications.title') }}</h4>
            <span class="unread-count" v-if="unreadCount > 0">({{ unreadCount }}{{ $t('notifications.unreadCount')
            }})</span>
          </div>
          <div class="header-actions">
            <el-button type="text" size="small" @click="markAllAsRead" v-if="unreadCount > 0">
              {{ $t('notifications.markAllRead') }}
            </el-button>
          </div>
        </div>

        <el-divider style="margin: 12px 0;" />

        <div class="notification-list" v-loading="loading">
          <div v-if="notifications.length === 0" class="empty-state">
            <el-icon class="empty-icon">
              <ChatDotSquare />
            </el-icon>
            <p class="empty-text">{{ $t('notifications.noNotifications') }}</p>
          </div>

          <div v-else class="notification-items">
            <div v-for="notification in notifications" :key="notification.id" class="notification-item"
              :class="{ unread: !notification.is_read }" @click="handleNotificationClick(notification)">
              <div class="item-icon">
                <el-icon :style="{ color: getNotificationColor(notification.level) }">
                  <component :is="getNotificationIcon(notification.type)" />
                </el-icon>
              </div>

              <div class="item-content">
                <div class="item-title">{{ notification.title }}</div>
                <div class="item-message">{{ notification.content || notification.message }}</div>
                <div class="item-meta">
                  <span class="item-time">{{ formatRelativeTime(notification.created_at) }}</span>
                  <el-tag :type="getNotificationTagType(notification.level)" size="small">
                    {{ getNotificationLevelText(notification.level) }}
                  </el-tag>
                </div>
              </div>

              <div class="item-actions">
                <el-button v-if="!notification.is_read" type="text" size="small"
                  @click.stop="markAsRead(notification.id)">
                  <el-icon>
                    <Check />
                  </el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <el-divider style="margin: 12px 0;" />

        <div class="notification-footer">
          <el-button type="text" size="small" @click="viewAll" class="view-all-btn">
            {{ $t('notifications.viewAll') }}
          </el-button>
        </div>
      </div>
    </el-popover>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import {
  Bell,
  ChatDotSquare,
  Check,
  Warning,
  InfoFilled,
  CircleCheck,
  CircleClose,
  Notification
} from '@element-plus/icons-vue'
import axios from 'axios'

const { t } = useI18n()
const router = useRouter()
const loading = ref(false)
const notifications = ref([])

// 计算属性
const unreadCount = computed(() => {
  return notifications.value.filter(n => !n.is_read).length
})

const hasUnread = computed(() => {
  return unreadCount.value > 0
})

// 获取通知图标
const getNotificationIcon = (type) => {
  const iconMap = {
    'info': InfoFilled,
    'success': CircleCheck,
    'warning': Warning,
    'error': CircleClose,
    'critical': CircleClose,
    'default': Notification
  }
  return iconMap[type] || iconMap.default
}

// 获取通知颜色
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

// 获取标签类型
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

// 获取等级文本
const getNotificationLevelText = (level) => {
  const levelMap = {
    'info': t('notifications.levels.info'),
    'success': t('notifications.levels.success'),
    'warning': t('notifications.levels.warning'),
    'error': t('notifications.levels.error'),
    'critical': t('notifications.levels.critical')
  }
  return levelMap[level] || t('notifications.levels.info')
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

  if (diffMins < 1) return t('notifications.time.justNow')
  if (diffMins < 60) return t('notifications.time.minutesAgo', { minutes: diffMins })
  if (diffHours < 24) return t('notifications.time.hoursAgo', { hours: diffHours })
  if (diffDays < 7) return t('notifications.time.daysAgo', { days: diffDays })
  return date.toLocaleDateString()
}

// 获取通知列表
const fetchNotifications = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/notifications/list', {
      params: { limit: 10 }
    })
    notifications.value = response.data.data || []
  } catch (error) {
    console.error('获取通知失败:', error)
  } finally {
    loading.value = false
  }
}

// 事件处理
const onShow = () => {
  fetchNotifications()
}

const handleBellClick = () => {
  // 点击铃铛的处理逻辑
}

const handleNotificationClick = async (notification) => {
  if (!notification.is_read) {
    await markAsRead(notification.id)
  }
  // 可以添加跳转到相关页面的逻辑
}

const markAsRead = async (notificationId) => {
  try {
    await axios.post(`/api/notifications/${notificationId}/read`)
    const notification = notifications.value.find(n => n.id === notificationId)
    if (notification) {
      notification.is_read = true
    }
  } catch (error) {
    ElMessage.error(t('notifications.markReadFailed'))
  }
}

const markAllAsRead = async () => {
  try {
    const unreadIds = notifications.value
      .filter(n => !n.is_read)
      .map(n => n.id)

    await Promise.all(unreadIds.map(id => axios.post(`/api/notifications/${id}/read`)))

    notifications.value.forEach(n => {
      n.is_read = true
    })

    ElMessage.success(t('notifications.markAllReadSuccess'))
  } catch (error) {
    ElMessage.error(t('notifications.markReadFailed'))
  }
}

const viewAll = () => {
  router.push('/notifications')
}

// 组件挂载时获取通知
onMounted(() => {
  fetchNotifications()
})
</script>

<style scoped>
.notification-bell {
  position: relative;
}

.bell-container {
  position: relative;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.bell-container:hover {
  background: #f5f7fa;
}

.bell-icon {
  font-size: 18px;
  color: #606266;
  transition: all 0.2s ease;
}

.bell-icon.shake {
  animation: shake 2s infinite;
  color: #409eff;
}

.notification-badge {
  position: absolute;
  top: 0;
  right: 0;
}

@keyframes shake {

  0%,
  50%,
  100% {
    transform: rotate(0deg);
  }

  10%,
  30% {
    transform: rotate(-8deg);
  }

  20%,
  40% {
    transform: rotate(8deg);
  }
}

.notification-dropdown {
  padding: 0;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f5f7fa;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.unread-count {
  font-size: 12px;
  color: #f56c6c;
  font-weight: 500;
}

.notification-list {
  max-height: 300px;
  overflow-y: auto;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 32px;
  color: #c0c4cc;
  margin-bottom: 12px;
}

.empty-text {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

.notification-items {
  padding: 0;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  position: relative;
  border-bottom: 1px solid #f8f9fa;
}

.notification-item:hover {
  background: #f8f9fa;
}

.notification-item.unread {
  background: #f0f9ff;

  &::before {
    content: '';
    position: absolute;
    left: 4px;
    top: 18px;
    width: 4px;
    height: 4px;
    background: #409eff;
    border-radius: 50%;
  }
}

.notification-item:last-child {
  border-bottom: none;
}

.item-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #f5f7fa;
  flex-shrink: 0;
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-message {
  font-size: 12px;
  color: #606266;
  margin-bottom: 6px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.item-time {
  font-size: 11px;
  color: #909399;
}

.item-actions {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.notification-item:hover .item-actions {
  opacity: 1;
}

.notification-footer {
  padding: 12px 16px;
  text-align: center;
  border-top: 1px solid #f5f7fa;
}

.view-all-btn {
  color: #409eff;
  font-size: 12px;
}

.view-all-btn:hover {
  color: #66b1ff;
}
</style>

<style>
.notification-popover {
  padding: 0 !important;
  border-radius: 8px !important;
  border: 1px solid #ebeef5 !important;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1) !important;
}
</style>