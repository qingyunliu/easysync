<template>
  <div class="task-detail">
    <!-- 基础信息 -->
    <el-card class="detail-card" header="基础信息">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="任务名称">{{ task.name }}</el-descriptions-item>
        <el-descriptions-item label="类型">
          <el-tag :type="getTaskTypeColor(task.type)">
            {{ getTaskTypeText(task.type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(task.status)">
            <el-icon style="vertical-align: middle; margin-right: 4px;">
              <component :is="getStatusIcon(task.status)" />
            </el-icon>
            {{ getStatusText(task.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="进度">
          <el-progress :percentage="task.progress || 0" :status="getProgressStatus(task.status)" :stroke-width="6" />
        </el-descriptions-item>
        <el-descriptions-item label="优先级">
          <el-tag :type="getPriorityType(task.priority)">
            {{ getPriorityText(task.priority) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="执行节点">
          {{ task.node_id ? getNodeName(task.node_id) : '未分配' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDateTime(task.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ task.started_at ? formatDateTime(task.started_at) : '未开始' }}</el-descriptions-item>
        <el-descriptions-item label="完成时间">{{ task.completed_at ? formatDateTime(task.completed_at) : '未完成' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 源端信息 -->
    <el-card class="detail-card" header="源端信息">
      <template v-if="task.source_type === 'storage' && task.source_storage_config">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="存储名称">{{ task.source_storage_config.name }}</el-descriptions-item>
          <el-descriptions-item label="存储类型">
            <el-tag :type="getStorageTypeColor(task.source_storage_config.type)">
              {{ getStorageTypeText(task.source_storage_config.type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(task.source_storage_config.status)">
              {{ getStatusText(task.source_storage_config.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="源端路径">{{ task.source_path }}</el-descriptions-item>
        </el-descriptions>
      </template>
      <template v-else-if="task.source_type === 'client' && task.source_client_config">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="客户端名称">{{ task.source_client_config.name }}</el-descriptions-item>
          <el-descriptions-item label="IP地址">{{ task.source_client_config.ip_address }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(task.source_client_config.status)">
              {{ getStatusText(task.source_client_config.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="源端路径">{{ task.source_path }}</el-descriptions-item>
        </el-descriptions>
      </template>
      <template v-else>
        <div class="no-data">无源端信息</div>
      </template>
    </el-card>

    <!-- 目标端信息 -->
    <el-card class="detail-card" header="目标端信息">
      <template v-if="task.target_storage_config">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="存储名称">{{ task.target_storage_config.name }}</el-descriptions-item>
          <el-descriptions-item label="存储类型">
            <el-tag :type="getStorageTypeColor(task.target_storage_config.type)">
              {{ getStorageTypeText(task.target_storage_config.type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(task.target_storage_config.status)">
              {{ getStatusText(task.target_storage_config.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="目标路径">{{ task.target_path }}</el-descriptions-item>
        </el-descriptions>
      </template>
      <template v-else>
        <div class="no-data">无目标端信息</div>
      </template>
    </el-card>

    <!-- 同步选项 -->
    <el-card class="detail-card" header="同步选项">
      <template v-if="task.options">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="删除目标多余文件">
            <el-tag :type="task.options.delete ? 'success' : 'info'">{{ task.options.delete ? '是' : '否' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="校验和检查">
            <el-tag :type="task.options.checksum ? 'success' : 'info'">{{ task.options.checksum ? '是' : '否' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="压缩传输">
            <el-tag :type="task.options.compress ? 'success' : 'info'">{{ task.options.compress ? '是' : '否' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="带宽限制">
            {{ task.options.bandwidth_limit ? `${task.options.bandwidth_limit} KB/s` : '无限制' }}
          </el-descriptions-item>
          <el-descriptions-item label="最大连接数">
            {{ task.options.max_connections || '默认' }}
          </el-descriptions-item>
          <el-descriptions-item label="重试次数">
            {{ task.options.retry_options?.max_retries || '默认' }}
          </el-descriptions-item>
        </el-descriptions>
      </template>
      <template v-else>
        <div class="no-data">无同步选项</div>
      </template>
    </el-card>

    <!-- 传输统计信息 -->
    <el-card class="detail-card" header="传输统计" v-if="task.details && hasTransferStats(task.details)">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ task.details.transferred_files || 0 }}</div>
              <div class="stat-label">已传输文件</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ task.details.total_files || 0 }}</div>
              <div class="stat-label">总文件数</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ formatFileSize(task.details.transferred_size || 0) }}</div>
              <div class="stat-label">已传输大小</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ formatFileSize(task.details.total_size || 0) }}</div>
              <div class="stat-label">总大小</div>
            </div>
          </div>
        </el-col>
      </el-row>
      
      <!-- 传输速度和ETA -->
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="8">
          <div class="stat-item">
            <div class="stat-icon speed">
              <el-icon><Loading /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ task.details.transfer_speed || '0 B/s' }}</div>
              <div class="stat-label">传输速度</div>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="stat-item">
            <div class="stat-icon eta">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ task.details.eta || '--:--' }}</div>
              <div class="stat-label">预计剩余时间</div>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="stat-item">
            <div class="stat-icon progress">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ task.details.progress || 0 }}%</div>
              <div class="stat-label">完成进度</div>
            </div>
          </div>
        </el-col>
      </el-row>
      
      <!-- 当前传输文件 -->
      <div v-if="task.details.current_file" style="margin-top: 20px;">
        <el-divider content-position="left">当前传输文件</el-divider>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="文件路径">{{ task.details.current_file.path }}</el-descriptions-item>
          <el-descriptions-item label="文件大小">{{ formatFileSize(task.details.current_file.size) }}</el-descriptions-item>
          <el-descriptions-item label="已传输">{{ formatFileSize(task.details.current_file.transferred) }}</el-descriptions-item>
          <el-descriptions-item label="传输速度">{{ task.details.current_file.speed }}</el-descriptions-item>
        </el-descriptions>
      </div>
      
      <!-- 最后更新时间 -->
      <div v-if="task.details.last_update" style="margin-top: 15px; text-align: right; color: var(--text-secondary); font-size: 12px;">
        最后更新: {{ formatDateTime(task.details.last_update) }}
      </div>
    </el-card>

    <!-- 任务统计 -->
    <el-card class="detail-card" header="任务统计">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-number">{{ task.stats?.total_files || 0 }}</div>
            <div class="stat-label">总文件数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-number">{{ task.stats?.processed_files || 0 }}</div>
            <div class="stat-label">已处理文件</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-number">{{ formatSize(task.stats?.total_size || 0) }}</div>
            <div class="stat-label">总大小</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-number">{{ formatSize(task.stats?.processed_size || 0) }}</div>
            <div class="stat-label">已处理大小</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 错误信息 -->
    <el-card v-if="task.error_message" class="detail-card" header="错误信息">
      <el-alert
        :title="task.error_message"
        type="error"
        show-icon
        :closable="false"
      />
    </el-card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  CircleCheck, Clock, Loading, Warning, CircleClose, Document, Connection
} from '@element-plus/icons-vue'

const props = defineProps({
  task: {
    type: Object,
    required: true
  },
  nodes: {
    type: Array,
    default: () => []
  }
})

// 辅助函数
const getStatusType = (status) => {
  const types = {
    active: 'success',
    pending: 'info',
    assigned: 'warning',
    running: 'success',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info',
    cancel_requested: 'info'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    active: '活跃',
    pending: '等待中',
    assigned: '已分配',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
    cancel_requested: '取消中'
  }
  return texts[status] || status
}

const getStatusIcon = (status) => {
  const icons = {
    active: CircleCheck,
    pending: Clock,
    assigned: Loading,
    running: Loading,
    completed: CircleCheck,
    failed: CircleClose,
    cancelled: Warning,
    cancel_requested: Warning
  }
  return icons[status] || Clock
}

const getTaskTypeColor = (type) => {
  const colors = {
    sync: 'primary',
    copy: 'success',
    'mount-check': 'warning'
  }
  return colors[type] || 'info'
}

const getTaskTypeText = (type) => {
  const texts = {
    sync: '同步',
    copy: '复制',
    'mount-check': '挂载检测'
  }
  return texts[type] || type
}

const getPriorityType = (priority) => {
  const types = {
    1: 'info',
    2: 'success',
    3: 'warning',
    4: 'danger'
  }
  return types[priority] || 'info'
}

const getPriorityText = (priority) => {
  const texts = {
    1: '低',
    2: '普通',
    3: '高',
    4: '紧急'
  }
  return texts[priority] || '普通'
}

const getProgressStatus = (status) => {
  if (status === 'failed') return 'exception'
  if (status === 'completed') return 'success'
  return ''
}

const getNodeName = (nodeId) => {
  const node = props.nodes.find(n => n.id === nodeId)
  return node ? node.name : `节点${nodeId}`
}

const getStorageTypeColor = (type) => {
  const colors = {
    local: 'info',
    nfs: 'success',
    smb: 'warning',
    ftp: 'danger',
    s3: 'primary',
    obs: 'primary',
    nas: 'success'
  }
  return colors[type] || 'info'
}

const getStorageTypeText = (type) => {
  const texts = {
    local: '本地',
    nfs: 'NFS',
    smb: 'SMB',
    ftp: 'FTP',
    s3: 'S3',
    obs: 'OBS',
    nas: 'NAS'
  }
  return texts[type] || type
}

const formatDateTime = (datetime) => {
  if (!datetime) return '-'
  return new Date(datetime).toLocaleString()
}

const formatSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

const hasTransferStats = (details) => {
  return details && (
    details.transferred_files > 0 || 
    details.total_files > 0 || 
    details.transferred_size > 0 || 
    details.total_size > 0 || 
    details.transfer_speed || 
    details.eta || 
    details.progress > 0 || 
    details.current_file
  )
}
</script>

<style scoped>
.task-detail {
  padding: 20px;
}

.detail-card {
  margin-bottom: 20px;
}

.detail-card:last-child {
  margin-bottom: 0;
}

.no-data {
  text-align: center;
  color: var(--el-text-color-secondary);
  padding: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  padding: 15px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  margin-right: 15px;
  font-size: 20px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.stat-icon.speed {
  background: var(--el-color-success-light-9);
  color: var(--el-color-success);
}

.stat-icon.eta {
  background: var(--el-color-warning-light-9);
  color: var(--el-color-warning);
}

.stat-icon.progress {
  background: var(--el-color-info-light-9);
  color: var(--el-color-info);
}

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: var(--el-text-color-primary);
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

:deep(.el-card__header) {
  background: var(--el-color-primary-light-9);
  border-bottom: 1px solid var(--el-border-color-light);
  font-weight: 600;
}

:deep(.el-descriptions__label) {
  font-weight: 500;
}
</style> 