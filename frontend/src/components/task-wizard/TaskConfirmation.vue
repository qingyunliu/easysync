<template>
  <div class="task-confirmation">
    <!-- 源端配置确认 -->
    <el-card class="confirmation-card" header="源端配置">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="存储名称">
          {{ wizardData.source.storageName }}
        </el-descriptions-item>
        <el-descriptions-item label="存储类型">
          <el-tag :type="getStorageTypeColor(wizardData.source.storageType)">
            {{ getStorageTypeText(wizardData.source.storageType) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="选中项目数">
          {{ wizardData.source.selectedPaths.length }} 项
        </el-descriptions-item>
      </el-descriptions>
      
      <!-- 选中的文件/目录列表 -->
      <div v-if="wizardData.source.selectedPaths.length > 0" class="selected-items">
        <h4>选中的文件/目录：</h4>
        <el-tag
          v-for="item in wizardData.source.selectedPaths"
          :key="item.path"
          class="selected-item"
          closable
        >
          <el-icon class="item-icon">
            <component :is="item.type === 'directory' ? 'Folder' : 'Document'" />
          </el-icon>
          {{ item.name }}
        </el-tag>
      </div>
    </el-card>

    <!-- 目标端配置确认 -->
    <el-card class="confirmation-card" header="目标端配置">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="存储名称">
          {{ wizardData.target.storageName }}
        </el-descriptions-item>
        <el-descriptions-item label="存储类型">
          <el-tag :type="getStorageTypeColor(wizardData.target.storageType)">
            {{ getStorageTypeText(wizardData.target.storageType) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="目标路径">
          {{ wizardData.target.targetPath }}
        </el-descriptions-item>
      </el-descriptions>
      
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
    </el-card>

    <!-- 任务参数确认 -->
    <el-card class="confirmation-card" header="任务参数">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="任务名称">
          {{ wizardData.parameters.taskName }}
        </el-descriptions-item>
        <el-descriptions-item label="优先级">
          <el-tag :type="getPriorityType(wizardData.parameters.priority)">
            {{ getPriorityText(wizardData.parameters.priority) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="任务描述">
          {{ wizardData.parameters.description || '无描述' }}
        </el-descriptions-item>
      </el-descriptions>
      
      <!-- 同步选项 -->
      <div class="sync-options">
        <h4>同步选项：</h4>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-tag :type="wizardData.parameters.syncOptions.delete ? 'success' : 'info'">
              删除目标多余文件: {{ wizardData.parameters.syncOptions.delete ? '是' : '否' }}
            </el-tag>
          </el-col>
          <el-col :span="8">
            <el-tag :type="wizardData.parameters.syncOptions.compress ? 'success' : 'info'">
              启用压缩传输: {{ wizardData.parameters.syncOptions.compress ? '是' : '否' }}
            </el-tag>
          </el-col>
          <el-col :span="8">
            <el-tag :type="wizardData.parameters.syncOptions.checksum ? 'success' : 'info'">
              校验文件完整性: {{ wizardData.parameters.syncOptions.checksum ? '是' : '否' }}
            </el-tag>
          </el-col>
        </el-row>
        
        <el-row :gutter="20" style="margin-top: 10px">
          <el-col :span="12">
            <el-tag type="info">
              带宽限制: {{ wizardData.parameters.syncOptions.bandwidth_limit || 0 }} MB/s
            </el-tag>
          </el-col>
          <el-col :span="12">
            <el-tag type="info">
              并发连接数: {{ wizardData.parameters.syncOptions.max_connections }}
            </el-tag>
          </el-col>
        </el-row>
      </div>
      
      <!-- 传输策略 -->
      <div class="retry-options">
        <h4>传输策略：</h4>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-tag type="info">
              重连次数: {{ wizardData.parameters.retryOptions.max_retries }}
            </el-tag>
          </el-col>
          <el-col :span="12">
            <el-tag type="info">
              重连间隔: {{ wizardData.parameters.retryOptions.retry_interval }} 秒
            </el-tag>
          </el-col>
        </el-row>
      </div>
      
      <!-- 高级参数 -->
      <div class="advanced-options">
        <h4>高级参数：</h4>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-tag type="info">
              缓冲区大小: {{ wizardData.parameters.advancedOptions?.buffer_size || 10 }} MB
            </el-tag>
          </el-col>
          <el-col :span="8">
            <el-tag type="info">
              超时时间: {{ wizardData.parameters.advancedOptions?.timeout || 300 }} 秒
            </el-tag>
          </el-col>
          <el-col :span="8">
            <el-tag type="info">
              排除模式: {{ wizardData.parameters.advancedOptions?.exclude_patterns || '无' }}
            </el-tag>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 预估信息 -->
    <el-card class="confirmation-card" header="预估信息">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="预估文件数">
          {{ estimatedFileCount }} 个文件
        </el-descriptions-item>
        <el-descriptions-item label="预估总大小">
          {{ estimatedTotalSize }}
        </el-descriptions-item>
        <el-descriptions-item label="预估传输时间">
          {{ estimatedTransferTime }}
        </el-descriptions-item>
        <el-descriptions-item label="预估带宽使用">
          {{ estimatedBandwidthUsage }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

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
import { Folder, Document } from '@element-plus/icons-vue'

const props = defineProps({
  wizardData: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['confirm'])

// 计算属性
const showOverrideWarning = computed(() => {
  return props.wizardData.source.storageId === props.wizardData.target.storageId
})

const overrideWarningText = computed(() => {
  if (!showOverrideWarning.value) return ''
  
  const storageType = getStorageTypeText(props.wizardData.source.storageType)
  return `您选择了相同的${storageType}存储作为源端和目标端，这可能会导致数据覆盖。请确保目标路径与源端路径不同，以避免数据丢失。`
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
  const totalSizeMB = totalSize / (1024 * 1024)
  const timeInSeconds = totalSizeMB / bandwidth
  
  if (timeInSeconds < 60) {
    return `${Math.ceil(timeInSeconds)} 秒`
  } else if (timeInSeconds < 3600) {
    return `${Math.ceil(timeInSeconds / 60)} 分钟`
  } else {
    return `${Math.ceil(timeInSeconds / 3600)} 小时`
  }
})

const estimatedBandwidthUsage = computed(() => {
  const bandwidth = props.wizardData.parameters.syncOptions.bandwidth_limit
  if (bandwidth === 0) {
    return '无限制'
  }
  return `${bandwidth} MB/s`
})

// 辅助函数
const getStorageTypeColor = (type) => {
  const colors = {
    'nas': 'success',
    's3': 'primary',
    'nfs': 'warning',
    'smb': 'danger'
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

.confirmation-card {
  margin-bottom: 20px;
}

.confirmation-card:last-child {
  margin-bottom: 0;
}

.selected-items {
  margin-top: 16px;
}

.selected-items h4 {
  margin: 0 0 12px 0;
  color: var(--el-text-color-primary);
  font-size: 14px;
  font-weight: 600;
}

.selected-item {
  margin-right: 8px;
  margin-bottom: 8px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.item-icon {
  font-size: 14px;
}

.override-warning {
  margin-top: 16px;
}

.sync-options,
.retry-options,
.advanced-options {
  margin-top: 16px;
}

.sync-options h4,
.retry-options h4,
.advanced-options h4 {
  margin: 0 0 12px 0;
  color: var(--el-text-color-primary);
  font-size: 14px;
  font-weight: 600;
}

.confirmation-actions {
  margin-top: 20px;
}

:deep(.el-card__header) {
  background: var(--el-color-primary-light-9);
  border-bottom: 1px solid var(--el-border-color-light);
  font-weight: 600;
}

:deep(.el-descriptions__label) {
  font-weight: 500;
}

:deep(.el-tag) {
  margin-right: 8px;
  margin-bottom: 8px;
}
</style> 