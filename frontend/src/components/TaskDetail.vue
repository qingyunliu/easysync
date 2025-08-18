<template>
  <div class="task-detail">
    <!-- 基础信息 -->
    <el-card class="detail-card" :header="$t('taskDetail.basicInfo')">
      <el-descriptions :column="3" border>
        <el-descriptions-item :label="$t('taskDetail.taskName')">{{ task.name }}</el-descriptions-item>
        <el-descriptions-item :label="$t('taskDetail.type')">
          <el-tag :type="getTaskTypeColor(task.type)">
            {{ getTaskTypeText(task.type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('taskDetail.status')">
          <el-tag :type="getStatusType(task.status)">
            <el-icon style="vertical-align: middle; margin-right: 4px;">
              <component :is="getStatusIcon(task.status)" />
            </el-icon>
            {{ getStatusText(task.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('taskDetail.progress')">
          <el-progress :percentage="task.progress || 0" :status="getProgressStatus(task.status)" :stroke-width="6" />
        </el-descriptions-item>
        <el-descriptions-item :label="$t('taskDetail.priority')">
          <el-tag :type="getPriorityType(task.priority)">
            {{ getPriorityText(task.priority) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('taskDetail.executionNode')">
          {{ task.node_id ? getNodeName(task.node_id) : $t('taskDetail.unassigned') }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('taskDetail.createTime')">{{ formatDateTime(task.created_at)
          }}</el-descriptions-item>
        <el-descriptions-item :label="$t('taskDetail.startTime')">{{ task.started_at ? formatDateTime(task.started_at) :
          $t('taskDetail.notStarted') }}</el-descriptions-item>
        <el-descriptions-item :label="$t('taskDetail.completeTime')">{{ task.completed_at ?
          formatDateTime(task.completed_at) : $t('taskDetail.notCompleted') }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 源端信息 -->
    <el-card class="detail-card" :header="$t('taskDetail.sourceInfo')">
      <template v-if="task.source_type === 'storage' && task.source_storage_config">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('taskDetail.storageName')">{{ task.source_storage_config.name
            }}</el-descriptions-item>
          <el-descriptions-item :label="$t('taskDetail.storageType')">
            <el-tag :type="getStorageTypeColor(task.source_storage_config.type)">
              {{ getStorageTypeText(task.source_storage_config.type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('taskDetail.status')">
            <el-tag :type="getStatusType(task.source_storage_config.status)">
              {{ getStatusText(task.source_storage_config.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('taskDetail.sourcePath')">{{ task.source_path }}</el-descriptions-item>
        </el-descriptions>
      </template>
      <template v-else-if="task.source_type === 'client' && task.source_client_config">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('taskDetail.clientName')">{{ task.source_client_config.name
            }}</el-descriptions-item>
          <el-descriptions-item :label="$t('taskDetail.ipAddress')">{{ task.source_client_config.ip_address
            }}</el-descriptions-item>
          <el-descriptions-item :label="$t('taskDetail.status')">
            <el-tag :type="getStatusType(task.source_client_config.status)">
              {{ getStatusText(task.source_client_config.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('taskDetail.sourcePath')">{{ task.source_path }}</el-descriptions-item>
        </el-descriptions>
      </template>
      <template v-else>
        <div class="no-data">{{ $t('taskDetail.noSourceInfo') }}</div>
      </template>
    </el-card>

    <!-- 目标端信息 -->
    <el-card class="detail-card" :header="$t('taskDetail.targetInfo')">
      <template v-if="task.target_storage_config">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('taskDetail.storageName')">{{ task.target_storage_config.name
            }}</el-descriptions-item>
          <el-descriptions-item :label="$t('taskDetail.storageType')">
            <el-tag :type="getStorageTypeColor(task.target_storage_config.type)">
              {{ getStorageTypeText(task.target_storage_config.type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('taskDetail.status')">
            <el-tag :type="getStatusType(task.target_storage_config.status)">
              {{ getStatusText(task.target_storage_config.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('taskDetail.targetPath')">{{ task.target_path }}</el-descriptions-item>
        </el-descriptions>
      </template>
      <template v-else>
        <div class="no-data">{{ $t('taskDetail.noTargetInfo') }}</div>
      </template>
    </el-card>

    <!-- 同步选项 -->
    <el-card class="detail-card" :header="$t('taskDetail.syncOptions')">
      <template v-if="task.options">
        <el-descriptions :column="3" border>
          <el-descriptions-item :label="$t('taskDetail.deleteExtraFiles')">
            <el-tag :type="task.options.delete ? 'success' : 'info'">{{ task.options.delete ? $t('common.yes') :
              $t('common.no') }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('taskDetail.checksumCheck')">
            <el-tag :type="task.options.checksum ? 'success' : 'info'">{{ task.options.checksum ? $t('common.yes') :
              $t('common.no') }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('taskDetail.compressTransfer')">
            <el-tag :type="task.options.compress ? 'success' : 'info'">{{ task.options.compress ? $t('common.yes') :
              $t('common.no') }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('taskDetail.bandwidthLimit')">
            {{ task.options.bandwidth_limit ? `${task.options.bandwidth_limit} KB/s` : $t('taskDetail.noLimit') }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('taskDetail.maxConnections')">
            {{ task.options.max_connections || $t('taskDetail.default') }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('taskDetail.retryCount')">
            {{ task.options.retry_options?.max_retries || $t('taskDetail.default') }}
          </el-descriptions-item>
        </el-descriptions>
      </template>
      <template v-else>
        <div class="no-data">{{ $t('taskDetail.noSyncOptions') }}</div>
      </template>
    </el-card>

    <!-- 传输统计信息 -->
    <el-card class="detail-card" :header="$t('taskDetail.transferStatistics')"
      v-if="task.details && hasTransferStats(task.details)">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon>
                <Document />
              </el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ task.details.transferred_files || 0 }}</div>
              <div class="stat-label">{{ $t('taskDetail.transferredFiles') }}</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon>
                <Document />
              </el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ task.details.total_files || 0 }}</div>
              <div class="stat-label">{{ $t('taskDetail.totalFiles') }}</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon>
                <Connection />
              </el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ formatFileSize(task.details.transferred_size || 0) }}</div>
              <div class="stat-label">{{ $t('taskDetail.transferredSize') }}</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon>
                <Connection />
              </el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ formatFileSize(task.details.total_size || 0) }}</div>
              <div class="stat-label">{{ $t('taskDetail.totalSize') }}</div>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 传输速度和ETA -->
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="8">
          <div class="stat-item">
            <div class="stat-icon speed">
              <el-icon>
                <Loading />
              </el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ task.details.transfer_speed || '0 B/s' }}</div>
              <div class="stat-label">{{ $t('taskDetail.transferSpeed') }}</div>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="stat-item">
            <div class="stat-icon eta">
              <el-icon>
                <Clock />
              </el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ task.details.eta || '--:--' }}</div>
              <div class="stat-label">{{ $t('taskDetail.estimatedTime') }}</div>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="stat-item">
            <div class="stat-icon progress">
              <el-icon>
                <CircleCheck />
              </el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ task.details.progress || 0 }}%</div>
              <div class="stat-label">{{ $t('taskDetail.completionProgress') }}</div>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 当前阶段 -->
      <div v-if="task.details.current_phase" style="margin-top: 20px;">
        <el-divider content-position="left">{{ $t('taskDetail.currentPhase') }}</el-divider>
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('taskDetail.phase')">{{ getPhaseText(task.details.current_phase)
            }}</el-descriptions-item>
          <el-descriptions-item :label="$t('taskDetail.progress')">{{ task.details.progress || 0
            }}%</el-descriptions-item>
          <el-descriptions-item v-if="task.details.transferred_files !== undefined"
            :label="$t('taskDetail.processedFiles')">{{ task.details.transferred_files }}/{{ task.details.total_files
            }}</el-descriptions-item>
          <el-descriptions-item v-if="task.details.transfer_speed" :label="$t('taskDetail.transferSpeed')">{{
            task.details.transfer_speed }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 当前传输文件 -->
      <div v-if="task.details.current_file" style="margin-top: 20px;">
        <el-divider content-position="left">{{ $t('taskDetail.currentTransferFile') }}</el-divider>
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('taskDetail.filePath')">{{ task.details.current_file.path
            }}</el-descriptions-item>
          <el-descriptions-item :label="$t('taskDetail.fileSize')">{{ formatFileSize(task.details.current_file.size)
            }}</el-descriptions-item>
          <el-descriptions-item :label="$t('taskDetail.transferred')">{{
            formatFileSize(task.details.current_file.transferred) }}</el-descriptions-item>
          <el-descriptions-item :label="$t('taskDetail.transferSpeed')">{{ task.details.current_file.speed
            }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 最后更新时间 -->
      <div v-if="task.details.last_update"
        style="margin-top: 15px; text-align: right; color: var(--text-secondary); font-size: 12px;">
        {{ $t('taskDetail.lastUpdate') }}: {{ formatDateTime(task.details.last_update) }}
      </div>
    </el-card>

    <!-- 任务统计 -->
    <el-card class="detail-card" :header="$t('taskDetail.taskStatistics')">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-number">{{ task.stats?.total_files || 0 }}</div>
            <div class="stat-label">{{ $t('taskDetail.totalFiles') }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-number">{{ task.stats?.processed_files || 0 }}</div>
            <div class="stat-label">{{ $t('taskDetail.processedFiles') }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-number">{{ formatSize(task.stats?.total_size || 0) }}</div>
            <div class="stat-label">{{ $t('taskDetail.totalSize') }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-number">{{ formatSize(task.stats?.processed_size || 0) }}</div>
            <div class="stat-label">{{ $t('taskDetail.processedSize') }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 错误信息 -->
    <el-card v-if="task.error_message" class="detail-card" :header="$t('taskDetail.errorInfo')">
      <el-alert :title="task.error_message" type="error" show-icon :closable="false" />
    </el-card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  CircleCheck, Clock, Loading, Warning, CircleClose, Document, Connection
} from '@element-plus/icons-vue'

const { t } = useI18n()

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
    active: t('tasks.statuses.running'),
    pending: t('tasks.statuses.pending'),
    assigned: t('tasks.statuses.assigned'),
    running: t('tasks.statuses.running'),
    completed: t('tasks.statuses.completed'),
    failed: t('tasks.statuses.failed'),
    cancelled: t('tasks.statuses.cancelled'),
    cancel_requested: t('tasks.statuses.cancelled')
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
    sync: t('tasks.types.sync'),
    copy: t('tasks.types.copy'),
    'mount-check': t('tasks.types.mountCheck')
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
    1: t('tasks.priorities.low'),
    2: t('tasks.priorities.normal'),
    3: t('tasks.priorities.high'),
    4: t('tasks.priorities.urgent')
  }
  return texts[priority] || t('tasks.priorities.normal')
}

const getProgressStatus = (status) => {
  if (status === 'failed') return 'exception'
  if (status === 'completed') return 'success'
  return ''
}

const getPhaseText = (phase) => {
  const phases = {
    'initializing': t('taskDetail.phases.initializing'),
    'checking': t('taskDetail.phases.checking'),
    'transferring': t('taskDetail.phases.transferring'),
    'completed': t('taskDetail.phases.completed')
  }
  return phases[phase] || phase
}

const getNodeName = (nodeId) => {
  const node = props.nodes.find(n => n.id === nodeId)
  return node ? node.name : `${t('taskDetail.node')}${nodeId}`
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
    local: t('taskDetail.storageTypes.local'),
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