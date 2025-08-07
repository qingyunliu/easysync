<template>
  <div class="task-parameters">
    <!-- 页面标题 -->
    <div class="parameters-header">
      <h3>配置任务参数</h3>
      <p class="parameters-description">根据源端和目标端类型配置相应的同步参数</p>
    </div>

    <!-- 基础信息 -->
    <el-collapse v-model="activeNames" accordion>
      <el-collapse-item name="basic" title="基础信息">
        <template #title>
          <div class="collapse-title">
            <Icon icon="mdi:information" class="title-icon" />
            <span>基础信息</span>
          </div>
        </template>
        
        <div class="collapse-content">
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
                    <el-option label="低" :value="1">
                      <div class="priority-option">
                        <Icon icon="mdi:flag" class="priority-icon low" />
                        <span>低</span>
                      </div>
                    </el-option>
                    <el-option label="普通" :value="2">
                      <div class="priority-option">
                        <Icon icon="mdi:flag" class="priority-icon normal" />
                        <span>普通</span>
                      </div>
                    </el-option>
                    <el-option label="高" :value="3">
                      <div class="priority-option">
                        <Icon icon="mdi:flag" class="priority-icon high" />
                        <span>高</span>
                      </div>
                    </el-option>
                    <el-option label="紧急" :value="4">
                      <div class="priority-option">
                        <Icon icon="mdi:flag" class="priority-icon urgent" />
                        <span>紧急</span>
                      </div>
                    </el-option>
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
        </div>
      </el-collapse-item>

      <!-- 同步选项 -->
      <el-collapse-item name="sync" title="同步选项">
        <template #title>
          <div class="collapse-title">
            <Icon icon="mdi:sync" class="title-icon" />
            <span>同步选项</span>
          </div>
        </template>
        
        <div class="collapse-content">
          <el-form :model="form.syncOptions" label-width="120px">
            <div class="options-grid">
              <div class="option-item">
                <el-checkbox 
                  v-model="form.syncOptions.delete"
                  @change="updateModelValue"
                >
                  <div class="option-content">
                    <Icon icon="mdi:delete" class="option-icon" />
                    <div class="option-text">
                      <div class="option-title">删除目标多余文件</div>
                      <div class="option-desc">同步时删除目标端多余的文件</div>
                    </div>
                  </div>
                </el-checkbox>
              </div>
              
              <div class="option-item">
                <el-checkbox 
                  v-model="form.syncOptions.compress"
                  @change="updateModelValue"
                >
                  <div class="option-content">
                    <Icon icon="mdi:compress" class="option-icon" />
                    <div class="option-text">
                      <div class="option-title">启用压缩传输</div>
                      <div class="option-desc">传输时压缩数据以减少带宽</div>
                    </div>
                  </div>
                </el-checkbox>
              </div>
              
              <div class="option-item">
                <el-checkbox 
                  v-model="form.syncOptions.checksum"
                  @change="updateModelValue"
                >
                  <div class="option-content">
                    <Icon icon="mdi:check-circle" class="option-icon" />
                    <div class="option-text">
                      <div class="option-title">校验文件完整性</div>
                      <div class="option-desc">传输后校验文件完整性</div>
                    </div>
                  </div>
                </el-checkbox>
              </div>
            </div>
            
            <el-divider />
            
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="带宽限制">
                  <el-input-number
                    v-model="form.syncOptions.bandwidth_limit"
                    :min="0"
                    :max="1000"
                    placeholder="0表示无限制"
                    style="width: 100%"
                    @change="updateModelValue"
                  >
                    <template #suffix>MB/s</template>
                  </el-input-number>
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
        </div>
      </el-collapse-item>

      <!-- 传输策略 -->
      <el-collapse-item name="retry" title="传输策略">
        <template #title>
          <div class="collapse-title">
            <Icon icon="mdi:connection" class="title-icon" />
            <span>传输策略</span>
          </div>
        </template>
        
        <div class="collapse-content">
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
                <el-form-item label="重连间隔">
                  <el-input-number
                    v-model="form.retryOptions.retry_interval"
                    :min="5"
                    :max="300"
                    placeholder="重试间隔时间"
                    style="width: 100%"
                    @change="updateModelValue"
                  >
                    <template #suffix>秒</template>
                  </el-input-number>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
      </el-collapse-item>

      <!-- 高级参数 -->
      <el-collapse-item name="advanced" title="高级参数">
        <template #title>
          <div class="collapse-title">
            <Icon icon="mdi:cog" class="title-icon" />
            <span>高级参数</span>
          </div>
        </template>
        
        <div class="collapse-content">
          <el-form :model="form.advancedOptions" label-width="120px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="缓冲区大小">
                  <el-input-number
                    v-model="form.advancedOptions.buffer_size"
                    :min="1"
                    :max="100"
                    placeholder="传输缓冲区大小"
                    style="width: 100%"
                    @change="updateModelValue"
                  >
                    <template #suffix>MB</template>
                  </el-input-number>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="超时时间">
                  <el-input-number
                    v-model="form.advancedOptions.timeout"
                    :min="30"
                    :max="3600"
                    placeholder="连接超时时间"
                    style="width: 100%"
                    @change="updateModelValue"
                  >
                    <template #suffix>秒</template>
                  </el-input-number>
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
        </div>
      </el-collapse-item>

      <!-- 场景特定参数 -->
      <el-collapse-item v-if="showScenarioOptions" name="scenario" :title="scenarioTitle">
        <template #title>
          <div class="collapse-title">
            <Icon icon="mdi:settings" class="title-icon" />
            <span>{{ scenarioTitle }}</span>
          </div>
        </template>
        
        <div class="collapse-content">
          <component 
            :is="scenarioComponent" 
            v-model="form.scenarioOptions"
            :source-storage="sourceStorage"
            :target-storage="targetStorage"
            @change="updateModelValue"
          />
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Icon } from '@iconify/vue'
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
const activeNames = ref(['basic'])
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
  const result = props.sourceStorage.storageType && props.targetStorage.storageType
  return result
})

const scenarioTitle = computed(() => {
  if (!showScenarioOptions.value) return ''
  
  const sourceType = props.sourceStorage.storageType === 's3' ? 'OBS' : 'NAS'
  const targetType = props.targetStorage.storageType === 's3' ? 'OBS' : 'NAS'
  return `${sourceType}到${targetType}参数`
})

const scenarioComponent = computed(() => {
  if (!showScenarioOptions.value) return null
  
  const sourceType = props.sourceStorage.storageType === 's3' ? 'obs' : 'nas'
  const targetType = props.targetStorage.storageType === 's3' ? 'obs' : 'nas'
  
  if (sourceType === 'nas' && targetType === 'nas') {
    return NasToNasOptions
  } else if (sourceType === 'nas' && targetType === 'obs') {
    return NasToObsOptions
  } else if (sourceType === 'obs' && targetType === 'nas') {
    return ObsToNasOptions
  } else if (sourceType === 'obs' && targetType === 'obs') {
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

// 监听props变化
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
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
  }
}, { immediate: true })
</script>

<style scoped>
.task-parameters {
  padding: 20px;
}

.parameters-header {
  margin-bottom: 30px;
}

.parameters-header h3 {
  margin: 0 0 8px 0;
  color: var(--el-text-color-primary);
  font-size: 20px;
  font-weight: 600;
}

.parameters-description {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  line-height: 1.5;
}

.collapse-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.title-icon {
  font-size: 18px;
  color: var(--el-color-primary);
}

.collapse-content {
  padding: 20px 0;
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.option-item {
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 16px;
  background: var(--el-bg-color-page);
  transition: all 0.2s;
}

.option-item:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.option-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.option-icon {
  font-size: 20px;
  color: var(--el-color-primary);
  margin-top: 2px;
}

.option-text {
  flex: 1;
}

.option-title {
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.option-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
}

.priority-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.priority-icon {
  font-size: 16px;
}

.priority-icon.low {
  color: #67c23a;
}

.priority-icon.normal {
  color: #409eff;
}

.priority-icon.high {
  color: #e6a23c;
}

.priority-icon.urgent {
  color: #f56c6c;
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

:deep(.el-collapse) {
  border: none;
  background: transparent;
}

:deep(.el-collapse-item__header) {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  margin-bottom: 8px;
  padding: 16px 20px;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.2s;
}

:deep(.el-collapse-item__header:hover) {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary);
}

:deep(.el-collapse-item__header.is-active) {
  background: var(--el-color-primary-light-8);
  border-color: var(--el-color-primary);
}

:deep(.el-collapse-item__content) {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  margin-bottom: 8px;
  padding: 20px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--el-border-color) inset;
  transition: box-shadow 0.2s;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset;
}

:deep(.el-button) {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.2s;
}

:deep(.el-button:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

:deep(.el-checkbox__label) {
  font-weight: 500;
}

:deep(.el-divider) {
  margin: 24px 0;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-input-number .el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--el-border-color) inset;
}

:deep(.el-input-number .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset;
}

:deep(.el-input-number .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset;
}
</style> 