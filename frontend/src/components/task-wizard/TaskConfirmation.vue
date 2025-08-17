<template>
  <div class="task-confirmation">
    <!-- 页面标题 -->
    <div class="confirmation-header">
      <h3>{{ $t('taskConfirmation.confirmTaskConfig') }}</h3>
      <p class="confirmation-description">{{ $t('taskConfirmation.confirmTaskConfigDesc') }}</p>
    </div>

    <!-- 配置概览 -->
    <div class="config-overview">
      <!-- 源端配置 -->
      <div class="config-section">
        <div class="section-header">
          <Icon icon="mdi:source" class="section-icon" />
          <h4>{{ $t('taskConfirmation.sourceConfig') }}</h4>
        </div>
        
        <div class="section-content">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">{{ $t('taskConfirmation.storageName') }}</span>
              <span class="info-value">{{ wizardData.source.storageName }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('taskConfirmation.storageType') }}</span>
              <el-tag :type="getStorageTypeColor(wizardData.source.storageType)" size="small">
                {{ getStorageTypeText(wizardData.source.storageType) }}
              </el-tag>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('taskConfirmation.selectedItems') }}</span>
              <span class="info-value">{{ wizardData.source.selectedPaths.length }} {{ $t('taskConfirmation.items') }}</span>
            </div>
          </div>
          
          <!-- 选中的文件/目录列表 -->
          <div v-if="wizardData.source.selectedPaths.length > 0" class="selected-items">
            <div class="items-header">
              <Icon icon="mdi:file-multiple" class="items-icon" />
              <span>{{ $t('taskConfirmation.selectedFilesDirectories') }}</span>
            </div>
            <div class="items-list">
              <el-tag
                v-for="item in wizardData.source.selectedPaths"
                :key="item.path"
                class="selected-item"
                size="small"
              >
                <Icon 
                  :icon="item.type === 'directory' ? 'mdi:folder' : 'mdi:file'" 
                  class="item-icon"
                />
                {{ item.name }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>

      <!-- 目标端配置 -->
      <div class="config-section">
        <div class="section-header">
          <Icon icon="mdi:target" class="section-icon" />
          <h4>{{ $t('taskConfirmation.targetConfig') }}</h4>
        </div>
        
        <div class="section-content">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">{{ $t('taskConfirmation.storageName') }}</span>
              <span class="info-value">{{ wizardData.target.storageName }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('taskConfirmation.storageType') }}</span>
              <el-tag :type="getStorageTypeColor(wizardData.target.storageType)" size="small">
                {{ getStorageTypeText(wizardData.target.storageType) }}
              </el-tag>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('taskConfirmation.targetPath') }}</span>
              <span class="info-value path-value">{{ wizardData.target.targetPath }}</span>
            </div>
          </div>
          
          <!-- 数据覆盖警告 -->
          <div v-if="showOverrideWarning" class="override-warning">
            <el-alert
              :title="$t('taskConfirmation.dataOverrideWarning')"
              type="warning"
              :description="overrideWarningText"
              show-icon
              :closable="false"
            />
          </div>
        </div>
      </div>

      <!-- 任务参数 -->
      <div class="config-section">
        <div class="section-header">
          <Icon icon="mdi:cog" class="section-icon" />
          <h4>{{ $t('taskConfirmation.taskParameters') }}</h4>
        </div>
        
        <div class="section-content">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">{{ $t('taskConfirmation.taskName') }}</span>
              <span class="info-value">{{ wizardData.parameters.taskName }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('taskConfirmation.priority') }}</span>
              <el-tag :type="getPriorityType(wizardData.parameters.priority)" size="small">
                {{ getPriorityText(wizardData.parameters.priority) }}
              </el-tag>
            </div>
            <div class="info-item full-width">
              <span class="info-label">{{ $t('taskConfirmation.taskDescription') }}</span>
              <span class="info-value">{{ wizardData.parameters.description || $t('taskConfirmation.noDescription') }}</span>
            </div>
          </div>
          
          <!-- 同步选项 -->
          <div class="options-section">
            <div class="options-header">
              <Icon icon="mdi:sync" class="options-icon" />
              <span>{{ $t('taskConfirmation.syncOptions') }}</span>
            </div>
            <div class="options-grid">
              <div class="option-item">
                <Icon icon="mdi:delete" class="option-icon" />
                <span>{{ $t('taskConfirmation.deleteExtraFiles') }}</span>
                <el-tag :type="wizardData.parameters.syncOptions.delete ? 'success' : 'info'" size="small">
                  {{ wizardData.parameters.syncOptions.delete ? $t('common.yes') : $t('common.no') }}
                </el-tag>
              </div>
              <div class="option-item">
                <Icon icon="mdi:compress" class="option-icon" />
                <span>{{ $t('taskConfirmation.enableCompression') }}</span>
                <el-tag :type="wizardData.parameters.syncOptions.compress ? 'success' : 'info'" size="small">
                  {{ wizardData.parameters.syncOptions.compress ? $t('common.yes') : $t('common.no') }}
                </el-tag>
              </div>
              <div class="option-item">
                <Icon icon="mdi:check-circle" class="option-icon" />
                <span>{{ $t('taskConfirmation.checksumVerification') }}</span>
                <el-tag :type="wizardData.parameters.syncOptions.checksum ? 'success' : 'info'" size="small">
                  {{ wizardData.parameters.syncOptions.checksum ? $t('common.yes') : $t('common.no') }}
                </el-tag>
              </div>
              <div class="option-item">
                <Icon icon="mdi:speedometer" class="option-icon" />
                <span>{{ $t('taskConfirmation.bandwidthLimit') }}</span>
                <el-tag type="info" size="small">
                  {{ wizardData.parameters.syncOptions.bandwidth_limit || 0 }} MB/s
                </el-tag>
              </div>
              <div class="option-item">
                <Icon icon="mdi:connection" class="option-icon" />
                <span>{{ $t('taskConfirmation.maxConnections') }}</span>
                <el-tag type="info" size="small">
                  {{ wizardData.parameters.syncOptions.max_connections }}
                </el-tag>
              </div>
            </div>
          </div>
          
          <!-- 传输策略 -->
          <div class="options-section">
            <div class="options-header">
              <Icon icon="mdi:connection" class="options-icon" />
              <span>{{ $t('taskConfirmation.transferStrategy') }}</span>
            </div>
            <div class="options-grid">
              <div class="option-item">
                <Icon icon="mdi:refresh" class="option-icon" />
                <span>{{ $t('taskConfirmation.retryCount') }}</span>
                <el-tag type="info" size="small">
                  {{ wizardData.parameters.retryOptions.max_retries }}
                </el-tag>
              </div>
              <div class="option-item">
                <Icon icon="mdi:timer" class="option-icon" />
                <span>{{ $t('taskConfirmation.retryInterval') }}</span>
                <el-tag type="info" size="small">
                  {{ wizardData.parameters.retryOptions.retry_interval }} {{ $t('common.seconds') }}
                </el-tag>
              </div>
            </div>
          </div>
          
          <!-- 高级参数 -->
          <div class="options-section">
            <div class="options-header">
              <Icon icon="mdi:settings" class="options-icon" />
              <span>{{ $t('taskConfirmation.advancedParameters') }}</span>
            </div>
            <div class="options-grid">
              <div class="option-item">
                <Icon icon="mdi:memory" class="option-icon" />
                <span>{{ $t('taskConfirmation.bufferSize') }}</span>
                <el-tag type="info" size="small">
                  {{ wizardData.parameters.advancedOptions?.buffer_size || 10 }} MB
                </el-tag>
              </div>
              <div class="option-item">
                <Icon icon="mdi:clock" class="option-icon" />
                <span>{{ $t('taskConfirmation.timeout') }}</span>
                <el-tag type="info" size="small">
                  {{ wizardData.parameters.advancedOptions?.timeout || 300 }} {{ $t('common.seconds') }}
                </el-tag>
              </div>
              <div class="option-item">
                <Icon icon="mdi:filter" class="option-icon" />
                <span>{{ $t('taskConfirmation.excludePatterns') }}</span>
                <el-tag type="info" size="small">
                  {{ wizardData.parameters.advancedOptions?.exclude_patterns || $t('taskConfirmation.none') }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 预估信息 -->
      <div class="config-section">
        <div class="section-header">
          <Icon icon="mdi:chart-line" class="section-icon" />
          <h4>{{ $t('taskConfirmation.estimatedInfo') }}</h4>
        </div>
        
        <div class="section-content">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">{{ $t('taskConfirmation.estimatedFileCount') }}</span>
              <span class="info-value">{{ estimatedFileCount }} {{ $t('taskConfirmation.files') }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('taskConfirmation.estimatedTotalSize') }}</span>
              <span class="info-value">{{ estimatedTotalSize }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('taskConfirmation.estimatedTransferTime') }}</span>
              <span class="info-value">{{ estimatedTransferTime }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('taskConfirmation.estimatedBandwidthUsage') }}</span>
              <span class="info-value">{{ estimatedBandwidthUsage }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 确认操作 -->
    <div class="confirmation-actions">
      <el-alert
        :title="$t('taskConfirmation.confirmConfigInfo')"
        type="info"
        :description="$t('taskConfirmation.confirmConfigInfoDesc')"
        show-icon
        :closable="false"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'

const { t } = useI18n()

const props = defineProps({
  wizardData: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['confirm'])

// 计算属性
const showOverrideWarning = computed(() => {
  return props.wizardData.source.storageId && 
         props.wizardData.target.storageId && 
         props.wizardData.source.storageId === props.wizardData.target.storageId
})

const overrideWarningText = computed(() => {
  if (props.wizardData.target.storageType === 's3') {
    return t('taskConfirmation.overrideWarningObs')
  } else {
    return t('taskConfirmation.overrideWarningNas')
  }
})

const estimatedFileCount = computed(() => {
  return props.wizardData.source.selectedPaths.length
})

const estimatedTotalSize = computed(() => {
  const totalSize = props.wizardData.source.selectedPaths.reduce((sum, item) => {
    return sum + (item.size || 0)
  }, 0)
  
  if (totalSize === 0) return t('taskConfirmation.unknown')
  
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let size = totalSize
  let unitIndex = 0
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`
})

const estimatedTransferTime = computed(() => {
  const totalSize = props.wizardData.source.selectedPaths.reduce((sum, item) => {
    return sum + (item.size || 0)
  }, 0)
  
  if (totalSize === 0) return t('taskConfirmation.unknown')
  
  const bandwidth = props.wizardData.parameters.syncOptions.bandwidth_limit || 10 // MB/s
  const timeInSeconds = totalSize / (1024 * 1024) / bandwidth
  
  if (timeInSeconds < 60) {
    return `${Math.ceil(timeInSeconds)} ${t('common.seconds')}`
  } else if (timeInSeconds < 3600) {
    return `${Math.ceil(timeInSeconds / 60)} ${t('taskConfirmation.minutes')}`
  } else {
    return `${Math.ceil(timeInSeconds / 3600)} ${t('taskConfirmation.hours')}`
  }
})

const estimatedBandwidthUsage = computed(() => {
  const bandwidth = props.wizardData.parameters.syncOptions.bandwidth_limit || 0
  return bandwidth === 0 ? t('taskConfirmation.noLimit') : `${bandwidth} MB/s`
})

// 方法
const getStorageTypeColor = (type) => {
  const colors = {
    'nas': 'success',
    's3': 'primary',
    'nfs': 'warning',
    'smb': 'info'
  }
  return colors[type] || 'info'
}

const getStorageTypeText = (type) => {
  const texts = {
    'nas': 'NAS',
    's3': 'OBS',
    'nfs': 'NFS',
    'smb': 'SMB'
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
    1: t('taskConfirmation.priorities.low'),
    2: t('taskConfirmation.priorities.normal'),
    3: t('taskConfirmation.priorities.high'),
    4: t('taskConfirmation.priorities.urgent')
  }
  return texts[priority] || t('taskConfirmation.priorities.normal')
}
</script>

<style scoped>
.task-confirmation {
  padding: 20px;
}

.confirmation-header {
  margin-bottom: 30px;
}

.confirmation-header h3 {
  margin: 0 0 8px 0;
  color: var(--el-text-color-primary);
  font-size: 20px;
  font-weight: 600;
}

.confirmation-description {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  line-height: 1.5;
}

.config-overview {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.config-section {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  overflow: hidden;
  background: var(--el-bg-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: linear-gradient(135deg, var(--el-color-primary-light-9) 0%, var(--el-color-primary-light-8) 100%);
  border-bottom: 1px solid var(--el-border-color);
}

.section-icon {
  font-size: 20px;
  color: var(--el-color-primary);
}

.section-header h4 {
  margin: 0;
  color: var(--el-text-color-primary);
  font-size: 16px;
  font-weight: 600;
}

.section-content {
  padding: 20px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-weight: 500;
}

.info-value {
  font-size: 14px;
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.path-value {
  word-break: break-all;
  font-family: monospace;
  background: var(--el-bg-color-page);
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid var(--el-border-color-light);
}

.selected-items {
  margin-top: 16px;
}

.items-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.items-icon {
  font-size: 16px;
  color: var(--el-color-primary);
}

.items-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.selected-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.item-icon {
  font-size: 14px;
}

.override-warning {
  margin-top: 16px;
}

.options-section {
  margin-top: 20px;
}

.options-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.options-icon {
  font-size: 16px;
  color: var(--el-color-primary);
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--el-bg-color-page);
  border-radius: 6px;
  border: 1px solid var(--el-border-color-light);
}

.option-icon {
  font-size: 16px;
  color: var(--el-color-primary);
  flex-shrink: 0;
}

.option-item span {
  flex: 1;
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.confirmation-actions {
  margin-top: 30px;
}

:deep(.el-alert) {
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.el-tag) {
  border-radius: 4px;
  font-weight: 500;
}
</style> 