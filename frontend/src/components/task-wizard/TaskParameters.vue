<template>
  <div class="task-parameters">
    <!-- 基础信息 -->
    <el-card class="parameter-card" header="基础信息">
      <el-form :model="form" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="任务名称" required>
              <el-input 
                v-model="form.taskName" 
                placeholder="请输入任务名称"
                @input="updateModelValue"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="优先级">
              <el-select v-model="form.priority" style="width: 100%" @change="updateModelValue">
                <el-option label="低" :value="1" />
                <el-option label="普通" :value="2" />
                <el-option label="高" :value="3" />
                <el-option label="紧急" :value="4" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="任务描述">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入任务描述"
            @input="updateModelValue"
          />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 同步选项 -->
    <el-card class="parameter-card" header="同步选项">
      <el-form :model="form.syncOptions" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item>
              <el-checkbox 
                v-model="form.syncOptions.delete"
                @change="updateModelValue"
              >
                删除目标多余文件
              </el-checkbox>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item>
              <el-checkbox 
                v-model="form.syncOptions.compress"
                @change="updateModelValue"
              >
                启用压缩传输
              </el-checkbox>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item>
              <el-checkbox 
                v-model="form.syncOptions.checksum"
                @change="updateModelValue"
              >
                校验文件完整性
              </el-checkbox>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="带宽限制(MB/s)">
              <el-input-number
                v-model="form.syncOptions.bandwidth_limit"
                :min="0"
                :max="1000"
                placeholder="0表示无限制"
                style="width: 100%"
                @change="updateModelValue"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="并发连接数">
              <el-input-number
                v-model="form.syncOptions.max_connections"
                :min="1"
                :max="10"
                placeholder="默认为1"
                style="width: 100%"
                @change="updateModelValue"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 传输策略 -->
    <el-card class="parameter-card" header="传输策略">
      <el-form :model="form.retryOptions" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="重连次数">
              <el-input-number
                v-model="form.retryOptions.max_retries"
                :min="0"
                :max="10"
                placeholder="最大重试次数"
                style="width: 100%"
                @change="updateModelValue"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="重连间隔(秒)">
              <el-input-number
                v-model="form.retryOptions.retry_interval"
                :min="5"
                :max="300"
                placeholder="重试间隔时间"
                style="width: 100%"
                @change="updateModelValue"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 高级参数 -->
    <el-card class="parameter-card" header="高级参数">
      <el-form :model="form.advancedOptions" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="缓冲区大小(MB)">
              <el-input-number
                v-model="form.advancedOptions.buffer_size"
                :min="1"
                :max="100"
                placeholder="传输缓冲区大小"
                style="width: 100%"
                @change="updateModelValue"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="超时时间(秒)">
              <el-input-number
                v-model="form.advancedOptions.timeout"
                :min="30"
                :max="3600"
                placeholder="连接超时时间"
                style="width: 100%"
                @change="updateModelValue"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="排除模式">
              <el-input
                v-model="form.advancedOptions.exclude_patterns"
                placeholder="*.tmp,*.log,.git/"
                @input="updateModelValue"
              />
              <div class="form-tip">多个模式用逗号分隔</div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="包含模式">
              <el-input
                v-model="form.advancedOptions.include_patterns"
                placeholder="*.jpg,*.png,*.pdf"
                @input="updateModelValue"
              />
              <div class="form-tip">多个模式用逗号分隔</div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 场景特定参数 -->
    <el-card v-if="showScenarioOptions" class="parameter-card" :header="scenarioTitle">
      <component 
        :is="scenarioComponent" 
        v-model="form.scenarioOptions"
        :source-storage="sourceStorage"
        :target-storage="targetStorage"
        @change="updateModelValue"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import NasToNasOptions from './scenarios/NasToNasOptions.vue'
import NasToObsOptions from './scenarios/NasToObsOptions.vue'
import ObsToNasOptions from './scenarios/ObsToNasOptions.vue'
import ObsToObsOptions from './scenarios/ObsToObsOptions.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      taskName: '',
      description: '',
      priority: 2,
      syncOptions: {
        delete: false,
        compress: false,
        checksum: true,
        bandwidth_limit: 0,
        max_connections: 1
      },
      retryOptions: {
        max_retries: 3,
        retry_interval: 30
      },
      advancedOptions: {
        buffer_size: 10,
        timeout: 300,
        exclude_patterns: '',
        include_patterns: ''
      },
      scenarioOptions: {}
    })
  },
  sourceStorage: {
    type: Object,
    default: () => ({})
  },
  targetStorage: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

// 响应式数据
const form = ref({
  taskName: props.modelValue.taskName || '',
  description: props.modelValue.description || '',
  priority: props.modelValue.priority || 2,
  syncOptions: {
    delete: props.modelValue.syncOptions?.delete || false,
    compress: props.modelValue.syncOptions?.compress || false,
    checksum: props.modelValue.syncOptions?.checksum || true,
    bandwidth_limit: props.modelValue.syncOptions?.bandwidth_limit || 0,
    max_connections: props.modelValue.syncOptions?.max_connections || 1
  },
  retryOptions: {
    max_retries: props.modelValue.retryOptions?.max_retries || 3,
    retry_interval: props.modelValue.retryOptions?.retry_interval || 30
  },
  advancedOptions: {
    buffer_size: props.modelValue.advancedOptions?.buffer_size || 10,
    timeout: props.modelValue.advancedOptions?.timeout || 300,
    exclude_patterns: props.modelValue.advancedOptions?.exclude_patterns || '',
    include_patterns: props.modelValue.advancedOptions?.include_patterns || ''
  },
  scenarioOptions: props.modelValue.scenarioOptions || {}
})

// 计算属性
const showScenarioOptions = computed(() => {
  return props.sourceStorage.storageType && props.targetStorage.storageType
})

const scenarioTitle = computed(() => {
  const sourceType = getStorageTypeText(props.sourceStorage.storageType)
  const targetType = getStorageTypeText(props.targetStorage.storageType)
  return `${sourceType} → ${targetType} 特定参数`
})

const scenarioComponent = computed(() => {
  const sourceType = props.sourceStorage.storageType
  const targetType = props.targetStorage.storageType
  
  if (sourceType === 'nas' && targetType === 'nas') {
    return NasToNasOptions
  } else if (sourceType === 'nas' && targetType === 's3') {
    return NasToObsOptions
  } else if (sourceType === 's3' && targetType === 'nas') {
    return ObsToNasOptions
  } else if (sourceType === 's3' && targetType === 's3') {
    return ObsToObsOptions
  }
  
  return null
})

// 方法
const updateModelValue = () => {
  const value = {
    taskName: form.value.taskName,
    description: form.value.description,
    priority: form.value.priority,
    syncOptions: { ...form.value.syncOptions },
    retryOptions: { ...form.value.retryOptions },
    advancedOptions: { ...form.value.advancedOptions },
    scenarioOptions: { ...form.value.scenarioOptions }
  }
  emit('update:modelValue', value)
  emit('change', value)
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

// 监听props变化
watch(() => props.modelValue, (newValue) => {
  form.value = {
    taskName: newValue.taskName || '',
    description: newValue.description || '',
    priority: newValue.priority || 2,
    syncOptions: {
      delete: newValue.syncOptions?.delete || false,
      compress: newValue.syncOptions?.compress || false,
      checksum: newValue.syncOptions?.checksum || true,
      bandwidth_limit: newValue.syncOptions?.bandwidth_limit || 0,
      max_connections: newValue.syncOptions?.max_connections || 1
    },
    retryOptions: {
      max_retries: newValue.retryOptions?.max_retries || 3,
      retry_interval: newValue.retryOptions?.retry_interval || 30
    },
    advancedOptions: {
      buffer_size: newValue.advancedOptions?.buffer_size || 10,
      timeout: newValue.advancedOptions?.timeout || 300,
      exclude_patterns: newValue.advancedOptions?.exclude_patterns || '',
      include_patterns: newValue.advancedOptions?.include_patterns || ''
    },
    scenarioOptions: newValue.scenarioOptions || {}
  }
}, { deep: true })
</script>

<style scoped>
.task-parameters {
  padding: 20px;
}

.parameter-card {
  margin-bottom: 20px;
}

.parameter-card:last-child {
  margin-bottom: 0;
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

:deep(.el-card__header) {
  background: var(--el-color-primary-light-9);
  border-bottom: 1px solid var(--el-border-color-light);
  font-weight: 600;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-checkbox__label) {
  font-weight: 500;
}
</style> 