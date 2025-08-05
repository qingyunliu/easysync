<template>
  <div class="task-confirmation">
    <!-- 页面标题 -->
    <div class="confirmation-header">
      <h3>确认任务配置</h3>
      <p class="confirmation-description">请确认以下配置信息，确认无误后点击创建任务</p>
    </div>

    <!-- 配置概览 -->
    <div class="config-overview">
      <!-- 源端配置 -->
      <div class="config-section">
        <div class="section-header">
          <Icon icon="mdi:source" class="section-icon" />
          <h4>源端配置</h4>
        </div>
        
        <div class="section-content">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">存储名称</span>
              <span class="info-value">{{ wizardData.source.storageName }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">存储类型</span>
              <el-tag :type="getStorageTypeColor(wizardData.source.storageType)" size="small">
                {{ getStorageTypeText(wizardData.source.storageType) }}
              </el-tag>
            </div>
            <div class="info-item">
              <span class="info-label">选中项目</span>
              <span class="info-value">{{ wizardData.source.selectedPaths.length }} 项</span>
            </div>
          </div>
          
          <!-- 选中的文件/目录列表 -->
          <div v-if="wizardData.source.selectedPaths.length > 0" class="selected-items">
            <div class="items-header">
              <Icon icon="mdi:file-multiple" class="items-icon" />
              <span>选中的文件/目录</span>
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
          <h4>目标端配置</h4>
        </div>
        
        <div class="section-content">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">存储名称</span>
              <span class="info-value">{{ wizardData.target.storageName }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">存储类型</span>
              <el-tag :type="getStorageTypeColor(wizardData.target.storageType)" size="small">
                {{ getStorageTypeText(wizardData.target.storageType) }}
              </el-tag>
            </div>
            <div class="info-item">
              <span class="info-label">目标路径</span>
              <span class="info-value path-value">{{ wizardData.target.targetPath }}</span>
            </div>
          </div>
          
          <!-- 数据覆盖警告 -->
          <div v-if="showOverrideWarning" class="override-warning">
            <el-alert
              title="数据覆盖警告"
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
          <h4>任务参数</h4>
        </div>
        
        <div class="section-content">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">任务名称</span>
              <span class="info-value">{{ wizardData.parameters.taskName }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">优先级</span>
              <el-tag :type="getPriorityType(wizardData.parameters.priority)" size="small">
                {{ getPriorityText(wizardData.parameters.priority) }}
              </el-tag>
            </div>
            <div class="info-item full-width">
              <span class="info-label">任务描述</span>
              <span class="info-value">{{ wizardData.parameters.description || '无描述' }}</span>
            </div>
          </div>
          
          <!-- 同步选项 -->
          <div class="options-section">
            <div class="options-header">
              <Icon icon="mdi:sync" class="options-icon" />
              <span>同步选项</span>
            </div>
            <div class="options-grid">
              <div class="option-item">
                <Icon icon="mdi:delete" class="option-icon" />
                <span>删除目标多余文件</span>
                <el-tag :type="wizardData.parameters.syncOptions.delete ? 'success' : 'info'" size="small">
                  {{ wizardData.parameters.syncOptions.delete ? '是' : '否' }}
                </el-tag>
              </div>
              <div class="option-item">
                <Icon icon="mdi:compress" class="option-icon" />
                <span>启用压缩传输</span>
                <el-tag :type="wizardData.parameters.syncOptions.compress ? 'success' : 'info'" size="small">
                  {{ wizardData.parameters.syncOptions.compress ? '是' : '否' }}
                </el-tag>
              </div>
              <div class="option-item">
                <Icon icon="mdi:check-circle" class="option-icon" />
                <span>校验文件完整性</span>
                <el-tag :type="wizardData.parameters.syncOptions.checksum ? 'success' : 'info'" size="small">
                  {{ wizardData.parameters.syncOptions.checksum ? '是' : '否' }}
                </el-tag>
              </div>
              <div class="option-item">
                <Icon icon="mdi:speedometer" class="option-icon" />
                <span>带宽限制</span>
                <el-tag type="info" size="small">
                  {{ wizardData.parameters.syncOptions.bandwidth_limit || 0 }} MB/s
                </el-tag>
              </div>
              <div class="option-item">
                <Icon icon="mdi:connection" class="option-icon" />
                <span>并发连接数</span>
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
              <span>传输策略</span>
            </div>
            <div class="options-grid">
              <div class="option-item">
                <Icon icon="mdi:refresh" class="option-icon" />
                <span>重连次数</span>
                <el-tag type="info" size="small">
                  {{ wizardData.parameters.retryOptions.max_retries }}
                </el-tag>
              </div>
              <div class="option-item">
                <Icon icon="mdi:timer" class="option-icon" />
                <span>重连间隔</span>
                <el-tag type="info" size="small">
                  {{ wizardData.parameters.retryOptions.retry_interval }} 秒
                </el-tag>
              </div>
            </div>
          </div>
          
          <!-- 高级参数 -->
          <div class="options-section">
            <div class="options-header">
              <Icon icon="mdi:settings" class="options-icon" />
              <span>高级参数</span>
            </div>
            <div class="options-grid">
              <div class="option-item">
                <Icon icon="mdi:memory" class="option-icon" />
                <span>缓冲区大小</span>
                <el-tag type="info" size="small">
                  {{ wizardData.parameters.advancedOptions?.buffer_size || 10 }} MB
                </el-tag>
              </div>
              <div class="option-item">
                <Icon icon="mdi:clock" class="option-icon" />
                <span>超时时间</span>
                <el-tag type="info" size="small">
                  {{ wizardData.parameters.advancedOptions?.timeout || 300 }} 秒
                </el-tag>
              </div>
              <div class="option-item">
                <Icon icon="mdi:filter" class="option-icon" />
                <span>排除模式</span>
                <el-tag type="info" size="small">
                  {{ wizardData.parameters.advancedOptions?.exclude_patterns || '无' }}
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
          <h4>预估信息</h4>
        </div>
        
        <div class="section-content">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">预估文件数</span>
              <span class="info-value">{{ estimatedFileCount }} 个文件</span>
            </div>
            <div class="info-item">
              <span class="info-label">预估总大小</span>
              <span class="info-value">{{ estimatedTotalSize }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">预估传输时间</span>
              <span class="info-value">{{ estimatedTransferTime }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">预估带宽使用</span>
              <span class="info-value">{{ estimatedBandwidthUsage }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 确认操作 -->
    <div class="confirmation-actions">
      <el-alert
        title="请确认以上配置信息"
        type="info"
        description="确认无误后点击创建任务按钮开始创建同步任务"
        show-icon
        :closable="false"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Icon } from '@iconify/vue'

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
    return '您选择了与源端相同的对象存储，可能会导致数据覆盖。请确保目标路径与源端路径不同。'
  } else {
    return '您选择了与源端相同的存储，可能会导致数据覆盖。请确保目标路径与源端路径不同。'
  }
})

const estimatedFileCount = computed(() => {
  return props.wizardData.source.selectedPaths.length
})

const estimatedTotalSize = computed(() => {
  const totalSize = props.wizardData.source.selectedPaths.reduce((sum, item) => {
    return sum + (item.size || 0)
  }, 0)
  
  if (totalSize === 0) return '未知'
  
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
  
  if (totalSize === 0) return '未知'
  
  const bandwidth = props.wizardData.parameters.syncOptions.bandwidth_limit || 10 // MB/s
  const timeInSeconds = totalSize / (1024 * 1024) / bandwidth
  
  if (timeInSeconds < 60) {
    return `${Math.ceil(timeInSeconds)} 秒`
  } else if (timeInSeconds < 3600) {
    return `${Math.ceil(timeInSeconds / 60)} 分钟`
  } else {
    return `${Math.ceil(timeInSeconds / 3600)} 小时`
  }
})

const estimatedBandwidthUsage = computed(() => {
  const bandwidth = props.wizardData.parameters.syncOptions.bandwidth_limit || 0
  return bandwidth === 0 ? '无限制' : `${bandwidth} MB/s`
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
    1: '低',
    2: '普通',
    3: '高',
    4: '紧急'
  }
  return texts[priority] || '普通'
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