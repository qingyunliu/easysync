<template>
  <div class="notifications-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1>消息通知</h1>
        <p class="page-description">管理和查看系统通知消息，控制通知的接收和展示</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="markAllAsRead" :disabled="!hasUnreadNotifications">
          <el-icon><Check /></el-icon>
          全部已读
        </el-button>
        <el-button @click="clearAllNotifications" :disabled="notifications.length === 0">
          <el-icon><Delete /></el-icon>
          清空消息
        </el-button>
      </div>
    </div>
    
    <!-- 统计面板 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content stat-flex">
            <div class="stat-icon total">
              <el-icon><ChatDotRound /></el-icon>
            </div>
            <div>
              <div class="stat-number">{{ stats.total || 0 }}</div>
              <div class="stat-label">总消息数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card unread">
          <div class="stat-content stat-flex">
            <div class="stat-icon unread">
              <el-icon><ChatDotRound /></el-icon>
            </div>
            <div>
              <div class="stat-number">{{ stats.unread || 0 }}</div>
              <div class="stat-label">未读消息</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card info">
          <div class="stat-content stat-flex">
            <div class="stat-icon info">
              <el-icon><InfoFilled /></el-icon>
            </div>
            <div>
              <div class="stat-number">{{ stats.info || 0 }}</div>
              <div class="stat-label">信息类型</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card warning">
          <div class="stat-content stat-flex">
            <div class="stat-icon warning">
              <el-icon><WarningFilled /></el-icon>
            </div>
            <div>
              <div class="stat-number">{{ stats.warning || 0 }}</div>
              <div class="stat-label">警告/错误</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 过滤器 -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-container">
        <div class="filter-left">
          <el-select v-model="filters.level" placeholder="消息级别" style="width: 120px" @change="handleFilterChange">
            <el-option label="全部" value="" />
            <el-option label="信息" value="info" />
            <el-option label="警告" value="warning" />
            <el-option label="错误" value="error" />
            <el-option label="成功" value="success" />
          </el-select>
          
          <el-select v-model="filters.status" placeholder="阅读状态" style="width: 120px" @change="handleFilterChange">
            <el-option label="全部" value="" />
            <el-option label="未读" value="unread" />
            <el-option label="已读" value="read" />
          </el-select>
          
          <el-select v-model="filters.type" placeholder="消息类型" style="width: 140px" @change="handleFilterChange">
            <el-option label="全部" value="" />
            <el-option label="系统通知" value="system" />
            <el-option label="任务通知" value="task" />
            <el-option label="存储通知" value="storage" />
            <el-option label="用户通知" value="user" />
          </el-select>
        </div>
        
        <div class="filter-right">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索通知内容"
            style="width: 250px"
            @input="handleSearch"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button @click="refreshNotifications" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 通知列表 -->
    <el-card class="notifications-card">
      <div v-loading="loading" class="notifications-container">
        <div v-if="filteredNotifications.length === 0" class="empty-state">
          <el-empty description="暂无通知消息">
            <el-button type="primary" @click="refreshNotifications">刷新页面</el-button>
          </el-empty>
        </div>
        
        <div v-else class="notifications-list">
          <div 
            v-for="notification in paginatedNotifications" 
            :key="notification.id"
            :class="['notification-item', { 'unread': !notification.is_read }]"
            @click="handleNotificationClick(notification)"
          >
            <div class="notification-content">
              <div class="notification-header">
                <div class="notification-left">
                  <el-icon :class="['level-icon', notification.level]">
                    <component :is="getLevelIcon(notification.level)" />
                  </el-icon>
                  <span class="notification-title">{{ notification.title }}</span>
                  <el-tag 
                    :type="getTypeTagType(notification.type)" 
                    size="small"
                    class="notification-type-tag"
                  >
                    {{ getTypeLabel(notification.type) }}
                  </el-tag>
                </div>
                <div class="notification-right">
                  <span class="notification-time">{{ formatTime(notification.created_at) }}</span>
                  <el-dropdown @command="(cmd) => handleNotificationAction(cmd, notification)" trigger="click">
                    <el-button type="text" size="small">
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item :command="notification.is_read ? 'mark-unread' : 'mark-read'">
                          <el-icon><Check /></el-icon>
                          {{ notification.is_read ? '标为未读' : '标为已读' }}
                        </el-dropdown-item>
                        <el-dropdown-item command="delete" divided>
                          <el-icon><Delete /></el-icon>
                          删除
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
              
              <div class="notification-body">
                <p class="notification-text">{{ notification.content }}</p>
              </div>
            </div>
            
            <div v-if="!notification.is_read" class="unread-indicator"></div>
          </div>
        </div>
        
        <!-- 分页 -->
        <div v-if="filteredNotifications.length > 0" class="pagination">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="filteredNotifications.length"
            layout="total, sizes, prev, pager, next"
            @size-change="handlePageSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </el-card>

    <!-- 通知详情弹窗 -->
    <el-dialog 
      v-model="detailDialog.visible" 
      :title="detailDialog.notification?.title || '通知详情'"
      width="600px"
      @open="handleDetailDialogOpen"
    >
      <div v-if="detailDialog.notification" class="notification-detail">
        <div class="detail-header">
          <div class="detail-level">
            <el-icon :class="['level-icon', detailDialog.notification.level]">
              <component :is="getLevelIcon(detailDialog.notification.level)" />
            </el-icon>
            <span>{{ getLevelLabel(detailDialog.notification.level) }}</span>
          </div>
          <el-tag :type="getTypeTagType(detailDialog.notification.type)" size="small">
            {{ getTypeLabel(detailDialog.notification.type) }}
          </el-tag>
        </div>
        
        <div class="detail-content">
          <p>{{ detailDialog.notification.content }}</p>
        </div>
        
        <div class="detail-meta">
          <div class="meta-item">
            <span class="meta-label">创建时间：</span>
            <span>{{ formatTime(detailDialog.notification.created_at) }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">阅读状态：</span>
            <el-tag :type="detailDialog.notification.is_read ? 'success' : 'warning'" size="small">
              {{ detailDialog.notification.is_read ? '已读' : '未读' }}
            </el-tag>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="detailDialog.visible = false">关闭</el-button>
        <el-button 
          v-if="!detailDialog.notification?.is_read" 
          type="primary" 
          @click="markAsReadFromDetail"
        >
          标记已读
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Bell,
  Check,
  Delete,
  ChatDotRound,
  InfoFilled,
  WarningFilled,
  Search,
  Refresh,
  MoreFilled,
  CircleCheckFilled,
  CircleCloseFilled,
  QuestionFilled
} from '@element-plus/icons-vue'
import axios from 'axios'

// 响应式数据
const loading = ref(false)
const notifications = ref([])
const currentPage = ref(1)
const pageSize = ref(10)

// 过滤器
const filters = reactive({
  level: '',
  status: '',
  type: '',
  keyword: ''
})

// 详情弹窗
const detailDialog = reactive({
  visible: false,
  notification: null
})

// 统计数据
const stats = computed(() => {
  const total = notifications.value.length
  const unread = notifications.value.filter(n => !n.is_read).length
  const info = notifications.value.filter(n => n.level === 'info').length
  const warning = notifications.value.filter(n => ['warning', 'error'].includes(n.level)).length
  
  return { total, unread, info, warning }
})

// 是否有未读消息
const hasUnreadNotifications = computed(() => {
  return notifications.value.some(n => !n.is_read)
})

// 过滤后的通知
const filteredNotifications = computed(() => {
  let result = notifications.value

  // 按级别过滤
  if (filters.level) {
    result = result.filter(n => n.level === filters.level)
  }

  // 按状态过滤
  if (filters.status) {
    const isRead = filters.status === 'read'
    result = result.filter(n => n.is_read === isRead)
  }

  // 按类型过滤
  if (filters.type) {
    result = result.filter(n => n.type === filters.type)
  }

  // 按关键词过滤
  if (filters.keyword) {
    const keyword = filters.keyword.toLowerCase()
    result = result.filter(n => 
      n.title.toLowerCase().includes(keyword) || 
      n.content.toLowerCase().includes(keyword)
    )
  }

  return result
})

// 分页后的通知
const paginatedNotifications = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredNotifications.value.slice(start, end)
})

// 生命周期
onMounted(() => {
  fetchNotifications()
})

// 方法
const fetchNotifications = async () => {
  try {
    loading.value = true
    const response = await axios.get('/api/notifications/list', {
      params: { limit: 1000 }
    })
    
    notifications.value = response.data.sort((a, b) => 
      new Date(b.created_at) - new Date(a.created_at)
    )
  } catch (error) {
    console.error('获取通知列表失败:', error)
    ElMessage.error('获取通知列表失败')
  } finally {
    loading.value = false
  }
}

const refreshNotifications = () => {
  fetchNotifications()
}

const handleFilterChange = () => {
  currentPage.value = 1
}

const handleSearch = () => {
  currentPage.value = 1
}

const handlePageSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (page) => {
  currentPage.value = page
}

const handleNotificationClick = (notification) => {
  detailDialog.notification = notification
  detailDialog.visible = true
}

const handleDetailDialogOpen = () => {
  if (detailDialog.notification && !detailDialog.notification.is_read) {
    markAsRead(detailDialog.notification.id)
  }
}

const markAsReadFromDetail = async () => {
  if (detailDialog.notification) {
    await markAsRead(detailDialog.notification.id)
    detailDialog.visible = false
  }
}

const markAsRead = async (notificationId) => {
  try {
    await axios.post(`/api/notifications/${notificationId}/read`)
    
    // 更新本地数据
    const notification = notifications.value.find(n => n.id === notificationId)
    if (notification) {
      notification.is_read = true
    }
    
    ElMessage.success('已标记为已读')
  } catch (error) {
    console.error('标记已读失败:', error)
    ElMessage.error('标记已读失败')
  }
}

const markAllAsRead = async () => {
  try {
    const unreadIds = notifications.value.filter(n => !n.is_read).map(n => n.id)
    
    if (unreadIds.length === 0) {
      ElMessage.info('没有未读消息')
      return
    }

    await ElMessageBox.confirm('确定要将所有未读消息标记为已读吗？', '确认操作', {
      type: 'warning'
    })

    // 批量标记已读
    const promises = unreadIds.map(id => axios.post(`/api/notifications/${id}/read`))
    await Promise.all(promises)

    // 更新本地数据
    notifications.value.forEach(n => {
      if (!n.is_read) n.is_read = true
    })

    ElMessage.success(`已将 ${unreadIds.length} 条消息标记为已读`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量标记已读失败:', error)
      ElMessage.error('批量标记已读失败')
    }
  }
}

const clearAllNotifications = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有通知消息吗？此操作不可恢复。', '确认清空', {
      type: 'warning',
      confirmButtonText: '确定清空',
      cancelButtonText: '取消'
    })

    const promises = notifications.value.map(n => axios.delete(`/api/notifications/${n.id}`))
    await Promise.all(promises)

    notifications.value = []
    ElMessage.success('已清空所有通知消息')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空通知失败:', error)
      ElMessage.error('清空通知失败')
    }
  }
}

const handleNotificationAction = async (command, notification) => {
  switch (command) {
    case 'mark-read':
      await markAsRead(notification.id)
      break
    case 'mark-unread':
      await markAsUnread(notification.id)
      break
    case 'delete':
      await deleteNotification(notification)
      break
  }
}

const markAsUnread = async (notificationId) => {
  try {
    await axios.post(`/api/notifications/${notificationId}/unread`)
    
    // 更新本地数据
    const notification = notifications.value.find(n => n.id === notificationId)
    if (notification) {
      notification.is_read = false
    }
    
    ElMessage.success('已标记为未读')
  } catch (error) {
    console.error('标记未读失败:', error)
    ElMessage.error('标记未读失败')
  }
}

const deleteNotification = async (notification) => {
  try {
    await ElMessageBox.confirm(`确定要删除通知"${notification.title}"吗？`, '确认删除', {
      type: 'warning'
    })

    await axios.delete(`/api/notifications/${notification.id}`)
    
    // 从本地数据中移除
    const index = notifications.value.findIndex(n => n.id === notification.id)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }

    ElMessage.success('通知已删除')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除通知失败:', error)
      ElMessage.error('删除通知失败')
    }
  }
}

// 辅助方法
const getLevelIcon = (level) => {
  const iconMap = {
    info: InfoFilled,
    success: CircleCheckFilled,
    warning: WarningFilled,
    error: CircleCloseFilled
  }
  return iconMap[level] || QuestionFilled
}

const getLevelLabel = (level) => {
  const labelMap = {
    info: '信息',
    success: '成功',
    warning: '警告',
    error: '错误'
  }
  return labelMap[level] || '未知'
}

const getTypeTagType = (type) => {
  const typeMap = {
    system: '',
    task: 'success',
    storage: 'warning',
    user: 'info'
  }
  return typeMap[type] || ''
}

const getTypeLabel = (type) => {
  const labelMap = {
    system: '系统通知',
    task: '任务通知',
    storage: '存储通知',
    user: '用户通知'
  }
  return labelMap[type] || type
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date
  
  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour
  
  if (diff < minute) {
    return '刚刚'
  } else if (diff < hour) {
    return `${Math.floor(diff / minute)}分钟前`
  } else if (diff < day) {
    return `${Math.floor(diff / hour)}小时前`
  } else if (diff < 7 * day) {
    return `${Math.floor(diff / day)}天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}
</script>

<style scoped>
.notifications-page {
  padding: 20px;
  background: var(--bg-color);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-left h1 {
  margin: 0 0 5px 0;
  color: var(--text-color);
  font-size: 24px;
  font-weight: 600;
}

.page-description {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 12px;
}

/* 统计卡片 */
.stat-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
}

.stat-content {
  padding: 0;
}

.stat-flex {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
}

.stat-icon.total { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.stat-icon.unread { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
.stat-icon.info { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
.stat-icon.warning { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }

.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-color);
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 4px;
}

/* 过滤器 */
.filter-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.filter-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.filter-left {
  display: flex;
  gap: 12px;
  align-items: center;
}

.filter-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 通知列表 */
.notifications-card {
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.notifications-container {
  min-height: 400px;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.notification-item {
  position: relative;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 8px;
}

.notification-item:hover {
  border-color: var(--border-light);
  transform: translateX(2px);
}

.notification-item.unread {
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  box-shadow: var(--card-shadow);
}

.notification-content {
  flex: 1;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.notification-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.level-icon {
  font-size: 16px;
}

.level-icon.info { color: #409eff; }
.level-icon.success { color: #67c23a; }
.level-icon.warning { color: #e6a23c; }
.level-icon.error { color: #f56c6c; }

.notification-title {
  font-weight: 600;
  color: var(--text-color);
  font-size: 16px;
}

.notification-type-tag {
  margin-left: 8px;
}

.notification-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.notification-time {
  font-size: 12px;
  color: var(--text-secondary);
}

.notification-body {
  margin-left: 24px;
}

.notification-text {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.5;
  font-size: 14px;
}

.unread-indicator {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary-color);
}

/* 分页 */
.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

/* 详情弹窗 */
.notification-detail {
  padding: 12px 0;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.detail-level {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.detail-content {
  margin-bottom: 16px;
  padding: 16px;
  background: var(--bg-color-page);
  border-radius: 8px;
  border-left: 4px solid var(--primary-color);
}

.detail-content p {
  margin: 0;
  line-height: 1.6;
  color: var(--text-color);
}

.detail-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-item {
  display: flex;
  align-items: center;
}

.meta-label {
  font-weight: 500;
  color: var(--text-secondary);
  min-width: 80px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .notifications-page {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .filter-container {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .filter-left {
    flex-wrap: wrap;
  }
  
  .filter-right {
    justify-content: stretch;
  }
  
  .notification-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .notification-left {
    width: 100%;
  }
  
  .notification-right {
    width: 100%;
    justify-content: space-between;
  }
}
</style>